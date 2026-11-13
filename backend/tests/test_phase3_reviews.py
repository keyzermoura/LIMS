"""Suíte de Testes da Fase 3: Revisão por Pares, Laudos Periciais Oficiais e Evidências (M3).

Valida:
1. Submissão de ensaios concluídos para revisão técnica colegiada.
2. Segregação estrita de funções (4-eyes principle / ISO/IEC 17025): executor não revisa o próprio ensaio.
3. Parecer técnico com devolução (justificativa obrigatória) ou aprovação.
4. Emissão de Laudo Pericial Oficial consolidado com hash SHA-256 e assinatura eletrônica (21 CFR Part 11).
5. Endpoint público de verificação de autenticidade (QR Code / auth_token).
6. Upload e download de evidências de bancada (dados brutos ALCOA+) com hash SHA-256.
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest
from httpx import AsyncClient

API = "/api/v1"


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def signed(token: str, signature_token: str) -> dict[str, str]:
    return {**auth(token), "X-Signature-Token": signature_token}


async def login(client: AsyncClient, username: str, password: str) -> dict[str, Any]:
    res = await client.post(
        f"{API}/auth/login",
        data={"username": username, "password": password},
    )
    assert res.status_code == 200, res.text
    return res.json()


async def issue_signature(
    client: AsyncClient,
    access_token: str,
    password: str,
    *,
    entity_type: str,
    entity_id: str,
    action: str = "UPDATE",
    meaning: str = "APROVACAO",
    reason: str = "Assinatura técnica eletrônica em conformidade Part 11.",
) -> dict[str, Any]:
    res = await client.post(
        f"{API}/auth/sign",
        headers=auth(access_token),
        json={
            "password": password,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "action": action,
            "meaning": meaning,
            "reason": reason,
        },
    )
    assert res.status_code == 200, res.text
    return res.json()


async def create_sample_fixture(
    client: AsyncClient, access_token: str, password: str
) -> dict[str, Any]:
    sample_id = str(uuid4())
    grant = await issue_signature(
        client,
        access_token,
        password,
        entity_type="DeviceSample",
        entity_id=sample_id,
        action="CREATE",
        meaning="AUTORIA",
        reason="Cadastro e ingresso de amostra no sistema.",
    )
    body = {
        "id": sample_id,
        "serial_number": f"SN-{uuid4().hex[:6].upper()}",
        "lot_number": "L-2026-F3",
        "manufacturer": "BioMed Test Corp",
        "commercial_name": "Ventilador Pulmonar V300",
        "model": "V-300-PRO",
        "registration_number": "80000000003",
        "description": "Amostra para testes de fase 3.",
        "storage_location": "Bancada Metrológica 03",
    }
    res = await client.post(
        f"{API}/samples",
        headers=signed(access_token, grant["token"]),
        json=body,
    )
    assert res.status_code == 201, res.text
    return res.json()["sample"]


async def _create_sample_and_completed_test(
    client: AsyncClient,
    fiscal_token: str,
    fiscal_password: str,
    analyst_token: str,
    analyst_password: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Helper que cadastra amostra, cria ensaio e registra resultado como concluído."""
    sample = await create_sample_fixture(client, fiscal_token, fiscal_password)

    # 2. Cria ensaio
    test_id = str(uuid4())
    grant_test = await issue_signature(
        client,
        fiscal_token,
        fiscal_password,
        entity_type="LabTest",
        entity_id=test_id,
        action="CREATE",
        meaning="AUTORIA",
        reason="Planejamento de ensaio técnico.",
    )
    test_payload = {
        "id": test_id,
        "device_sample_id": sample["id"],
        "name": "Ensaio de Pressão Inspiratória",
        "unit": "cmH2O",
        "lower_limit": 10.0,
        "upper_limit": 40.0,
        "acceptance_criteria": "Entre 10 e 40 cmH2O",
        "parameters": {"flow_rate": 30},
    }
    t_res = await client.post(
        f"{API}/tests",
        headers=signed(fiscal_token, grant_test["token"]),
        json=test_payload,
    )
    assert t_res.status_code == 201, t_res.text

    # 3. Analista assina e conclui ensaio
    sig = await issue_signature(
        client,
        analyst_token,
        analyst_password,
        entity_type="LabTest",
        entity_id=test_id,
        action="UPDATE",
        meaning="AUTORIA",
        reason="Execução analítica e inserção de dados concluída.",
    )

    result_payload = {
        "result_value": 24.5,
        "result_text": "Dentro dos limites especificados",
        "outcome": "APROVADO",
        "version": 1,
        "notes": "Execução analítica em conformidade.",
    }
    post_res = await client.patch(
        f"{API}/tests/{test_id}/result",
        headers=signed(analyst_token, sig["token"]),
        json=result_payload,
    )
    assert post_res.status_code == 200, post_res.text
    completed_test = post_res.json()["test"]
    return sample, completed_test


@pytest.mark.anyio
async def test_peer_review_lifecycle_and_segregation(
    client: AsyncClient,
    users: dict[str, dict[str, Any]],
) -> None:
    """Valida o fluxo completo de revisão por pares e a regra estrita de segregação de funções."""
    analyst_pass = users["tecnico"]["password"]
    reviewer_pass = users["fiscal"]["password"]

    analyst_auth = await login(client, "tecnico", analyst_pass)
    reviewer_auth = await login(client, "fiscal", reviewer_pass)

    sample, test = await _create_sample_and_completed_test(
        client,
        fiscal_token=reviewer_auth["access_token"],
        fiscal_password=reviewer_pass,
        analyst_token=analyst_auth["access_token"],
        analyst_password=analyst_pass,
    )

    test_id = test["id"]

    # 1. Submissão para revisão
    sub_res = await client.post(
        f"{API}/reviews/tests/{test_id}/submit",
        headers=auth(analyst_auth["access_token"]),
        json={"notes": "Ensaio concluído, aguardando revisão técnica."},
    )
    assert sub_res.status_code == 200, sub_res.text
    assert sub_res.json()["review_status"] == "PENDENTE"

    # Ensaio deve aparecer na lista de pendências
    pend_res = await client.get(
        f"{API}/reviews/tests/pending",
        headers=auth(reviewer_auth["access_token"]),
    )
    assert pend_res.status_code == 200
    pending_ids = [t["id"] for t in pend_res.json()]
    assert test_id in pending_ids

    # 2. Violação de Segregação de Funções: O próprio analista executor tenta aprovar o próprio ensaio
    sig_analyst = await issue_signature(
        client,
        analyst_auth["access_token"],
        analyst_pass,
        entity_type="LabTest",
        entity_id=test_id,
        action="UPDATE",
        meaning="APROVACAO",
    )
    viol_res = await client.post(
        f"{API}/reviews/tests/{test_id}/decide",
        headers=signed(analyst_auth["access_token"], sig_analyst["token"]),
        json={"status": "APROVADO", "notes": "Auto-aprovação indevida"},
    )
    assert viol_res.status_code == 422
    assert "Segregação de funções violada" in viol_res.text

    # 3. Devolução com ressalva sem justificativa mínima deve falhar
    dev_invalid = await client.post(
        f"{API}/reviews/tests/{test_id}/decide",
        headers=auth(reviewer_auth["access_token"]),
        json={"status": "DEVOLVIDO", "justification": "Curto"},
    )
    assert dev_invalid.status_code == 422
    assert "Justificativa obrigatória" in dev_invalid.text

    # 4. Devolução válida com justificativa
    dev_valid = await client.post(
        f"{API}/reviews/tests/{test_id}/decide",
        headers=auth(reviewer_auth["access_token"]),
        json={
            "status": "DEVOLVIDO",
            "justification": "Identificada inconsistência no registro da temperatura ambiente.",
        },
    )
    assert dev_valid.status_code == 200, dev_valid.text
    assert dev_valid.json()["status"] == "DEVOLVIDO"

    # 5. Analista re-executa, corrige e ressubmete
    sig_retest = await issue_signature(
        client,
        analyst_auth["access_token"],
        analyst_pass,
        entity_type="LabTest",
        entity_id=test_id,
        action="UPDATE",
        meaning="AUTORIA",
    )
    await client.patch(
        f"{API}/tests/{test_id}/result",
        headers=signed(analyst_auth["access_token"], sig_retest["token"]),
        json={
            "result_value": 25.0,
            "result_text": "Temperatura corrigida e estável",
            "outcome": "APROVADO",
            "version": 2,
            "amendment_reason": "Correção de dados com apontamento da revisão técnica.",
        },
    )
    await client.post(
        f"{API}/reviews/tests/{test_id}/submit",
        headers=auth(analyst_auth["access_token"]),
        json={"notes": "Ressubmissão após correção."},
    )

    # 6. Revisor independente aprova com assinatura eletrônica
    sig_reviewer = await issue_signature(
        client,
        reviewer_auth["access_token"],
        reviewer_pass,
        entity_type="LabTest",
        entity_id=test_id,
        action="UPDATE",
        meaning="APROVACAO",
    )
    approve_res = await client.post(
        f"{API}/reviews/tests/{test_id}/decide",
        headers=signed(reviewer_auth["access_token"], sig_reviewer["token"]),
        json={
            "status": "APROVADO",
            "notes": "Parâmetros verificados e validados por amostragem independente.",
        },
    )
    assert approve_res.status_code == 200, approve_res.text
    assert approve_res.json()["status"] == "APROVADO"

    # Histórico de revisões
    hist_res = await client.get(
        f"{API}/reviews/tests/{test_id}",
        headers=auth(reviewer_auth["access_token"]),
    )
    assert hist_res.status_code == 200
    assert len(hist_res.json()) >= 2


@pytest.mark.anyio
async def test_official_report_issuance_and_public_verification(
    client: AsyncClient,
    users: dict[str, dict[str, Any]],
) -> None:
    """Valida a emissão do laudo pericial oficial e sua autenticação pública por QR Code / token."""
    analyst_pass = users["tecnico"]["password"]
    fiscal_pass = users["fiscal"]["password"]

    analyst_auth = await login(client, "tecnico", analyst_pass)
    fiscal_auth = await login(client, "fiscal", fiscal_pass)

    sample, test = await _create_sample_and_completed_test(
        client,
        fiscal_token=fiscal_auth["access_token"],
        fiscal_password=fiscal_pass,
        analyst_token=analyst_auth["access_token"],
        analyst_password=analyst_pass,
    )

    test_id = test["id"]
    sample_id = sample["id"]

    # Submete e aprova o ensaio
    await client.post(
        f"{API}/reviews/tests/{test_id}/submit",
        headers=auth(analyst_auth["access_token"]),
        json={},
    )
    await client.post(
        f"{API}/reviews/tests/{test_id}/decide",
        headers=auth(fiscal_auth["access_token"]),
        json={"status": "APROVADO", "notes": "Ensaio homologado."},
    )

    # Assina emissão do laudo
    sig_report = await issue_signature(
        client,
        fiscal_auth["access_token"],
        fiscal_pass,
        entity_type="DeviceSample",
        entity_id=sample_id,
        action="CLOSE",
        meaning="RESPONSABILIDADE_TECNICA",
        reason="Emissão formal de Laudo Pericial Oficial de Conformidade Técnica.",
    )

    report_payload = {
        "device_sample_id": sample_id,
        "test_ids": [test_id],
        "title": "Laudo Pericial Oficial de Conformidade Mecânica",
        "conclusion": "APROVADO",
        "summary": "O lote de dispositivos atende a todos os critérios regulatórios aplicáveis.",
    }
    rep_res = await client.post(
        f"{API}/reports/official",
        headers=signed(fiscal_auth["access_token"], sig_report["token"]),
        json=report_payload,
    )
    assert rep_res.status_code == 200, rep_res.text
    report = rep_res.json()
    assert report["report_number"].startswith("LDO-")
    assert len(report["sha256_hash"]) == 64
    assert len(report["auth_token"]) >= 20

    # Verificação pública (sem token de autorização / anônima)
    verify_res = await client.get(f"{API}/reports/verify/{report['auth_token']}")
    assert verify_res.status_code == 200, verify_res.text
    verify_data = verify_res.json()
    assert verify_data["is_valid"] is True
    assert verify_data["report_number"] == report["report_number"]
    assert verify_data["sha256_hash"] == report["sha256_hash"]
    assert verify_data["sample_acc_number"] == sample["accession_number"]


@pytest.mark.anyio
async def test_evidence_attachment_integrity(
    client: AsyncClient,
    users: dict[str, dict[str, Any]],
) -> None:
    """Valida o repositório de evidências brutas de bancada com cálculo de hash SHA-256."""
    analyst_pass = users["tecnico"]["password"]
    fiscal_pass = users["fiscal"]["password"]

    analyst_auth = await login(client, "tecnico", analyst_pass)
    fiscal_auth = await login(client, "fiscal", fiscal_pass)

    sample, test = await _create_sample_and_completed_test(
        client,
        fiscal_token=fiscal_auth["access_token"],
        fiscal_password=fiscal_pass,
        analyst_token=analyst_auth["access_token"],
        analyst_password=analyst_pass,
    )
    test_id = test["id"]

    # Upload de arquivo binário / curva de ensaio
    raw_data = b"CURVA_DE_CALIBRACAO_E_PRESSAO_RAW_DATA_1234567890"
    files = {"file": ("curva_pressao.bin", raw_data, "application/octet-stream")}
    up_res = await client.post(
        f"{API}/attachments/tests/{test_id}",
        headers=auth(analyst_auth["access_token"]),
        files=files,
    )
    assert up_res.status_code == 200, up_res.text
    attachment = up_res.json()
    assert attachment["filename"] == "curva_pressao.bin"
    assert attachment["file_size"] == len(raw_data)
    assert len(attachment["sha256_hash"]) == 64

    # Download do arquivo
    down_res = await client.get(
        f"{API}/attachments/{attachment['id']}/download",
        headers=auth(analyst_auth["access_token"]),
    )
    assert down_res.status_code == 200
    assert down_res.content == raw_data
    assert down_res.headers["X-SHA256-Checksum"] == attachment["sha256_hash"]
