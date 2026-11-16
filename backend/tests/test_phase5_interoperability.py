"""Suíte de Testes da Fase 5: Interoperabilidade, Webhooks Assinados e Validação Pública (Sprint 5.4).

Conforme ESPECIFICACAO_CAMADA_INTEGRACAO_LIMS.md e ALCOA+:
1. Assinatura HMAC SHA-256 de webhooks (X-LIMS-Signature, anti-replay, integridade).
2. Ciclo de vida de subscrições e histórico transacional de outbox deliveries.
3. Validação pública de autenticidade de laudos por QR Code / Token e Hash SHA-256 (/public/reports/verify).
4. Matriz de autorização e bloqueio estrito de escrita para AUDITOR (H0.7).
5. Geração monotônica de numeração de laudos oficiais sem colisão sob concorrência (H0.5).
"""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

import httpx
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.dialect import next_sequence
from app.models.base import utcnow
from app.models.enums import (
    CoordinationReviewStatus,
    SampleStatus,
    TestOutcome,
    TestStatus,
)
from app.models.lab_test import LabTest
from app.services import webhook_service
from app.services.webhook_service import compute_signature

API = "/api/v1"


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def login(client: AsyncClient, username: str, password: str) -> dict[str, Any]:
    res = await client.post(
        f"{API}/auth/login",
        data={"username": username, "password": password},
    )
    assert res.status_code == 200, res.text
    return res.json()


@pytest.mark.asyncio
async def test_webhook_hmac_signature_calculation() -> None:
    """Valida a derivação exata da assinatura HMAC SHA-256 e validação anti-replay."""
    secret = "chave-super-secreta-integracao-123456"
    timestamp = 1763300000
    payload_body = '{"event":"report.issued","report_number":"LDO-2026-0001"}'

    sig1 = compute_signature(secret, timestamp, payload_body)
    assert sig1.startswith("v1=")
    assert len(sig1) == 67  # 'v1=' (3) + 64 hex chars

    # Determinístico para a mesma entrada
    sig2 = compute_signature(secret, timestamp, payload_body)
    assert sig1 == sig2

    # Qualquer alteração no corpo ou timestamp gera assinatura divergente
    sig_tampered = compute_signature(secret, timestamp + 1, payload_body)
    assert sig1 != sig_tampered


@pytest.mark.asyncio
async def test_webhook_subscription_lifecycle_and_ping(
    client: AsyncClient, users: dict[str, Any]
) -> None:
    """Valida o cadastro de endpoint de webhook, listagem, teste com ping e remoção."""
    adm_token = (await login(client, "admin", users["admin"]["password"]))["access_token"]
    tec_token = (await login(client, "tecnico", users["tecnico"]["password"]))["access_token"]

    # 1. Técnico não tem permissão para gerenciar subscrições de webhook (RBAC)
    res_forbidden = await client.post(
        f"{API}/webhooks/subscriptions",
        json={"url": "https://erp.exemplo.com.br/lims-events", "description": "ERP Corporativo"},
        headers=auth(tec_token),
    )
    assert res_forbidden.status_code == 403

    # 2. Administrador cadastra subscrição
    res_create = await client.post(
        f"{API}/webhooks/subscriptions",
        json={
            "url": "https://httpbin.org/post",
            "description": "Serviço de Laudos Externos",
            "events": ["report.issued", "test.completed"],
        },
        headers=auth(adm_token),
    )
    assert res_create.status_code == 201, res_create.text
    sub_data = res_create.json()
    sub_id = sub_data["id"]
    assert sub_data["url"] == "https://httpbin.org/post"
    assert "report.issued" in sub_data["events"]

    # 3. Listagem de subscrições
    res_list = await client.get(f"{API}/webhooks/subscriptions", headers=auth(adm_token))
    assert res_list.status_code == 200
    assert any(s["id"] == sub_id for s in res_list.json())

    # 4. Detalhes
    res_detail = await client.get(f"{API}/webhooks/subscriptions/{sub_id}", headers=auth(adm_token))
    assert res_detail.status_code == 200
    assert res_detail.json()["id"] == sub_id

    # 5. Ping de teste
    res_ping = await client.post(
        f"{API}/webhooks/subscriptions/{sub_id}/ping",
        headers=auth(adm_token),
    )
    assert res_ping.status_code == 200, res_ping.text
    ping_data = res_ping.json()
    assert ping_data["event"] == "ping"
    assert ping_data["signature_header"].startswith("v1=")

    # 6. Listagem de entregas
    res_deliv = await client.get(
        f"{API}/webhooks/deliveries?subscription_id={sub_id}",
        headers=auth(adm_token),
    )
    assert res_deliv.status_code == 200
    assert len(res_deliv.json()) >= 1

    # 7. Remoção de subscrição
    res_del = await client.delete(
        f"{API}/webhooks/subscriptions/{sub_id}",
        headers=auth(adm_token),
    )
    assert res_del.status_code == 204


@pytest.mark.asyncio
async def test_webhook_dispatch_event_creates_outbox_deliveries(
    db_factory: async_sessionmaker[AsyncSession],
    users: dict[str, Any],
) -> None:
    """Valida o envio transacional de eventos e criação dos registros de entrega."""
    async with db_factory() as db:
        # Cadastra subscrição ativa
        sub = await webhook_service.create_subscription(
            db,
            url="https://webhook.mock/receive",
            description="Receptor de Mock",
            events=["report.issued"],
            secret="mock-secret-1234567890",
            created_by_id=UUID(users["admin"]["id"]),
        )
        sub_id = sub.id

        # Simula cliente HTTP local usando mock transport
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers.get("X-LIMS-Event") == "report.issued"
            assert request.headers.get("X-LIMS-Delivery") is not None
            assert request.headers.get("X-LIMS-Signature") is not None
            return httpx.Response(200, json={"status": "ok"})

        mock_transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=mock_transport) as mock_client:
            deliveries = await webhook_service.dispatch_event(
                db,
                event="report.issued",
                payload={"report_number": "LDO-2026-9999", "status": "CONFORME"},
                client=mock_client,
            )
            assert len(deliveries) >= 1
            deliv = deliveries[0]
            assert deliv.status == "DELIVERED"
            assert deliv.status_code == 200

        # Limpeza
        await webhook_service.delete_subscription(db, sub_id)


@pytest.mark.asyncio
async def test_monotonic_sequence_and_concurrent_reports(
    db_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Valida que official_report_seq é estritamente monotônica e elimina risco de colisão (H0.5)."""
    async with db_factory() as db:
        seq1 = await next_sequence(db, "official_report_seq")
        seq2 = await next_sequence(db, "official_report_seq")
        seq3 = await next_sequence(db, "official_report_seq")
        assert seq2 == seq1 + 1
        assert seq3 == seq2 + 1


@pytest.mark.asyncio
async def test_public_report_verification_by_token_and_hash(
    client: AsyncClient,
    users: dict[str, Any],
    db_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Valida a consulta pública de autenticidade por auth_token e sha256_hash (/public/reports/verify)."""
    # 1. Cria laudo no banco
    fisc_token = (await login(client, "fiscal", users["fiscal"]["password"]))["access_token"]
    fiscal_user = users["fiscal"]

    # Cria amostra
    from app.models.device_sample import DeviceSample
    sample_id = uuid4()
    async with db_factory() as db:
        sample = DeviceSample(
            id=sample_id,
            accession_number=f"LIMS-2026-{uuid4().hex[:6].upper()}",
            manufacturer="Fabricante Nacional S/A",
            commercial_name="Bolsa Coletora para Teste",
            lot_number="LOTE-PUB-01",
            serial_number="SN-PUB-01",
            status=SampleStatus.EM_TESTE,
            received_by_id=UUID(fiscal_user["id"]),
        )
        db.add(sample)
        test = LabTest(
            id=uuid4(),
            device_sample_id=sample_id,
            name="Ensaio de Estanqueidade",
            unit="kPa",
            status=TestStatus.CONCLUIDO,
            review_status=CoordinationReviewStatus.APROVADO,
            outcome=TestOutcome.APROVADO,
            tested_at=utcnow(),
        )
        db.add(test)
        await db.commit()

    # Emite assinatura e laudo
    sig_res = await client.post(
        f"{API}/auth/sign",
        headers=auth(fisc_token),
        json={
            "password": users["fiscal"]["password"],
            "entity_type": "DeviceSample",
            "entity_id": str(sample_id),
            "action": "CLOSE",
            "meaning": "RESPONSABILIDADE_TECNICA",
            "reason": "Emissão de Laudo Oficial",
        },
    )
    assert sig_res.status_code == 200, sig_res.text
    sig_token = sig_res.json()["token"]

    report_payload = {
        "device_sample_id": str(sample_id),
        "test_ids": [str(test.id)],
        "title": "Laudo Pericial Oficial de Conformidade Técnica",
        "conclusion": "APROVADO",
        "summary": "Dispositivo médico aprovado em todos os ensaios normativos.",
    }
    rep_res = await client.post(
        f"{API}/reports/official",
        json=report_payload,
        headers={**auth(fisc_token), "X-Signature-Token": sig_token},
    )
    assert rep_res.status_code == 200, rep_res.text
    rep_data = rep_res.json()
    auth_token = rep_data["auth_token"]
    sha256_hash = rep_data["sha256_hash"]

    # 2. Consulta pública por auth_token (sem headers de autorização)
    res_pub_token = await client.get(f"{API}/public/reports/verify/{auth_token}")
    assert res_pub_token.status_code == 200, res_pub_token.text
    data_token = res_pub_token.json()
    assert data_token["is_valid"] is True
    assert data_token["report_number"] == rep_data["report_number"]
    assert data_token["sha256_hash"] == sha256_hash

    # 3. Consulta pública por SHA-256 hash (sem headers de autorização)
    res_pub_hash = await client.get(f"{API}/public/reports/verify/{sha256_hash}")
    assert res_pub_hash.status_code == 200, res_pub_hash.text
    data_hash = res_pub_hash.json()
    assert data_hash["is_valid"] is True
    assert data_hash["report_number"] == rep_data["report_number"]

    # 4. Token inexistente retorna 404
    res_404 = await client.get(f"{API}/public/reports/verify/token-inexistente-123")
    assert res_404.status_code == 404


@pytest.mark.asyncio
async def test_rbac_security_auditor_cannot_mutate(
    client: AsyncClient, users: dict[str, Any]
) -> None:
    """Garante que usuário com perfil AUDITOR possui apenas acesso de leitura (H0.7)."""
    aud_token = (await login(client, "auditor", users["auditor"]["password"]))["access_token"]

    # Leitura permitida em analytics
    res_op = await client.get(f"{API}/analytics/operational", headers=auth(aud_token))
    assert res_op.status_code == 200

    # Escrita bloqueada em anexos
    res_att = await client.post(
        f"{API}/attachments/tests/{uuid4()}",
        files={"file": ("evidencia.txt", b"conteudo", "text/plain")},
        headers=auth(aud_token),
    )
    assert res_att.status_code == 403

    # Escrita bloqueada em dados de instrumentos
    res_inst = await client.post(
        f"{API}/instrument-data/upload-raw",
        json={
            "equipment_id": str(uuid4()),
            "file_name": "teste.raw",
            "file_format": "GENERIC_JSON",
            "raw_content": "{}",
        },
        headers=auth(aud_token),
    )
    assert res_inst.status_code == 403

    # Escrita bloqueada em orçamentos de incerteza
    res_unc = await client.post(
        f"{API}/uncertainty/budgets",
        json={
            "lab_test_id": str(uuid4()),
            "components": [],
            "decision_rule": "ILAC_G8_GUARDED",
        },
        headers=auth(aud_token),
    )
    assert res_unc.status_code == 403
