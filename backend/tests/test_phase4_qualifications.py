"""Suíte de Testes da Fase 4: Matriz de Competência e Qualificação de Analistas (ISO/IEC 17025 §6.2 / M4.1).

Valida:
1. Concessão formal de qualificação com assinatura eletrônica (21 CFR Part 11).
2. Bloqueio automático de execução analítica de bancada para operador sem qualificação vigente.
3. Desbloqueio após habilitação e registro de treinamentos comprobatórios.
4. Suspensão e revogação de competência técnica com justificativa obrigatória.
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
    reason: str = "Concessão formal de qualificação técnica segundo ISO 17025.",
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


@pytest.mark.anyio
async def test_analyst_qualification_lifecycle_and_execution_guard(
    client: AsyncClient,
    users: dict[str, dict[str, Any]],
) -> None:
    """Valida o ciclo de qualificação e o bloqueio de ensaios por analistas não habilitados."""
    analyst_pass = users["tecnico"]["password"]
    fiscal_pass = users["fiscal"]["password"]

    analyst_auth = await login(client, "tecnico", analyst_pass)
    fiscal_auth = await login(client, "fiscal", fiscal_pass)

    analyst_id = analyst_auth["user"]["id"]

    # 1. Cadastra um Método Analítico padronizado
    method_code = f"MET-COMP-{uuid4().hex[:6].upper()}"
    method_res = await client.post(
        f"{API}/catalog/methods",
        headers=auth(fiscal_auth["access_token"]),
        json={
            "code": method_code,
            "name": "Ensaio de Corrente de Fuga em Condição Normal",
            "standard": "ABNT NBR IEC 60601-1:2010 Cláusula 8.7",
            "version": 1,
            "default_unit": "uA",
            "default_upper_limit": 100.0,
            "category": "Segurança Elétrica Médica",
        },
    )
    assert method_res.status_code == 201, method_res.text
    method = method_res.json()
    method_id = method["id"]

    # 2. Cadastra uma Amostra e Ensaio associado a este método
    sample_id = str(uuid4())
    sig_sample = await issue_signature(
        client,
        fiscal_auth["access_token"],
        fiscal_pass,
        entity_type="DeviceSample",
        entity_id=sample_id,
        action="CREATE",
        meaning="AUTORIA",
    )
    sample_res = await client.post(
        f"{API}/samples",
        headers=signed(fiscal_auth["access_token"], sig_sample["token"]),
        json={
            "id": sample_id,
            "serial_number": f"SN-{uuid4().hex[:6].upper()}",
            "lot_number": "L-F4-COMP",
            "manufacturer": "BioEletronics S.A.",
            "commercial_name": "Monitor Multiparamétrico M10",
            "model": "M-10-HOSP",
            "registration_number": "80000000041",
            "description": "Amostra para validação de competência da Fase 4.",
            "storage_location": "Bancada Metrológica 04",
        },
    )
    assert sample_res.status_code == 201, sample_res.text

    test_id = str(uuid4())
    sig_test = await issue_signature(
        client,
        fiscal_auth["access_token"],
        fiscal_pass,
        entity_type="LabTest",
        entity_id=test_id,
        action="CREATE",
        meaning="AUTORIA",
    )
    test_res = await client.post(
        f"{API}/tests",
        headers=signed(fiscal_auth["access_token"], sig_test["token"]),
        json={
            "id": test_id,
            "device_sample_id": sample_id,
            "name": "Ensaio de Corrente de Fuga",
            "method_id": method_id,
            "unit": "uA",
            "upper_limit": 100.0,
        },
    )
    assert test_res.status_code == 201, test_res.text

    # 3. BLOQUEIO REGULATÓRIO (ISO 17025 §6.2):
    # Analista tenta iniciar execução na bancada sem possuir qualificação para o método
    exec_block_res = await client.post(
        f"{API}/tests/{test_id}/executions",
        headers=auth(analyst_auth["access_token"]),
        json={"notes": "Tentativa de início sem qualificação prévia"},
    )
    assert exec_block_res.status_code == 422, exec_block_res.text
    assert "Bloqueio de Competência Metrológica (ISO/IEC 17025 §6.2)" in exec_block_res.text

    # Verifica status na rota pública/interna de checagem
    check_res = await client.get(
        f"{API}/qualifications/check",
        headers=auth(analyst_auth["access_token"]),
        params={"user_id": analyst_id, "method_id": method_id},
    )
    assert check_res.status_code == 200
    assert check_res.json()["is_qualified"] is False

    # 4. Concessão formal de qualificação pelo Fiscal com assinatura eletrônica
    sig_grant = await issue_signature(
        client,
        fiscal_auth["access_token"],
        fiscal_pass,
        entity_type="User",
        entity_id=analyst_id,
        action="UPDATE",
        meaning="APROVACAO",
        reason="Habilitação técnica após treinamento prático e avaliação de bancada.",
    )
    grant_res = await client.post(
        f"{API}/qualifications/grant",
        headers=signed(fiscal_auth["access_token"], sig_grant["token"]),
        json={
            "user_id": analyst_id,
            "method_id": method_id,
            "status": "QUALIFICADO",
            "scope": "Execução completa de ensaios de segurança elétrica",
            "notes": "Analista concluiu 40h de treinamento em normas ABNT.",
            "trainings": [
                {
                    "title": "Treinamento Prático na Norma IEC 60601-1",
                    "provider": "Instituto Metrológico Nacional",
                    "hours": 40.0,
                    "certificate_code": "CERT-2026-IEC60601",
                }
            ],
        },
    )
    assert grant_res.status_code == 201, grant_res.text
    qual_data = grant_res.json()
    assert qual_data["status"] == "QUALIFICADO"
    assert qual_data["is_active"] is True
    assert len(qual_data["trainings"]) == 1

    # 5. AGORA A EXECUÇÃO DEVE SER PERMITIDA COM SUCESSO!
    exec_allow_res = await client.post(
        f"{API}/tests/{test_id}/executions",
        headers=auth(analyst_auth["access_token"]),
        json={
            "temperature_celsius": 22.5,
            "humidity_percent": 55.0,
            "notes": "Execução autorizada após homologação de competência.",
        },
    )
    assert exec_allow_res.status_code == 201, exec_allow_res.text
    execution = exec_allow_res.json()
    assert execution["status"] == "EM_ANDAMENTO"

    # 6. Suspensão da qualificação por desvio ou reciclagem obrigatória
    sig_revoke = await issue_signature(
        client,
        fiscal_auth["access_token"],
        fiscal_pass,
        entity_type="User",
        entity_id=analyst_id,
        action="UPDATE",
        meaning="APROVACAO",
        reason="Suspensão preventiva para reciclagem.",
    )
    revoke_res = await client.post(
        f"{API}/qualifications/{qual_data['id']}/revoke",
        headers=signed(fiscal_auth["access_token"], sig_revoke["token"]),
        json={
            "status": "SUSPENSO",
            "reason": "Necessária reciclagem periódica após atualização normativa.",
        },
    )
    assert revoke_res.status_code == 200, revoke_res.text
    assert revoke_res.json()["status"] == "SUSPENSO"
    assert revoke_res.json()["is_active"] is False

    # Conclui a execução anterior para tentar iniciar outra
    await client.post(
        f"{API}/executions/{execution['id']}/complete",
        headers=auth(analyst_auth["access_token"]),
        json={"outcome": "APROVADO", "result_value": 45.2},
    )

    # Nova tentativa de execução bloqueada novamente devido ao status SUSPENSO
    exec_blocked_again = await client.post(
        f"{API}/tests/{test_id}/executions",
        headers=auth(analyst_auth["access_token"]),
        json={"notes": "Tentativa com qualificação suspensa"},
    )
    assert exec_blocked_again.status_code == 422
    assert "Habilitação com status impeditivo: SUSPENSO" in exec_blocked_again.text
