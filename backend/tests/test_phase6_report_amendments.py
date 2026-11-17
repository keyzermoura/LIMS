"""Testes de Versionamento, Emendas e Geração Real de PDF para Laudos Oficiais (Horizonte 1 / Sprint 6.1).

Conforme requisitos ISO/IEC 17025:2017 §7.8.8, 21 CFR Part 11 e ALCOA+.
"""

from __future__ import annotations

import hashlib
from typing import Any
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.base import utcnow
from app.models.device_sample import DeviceSample
from app.models.enums import (
    CoordinationReviewStatus,
    SampleStatus,
    TestOutcome,
    TestStatus,
)
from app.models.lab_test import LabTest

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


async def get_signature_token(
    client: AsyncClient,
    token: str,
    password: str,
    entity_id: str,
    entity_type: str = "DeviceSample",
) -> str:
    res = await client.post(
        f"{API}/auth/sign",
        headers=auth(token),
        json={
            "entity_type": entity_type,
            "entity_id": entity_id,
            "action": "CLOSE",
            "meaning": "RESPONSABILIDADE_TECNICA",
            "reason": "Homologação e assinatura pericial de laudo oficial",
            "password": password,
        },
    )
    assert res.status_code == 200, res.text
    return res.json()["token"]


async def create_sample_and_test(
    db_factory: async_sessionmaker[AsyncSession],
    user_id: str,
) -> tuple[UUID, UUID]:
    sample_id = uuid4()
    test_id = uuid4()
    async with db_factory() as db:
        sample = DeviceSample(
            id=sample_id,
            accession_number=f"BR-2026-{uuid4().hex[:4].upper()}",
            commercial_name="Cateter Guia Angiográfico SuperFlow",
            manufacturer="Biotec Med Indústria Ltda",
            lot_number="LOT-2026-X89",
            serial_number="SN-789012",
            status=SampleStatus.EM_TESTE,
            received_by_id=UUID(user_id),
        )
        db.add(sample)
        test = LabTest(
            id=test_id,
            device_sample_id=sample_id,
            name="Pressão de Ruptura Estática",
            unit="kPa",
            lower_limit=300.0,
            upper_limit=None,
            result_value=425.8,
            outcome=TestOutcome.APROVADO,
            status=TestStatus.CONCLUIDO,
            review_status=CoordinationReviewStatus.APROVADO,
            tested_at=utcnow(),
        )
        db.add(test)
        await db.commit()
    return sample_id, test_id


@pytest.mark.asyncio
async def test_generate_report_creates_valid_pdf_and_sha256(
    client: AsyncClient,
    users: dict[str, Any],
    db_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Emissão de laudo V1 deve gerar PDF binário determinístico, hash SHA-256 e version=1."""
    fisc = users["fiscal"]
    fisc_token = (await login(client, "fiscal", fisc["password"]))["access_token"]
    sample_id, test_id = await create_sample_and_test(db_factory, fisc["id"])

    sig_token = await get_signature_token(
        client, fisc_token, fisc["password"], str(sample_id), "DeviceSample"
    )

    res = await client.post(
        f"{API}/reports/official",
        headers={**auth(fisc_token), "X-Signature-Token": sig_token},
        json={
            "device_sample_id": str(sample_id),
            "test_ids": [str(test_id)],
            "title": "Laudo Pericial de Fiscalização Sanitária",
            "conclusion": "APROVADO",
            "summary": "Amostra atendeu integralmente aos ensaios mecânicos de segurança.",
        },
    )
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["version"] == 1
    assert data["is_latest"] is True
    assert data["root_report_id"] is None
    assert data["supersedes_id"] is None
    assert data["amendment_reason"] is None
    assert len(data["sha256_hash"]) == 64

    # Download do PDF emitido
    pdf_res = await client.get(
        f"{API}/reports/official/{data['id']}/pdf",
        headers=auth(fisc_token),
    )
    assert pdf_res.status_code == 200
    assert pdf_res.headers["Content-Type"] == "application/pdf"
    pdf_bytes = pdf_res.content
    assert pdf_bytes.startswith(b"%PDF-")
    assert hashlib.sha256(pdf_bytes).hexdigest() == data["sha256_hash"]


@pytest.mark.asyncio
async def test_amend_report_lifecycle_and_immutability(
    client: AsyncClient,
    users: dict[str, Any],
    db_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Emenda de laudo (ISO 17025 §7.8.8) cria V2 imutável, inativa V1 e mantém trilha histórica."""
    fisc = users["fiscal"]
    fisc_token = (await login(client, "fiscal", fisc["password"]))["access_token"]
    sample_id, test_id = await create_sample_and_test(db_factory, fisc["id"])

    # 1. Emite Laudo Original V1
    sig_v1 = await get_signature_token(
        client, fisc_token, fisc["password"], str(sample_id), "DeviceSample"
    )
    res_v1 = await client.post(
        f"{API}/reports/official",
        headers={**auth(fisc_token), "X-Signature-Token": sig_v1},
        json={
            "device_sample_id": str(sample_id),
            "test_ids": [str(test_id)],
            "title": "Laudo Original",
            "conclusion": "APROVADO",
        },
    )
    assert res_v1.status_code == 200
    v1_data = res_v1.json()
    v1_id = v1_data["id"]
    v1_num = v1_data["report_number"]

    # 2. Emite Emenda Retificadora V2
    sig_v2 = await get_signature_token(
        client, fisc_token, fisc["password"], str(v1_id), "OfficialReport"
    )
    res_v2 = await client.post(
        f"{API}/reports/official/{v1_id}/amend",
        headers={**auth(fisc_token), "X-Signature-Token": sig_v2},
        json={
            "amendment_reason": "Retificação formal do resumo pericial para inclusão de nota técnica fiscal.",
            "title": "Laudo Retificado e Emendado",
            "summary": "Resumo atualizado com observações complementares.",
        },
    )
    assert res_v2.status_code == 200, res_v2.text
    v2_data = res_v2.json()

    assert v2_data["version"] == 2
    assert v2_data["is_latest"] is True
    assert v2_data["root_report_id"] == v1_id
    assert v2_data["supersedes_id"] == v1_id
    assert "Retificação formal" in v2_data["amendment_reason"]
    assert v2_data["report_number"] == f"{v1_num}-V2"

    # 3. Consulta V1 novamente: is_latest agora deve ser False
    res_v1_refreshed = await client.get(
        f"{API}/reports/official/{v1_id}",
        headers=auth(fisc_token),
    )
    assert res_v1_refreshed.status_code == 200
    assert res_v1_refreshed.json()["is_latest"] is False


@pytest.mark.asyncio
async def test_amend_report_validation_rules(
    client: AsyncClient,
    users: dict[str, Any],
    db_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Valida regras de domínio: justificativa curta demais e tentativa de emendar laudo já superado."""
    fisc = users["fiscal"]
    fisc_token = (await login(client, "fiscal", fisc["password"]))["access_token"]
    sample_id, test_id = await create_sample_and_test(db_factory, fisc["id"])

    sig_v1 = await get_signature_token(
        client, fisc_token, fisc["password"], str(sample_id), "DeviceSample"
    )
    res_v1 = await client.post(
        f"{API}/reports/official",
        headers={**auth(fisc_token), "X-Signature-Token": sig_v1},
        json={"device_sample_id": str(sample_id), "test_ids": [str(test_id)]},
    )
    v1_id = res_v1.json()["id"]

    # Tentativa com justificativa < 10 caracteres falha no schema Pydantic (min_length=10)
    sig_v2 = await get_signature_token(
        client, fisc_token, fisc["password"], str(v1_id), "OfficialReport"
    )
    res_short = await client.post(
        f"{API}/reports/official/{v1_id}/amend",
        headers={**auth(fisc_token), "X-Signature-Token": sig_v2},
        json={"amendment_reason": "Curto"},
    )
    assert res_short.status_code == 422

    # Cria V2 legítimo
    res_v2 = await client.post(
        f"{API}/reports/official/{v1_id}/amend",
        headers={**auth(fisc_token), "X-Signature-Token": sig_v2},
        json={"amendment_reason": "Justificativa válida com mais de 10 caracteres."},
    )
    assert res_v2.status_code == 200

    # Tentativa de emendar novamente o V1 (que agora está superado) é rejeitada
    sig_fail = await get_signature_token(
        client, fisc_token, fisc["password"], str(v1_id), "OfficialReport"
    )
    res_superseded = await client.post(
        f"{API}/reports/official/{v1_id}/amend",
        headers={**auth(fisc_token), "X-Signature-Token": sig_fail},
        json={"amendment_reason": "Tentativa de emendar versão antiga já superada."},
    )
    assert res_superseded.status_code == 422
    assert "já foi superado" in res_superseded.json()["detail"]


@pytest.mark.asyncio
async def test_public_verification_displays_version_and_superseded_alert(
    client: AsyncClient,
    users: dict[str, Any],
    db_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Verificação pública sem login indica com clareza versão N de M e histórico de emendas."""
    fisc = users["fiscal"]
    fisc_token = (await login(client, "fiscal", fisc["password"]))["access_token"]
    sample_id, test_id = await create_sample_and_test(db_factory, fisc["id"])

    sig_v1 = await get_signature_token(
        client, fisc_token, fisc["password"], str(sample_id), "DeviceSample"
    )
    res_v1 = await client.post(
        f"{API}/reports/official",
        headers={**auth(fisc_token), "X-Signature-Token": sig_v1},
        json={"device_sample_id": str(sample_id), "test_ids": [str(test_id)]},
    )
    v1_data = res_v1.json()

    # Emite V2
    sig_v2 = await get_signature_token(
        client, fisc_token, fisc["password"], str(v1_data["id"]), "OfficialReport"
    )
    res_v2 = await client.post(
        f"{API}/reports/official/{v1_data['id']}/amend",
        headers={**auth(fisc_token), "X-Signature-Token": sig_v2},
        json={"amendment_reason": "Ajuste metrológico aprovado pela coordenação técnica."},
    )
    v2_data = res_v2.json()

    # Consulta pública em V1 (antigo): deve avisar que foi superado
    pub_v1 = await client.get(f"{API}/public/reports/verify/{v1_data['auth_token']}")
    assert pub_v1.status_code == 200
    info_v1 = pub_v1.json()
    assert info_v1["is_valid"] is True
    assert info_v1["version"] == 1
    assert info_v1["is_latest"] is False
    assert info_v1["latest_report_number"] == v2_data["report_number"]
    assert len(info_v1["history"]) == 2

    # Consulta pública em V2 (vigente): is_latest True
    pub_v2 = await client.get(f"{API}/public/reports/verify/{v2_data['auth_token']}")
    assert pub_v2.status_code == 200
    info_v2 = pub_v2.json()
    assert info_v2["is_valid"] is True
    assert info_v2["version"] == 2
    assert info_v2["is_latest"] is True
    assert info_v2["supersedes_number"] == v1_data["report_number"]
    assert len(info_v2["history"]) == 2

    # Download público de PDF por Token
    pdf_pub = await client.get(f"{API}/public/reports/{v2_data['auth_token']}/pdf")
    assert pdf_pub.status_code == 200
    assert pdf_pub.headers["Content-Type"] == "application/pdf"
    assert hashlib.sha256(pdf_pub.content).hexdigest() == v2_data["sha256_hash"]
