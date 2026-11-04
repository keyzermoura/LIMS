"""Fluxos HTTP ponta a ponta: autenticação, assinatura, custódia, laudo e CAPA.

Estes testes sobem a aplicação FastAPI real (middlewares, dependências, RBAC,
handlers de erro) sobre um banco isolado por teste: SQLite por padrão ou
PostgreSQL quando `LIMS_TEST_DATABASE_URL` está definido.
"""

from __future__ import annotations

import os
from datetime import timedelta
from typing import Any
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.audit_log import AuditLog
from app.models.base import utcnow
from app.services import signature_service

API = "/api/v1"
IS_POSTGRES = bool(os.getenv("LIMS_TEST_DATABASE_URL"))


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def signed(token: str, signature_token: str) -> dict[str, str]:
    return {**auth(token), "X-Signature-Token": signature_token}


async def login(
    client: AsyncClient, username: str, password: str
) -> dict[str, Any]:
    response = await client.post(
        f"{API}/auth/login",
        data={"username": username, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()


async def issue_signature(
    client: AsyncClient,
    access_token: str,
    password: str,
    *,
    entity_type: str,
    entity_id: str,
    action: str = "CREATE",
    meaning: str = "AUTORIA",
) -> dict[str, Any]:
    response = await client.post(
        f"{API}/auth/sign",
        headers=auth(access_token),
        json={
            "password": password,
            "meaning": meaning,
            "reason": "Assinatura de teste de integração vinculada ao registro.",
            "entity_type": entity_type,
            "entity_id": str(entity_id),
            "action": action,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def sample_body(
    sample_id: str, *, serial: str = "SN-100", lot: str = "L-100"
) -> dict[str, Any]:
    return {
        "id": sample_id,
        "serial_number": serial,
        "lot_number": lot,
        "manufacturer": "Fabricante de Teste Ltda.",
        "commercial_name": "Monitor de Sinais Vitais",
        "model": "MVP-1",
        "registration_number": "80000000001",
        "description": "Amostra coletada em fiscalização de teste.",
        "storage_location": "Prateleira A1",
    }


async def create_sample(
    client: AsyncClient,
    access_token: str,
    password: str,
    *,
    serial: str = "SN-100",
    lot: str = "L-100",
) -> dict[str, Any]:
    sample_id = str(uuid4())
    grant = await issue_signature(
        client,
        access_token,
        password,
        entity_type="DeviceSample",
        entity_id=sample_id,
        action="CREATE",
    )
    response = await client.post(
        f"{API}/samples",
        headers=signed(access_token, grant["token"]),
        json=sample_body(sample_id, serial=serial, lot=lot),
    )
    assert response.status_code == 201, response.text
    return response.json()


async def create_test(
    client: AsyncClient,
    access_token: str,
    password: str,
    *,
    sample_id: str,
    assigned_to_id: str,
    lower: float = 4.5,
    upper: float = 5.5,
) -> dict[str, Any]:
    test_id = str(uuid4())
    grant = await issue_signature(
        client,
        access_token,
        password,
        entity_type="LabTest",
        entity_id=test_id,
        action="CREATE",
    )
    response = await client.post(
        f"{API}/tests",
        headers=signed(access_token, grant["token"]),
        json={
            "id": test_id,
            "device_sample_id": sample_id,
            "name": "Vazão de infusão",
            "method": "Gravimetria",
            "parameters": {"temperatura": "23 °C"},
            "unit": "ml/h",
            "lower_limit": lower,
            "upper_limit": upper,
            "acceptance_criteria": "Vazão dentro de ±10% do ajuste.",
            "assigned_to_id": assigned_to_id,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["test"]


async def test_login_profile_and_audit_rbac(client: AsyncClient, users) -> None:
    fiscal = await login(client, "fiscal", users["fiscal"]["password"])

    me = await client.get(f"{API}/auth/me", headers=auth(fiscal["access_token"]))
    assert me.status_code == 200
    assert me.json()["role"] == "FISCAL"
    assert "samples:create" in me.json()["permissions"]

    tecnico = await login(client, "tecnico", users["tecnico"]["password"])
    denied = await client.get(f"{API}/audit", headers=auth(tecnico["access_token"]))
    assert denied.status_code == 403

    auditor = await login(client, "auditor", users["auditor"]["password"])
    allowed = await client.get(f"{API}/audit", headers=auth(auditor["access_token"]))
    assert allowed.status_code == 200
    assert allowed.json()["total"] >= 1  # eventos de LOGIN já registrados


async def test_sample_creation_requires_signature(
    client: AsyncClient, users
) -> None:
    fiscal = await login(client, "fiscal", users["fiscal"]["password"])
    body = sample_body(str(uuid4()))

    denied = await client.post(
        f"{API}/samples", headers=auth(fiscal["access_token"]), json=body
    )
    assert denied.status_code == 401
    assert denied.json()["code"] == "ESIGNATURE_REJECTED"

    created = await create_sample(
        client,
        fiscal["access_token"],
        users["fiscal"]["password"],
        serial="SN-REQ",
        lot="L-REQ",
    )
    sample = created["sample"]
    assert sample["status"] == "RECEBIDO"
    assert sample["accession_number"].startswith("LIMS-")
    assert sample["current_custodian"]["username"] == "fiscal"

    timeline = await client.get(
        f"{API}/samples/{sample['id']}/timeline",
        headers=auth(fiscal["access_token"]),
    )
    assert timeline.status_code == 200
    assert {"RECEIPT", "CUSTODY"} <= {event["type"] for event in timeline.json()}


async def test_signature_token_is_single_use(client: AsyncClient, users) -> None:
    fiscal = await login(client, "fiscal", users["fiscal"]["password"])
    sample_id = str(uuid4())
    grant = await issue_signature(
        client,
        fiscal["access_token"],
        users["fiscal"]["password"],
        entity_type="DeviceSample",
        entity_id=sample_id,
    )
    headers = signed(fiscal["access_token"], grant["token"])
    body = sample_body(sample_id, serial="SN-ONE", lot="L-ONE")

    first = await client.post(f"{API}/samples", headers=headers, json=body)
    assert first.status_code == 201

    replay = await client.post(f"{API}/samples", headers=headers, json=body)
    assert replay.status_code == 409
    assert replay.json()["code"] == "ESIGNATURE_REJECTED"

    auditor = await login(client, "auditor", users["auditor"]["password"])
    audit = await client.get(
        f"{API}/audit",
        params={"action": "SIGNATURE_REJECTED"},
        headers=auth(auditor["access_token"]),
    )
    assert audit.status_code == 200
    assert audit.json()["total"] >= 1


async def test_signature_is_bound_to_the_entity(client: AsyncClient, users) -> None:
    fiscal = await login(client, "fiscal", users["fiscal"]["password"])
    signed_id = str(uuid4())
    other_id = str(uuid4())
    grant = await issue_signature(
        client,
        fiscal["access_token"],
        users["fiscal"]["password"],
        entity_type="DeviceSample",
        entity_id=signed_id,
    )
    headers = signed(fiscal["access_token"], grant["token"])

    wrong = await client.post(
        f"{API}/samples",
        headers=headers,
        json=sample_body(other_id, serial="SN-WRONG", lot="L-WRONG"),
    )
    assert wrong.status_code == 403

    # A rejeição não consome o token: o registro correto ainda pode ser assinado.
    right = await client.post(
        f"{API}/samples",
        headers=headers,
        json=sample_body(signed_id, serial="SN-RIGHT", lot="L-RIGHT"),
    )
    assert right.status_code == 201


async def test_custody_transfer_only_by_current_custodian(
    client: AsyncClient, users
) -> None:
    fiscal = await login(client, "fiscal", users["fiscal"]["password"])
    created = await create_sample(
        client,
        fiscal["access_token"],
        users["fiscal"]["password"],
        serial="SN-CUS",
        lot="L-CUS",
    )
    sample = created["sample"]

    transfer_body = {
        "device_sample_id": sample["id"],
        "to_custodian_id": users["custodiante"]["id"],
        "reason": "Transferência para o laboratório de ensaios.",
        "storage_location": "Prateleira B2",
        "seal_number": "SELO-2026-01",
        "version": sample["version"],
    }

    tecnico = await login(client, "tecnico", users["tecnico"]["password"])
    tec_grant = await issue_signature(
        client,
        tecnico["access_token"],
        users["tecnico"]["password"],
        entity_type="DeviceSample",
        entity_id=sample["id"],
        action="TRANSFER",
        meaning="TRANSFERENCIA_DE_CUSTODIA",
    )
    denied = await client.post(
        f"{API}/custody/transfer",
        headers=signed(tecnico["access_token"], tec_grant["token"]),
        json=transfer_body,
    )
    assert denied.status_code == 403

    fiscal_grant = await issue_signature(
        client,
        fiscal["access_token"],
        users["fiscal"]["password"],
        entity_type="DeviceSample",
        entity_id=sample["id"],
        action="TRANSFER",
        meaning="TRANSFERENCIA_DE_CUSTODIA",
    )
    accepted = await client.post(
        f"{API}/custody/transfer",
        headers=signed(fiscal["access_token"], fiscal_grant["token"]),
        json=transfer_body,
    )
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["sample"]["current_custodian"]["username"] == "custodiante"


async def test_reproved_result_opens_capa(client: AsyncClient, users) -> None:
    fiscal = await login(client, "fiscal", users["fiscal"]["password"])
    tecnico = await login(client, "tecnico", users["tecnico"]["password"])

    created = await create_sample(
        client,
        fiscal["access_token"],
        users["fiscal"]["password"],
        serial="SN-FAIL",
        lot="L-FAIL",
    )
    sample_id = created["sample"]["id"]
    test = await create_test(
        client,
        fiscal["access_token"],
        users["fiscal"]["password"],
        sample_id=sample_id,
        assigned_to_id=users["tecnico"]["id"],
    )

    grant = await issue_signature(
        client,
        tecnico["access_token"],
        users["tecnico"]["password"],
        entity_type="LabTest",
        entity_id=test["id"],
        action="UPDATE",
        meaning="RESPONSABILIDADE_TECNICA",
    )
    result = await client.patch(
        f"{API}/tests/{test['id']}/result",
        headers=signed(tecnico["access_token"], grant["token"]),
        json={"result_value": 6.2, "version": test["version"]},
    )
    assert result.status_code == 200, result.text
    payload = result.json()
    assert payload["result_version"]["outcome"] == "REPROVADO"
    assert payload["alert"]["code"] == "RESULTADO_REPROVADO"
    assert payload["capa_id"] is not None

    sample = await client.get(
        f"{API}/samples/{sample_id}", headers=auth(fiscal["access_token"])
    )
    assert sample.json()["status"] == "REPROVADO"

    capas = await client.get(
        f"{API}/capas",
        params={"sample_id": sample_id},
        headers=auth(fiscal["access_token"]),
    )
    assert capas.status_code == 200
    capa = capas.json()["items"][0]
    assert capa["auto_opened"] is True
    assert capa["lab_test_id"] == test["id"]
    assert capa["status"] == "ABERTA"

    # Resultado assinado é imutável: corrigir exige motivo de emenda.
    amendment = await client.patch(
        f"{API}/tests/{test['id']}/result",
        headers=signed(tecnico["access_token"], grant["token"]),
        json={"result_value": 5.0, "version": payload["test"]["version"]},
    )
    assert amendment.status_code == 409


async def test_manual_approval_requires_all_tests_approved(
    client: AsyncClient, users
) -> None:
    fiscal = await login(client, "fiscal", users["fiscal"]["password"])
    created = await create_sample(
        client,
        fiscal["access_token"],
        users["fiscal"]["password"],
        serial="SN-PEND",
        lot="L-PEND",
    )
    sample = created["sample"]
    await create_test(
        client,
        fiscal["access_token"],
        users["fiscal"]["password"],
        sample_id=sample["id"],
        assigned_to_id=users["tecnico"]["id"],
    )

    # `create_test` já move a amostra para EM_TESTE, mas o ensaio está pendente.
    current = await client.get(
        f"{API}/samples/{sample['id']}", headers=auth(fiscal["access_token"])
    )
    version = current.json()["version"]

    grant = await issue_signature(
        client,
        fiscal["access_token"],
        users["fiscal"]["password"],
        entity_type="DeviceSample",
        entity_id=sample["id"],
        action="UPDATE",
        meaning="APROVACAO",
    )
    denied = await client.patch(
        f"{API}/samples/{sample['id']}/status",
        headers=signed(fiscal["access_token"], grant["token"]),
        json={
            "status": "APROVADO",
            "reason": "Tentativa de aprovação com ensaio pendente.",
            "version": version,
        },
    )
    assert denied.status_code == 422
    assert "todos os ensaios" in denied.json()["detail"]


async def test_refresh_rotation_detects_reuse(client: AsyncClient, users) -> None:
    first = await login(client, "fiscal", users["fiscal"]["password"])

    rotated = await client.post(
        f"{API}/auth/refresh", json={"refresh_token": first["refresh_token"]}
    )
    assert rotated.status_code == 200, rotated.text
    second = rotated.json()

    reuse = await client.post(
        f"{API}/auth/refresh", json={"refresh_token": first["refresh_token"]}
    )
    assert reuse.status_code == 403

    # Reutilização revoga TODAS as sessões, inclusive a recém-rotacionada.
    blocked = await client.post(
        f"{API}/auth/refresh", json={"refresh_token": second["refresh_token"]}
    )
    assert blocked.status_code == 403

    stale_access = await client.get(
        f"{API}/auth/me", headers=auth(second["access_token"])
    )
    assert stale_access.status_code == 401


async def test_audit_chain_verification_detects_tampering(
    client: AsyncClient,
    users,
    db_factory: async_sessionmaker[AsyncSession],
) -> None:
    fiscal = await login(client, "fiscal", users["fiscal"]["password"])
    await create_sample(
        client,
        fiscal["access_token"],
        users["fiscal"]["password"],
        serial="SN-AUD",
        lot="L-AUD",
    )

    auditor = await login(client, "auditor", users["auditor"]["password"])
    before = await client.post(
        f"{API}/audit/verify", headers=auth(auditor["access_token"])
    )
    assert before.status_code == 200
    assert before.json()["ok"] is True

    async def tamper() -> None:
        async with db_factory() as db:
            row = await db.scalar(
                select(AuditLog).order_by(AuditLog.sequence.asc()).limit(1)
            )
            assert row is not None
            row.payload = {**row.payload, "reason": "CONTEÚDO ADULTERADO"}
            await db.commit()

    if IS_POSTGRES:
        # No PostgreSQL o trigger append-only impede a adulteração antes que
        # ela chegue ao disco; a cadeia permanece íntegra.
        with pytest.raises(DBAPIError, match="append-only"):
            await tamper()

        after = await client.post(
            f"{API}/audit/verify", headers=auth(auditor["access_token"])
        )
        assert after.json()["ok"] is True
        return

    # No SQLite (sem triggers) a adulteração é detectada pela cadeia de hashes.
    await tamper()
    after = await client.post(
        f"{API}/audit/verify", headers=auth(auditor["access_token"])
    )
    assert after.status_code == 200
    report = after.json()
    assert report["ok"] is False
    assert any(issue["type"] == "HASH_MISMATCH" for issue in report["issues"])


async def test_expired_signature_is_rejected(
    client: AsyncClient,
    users,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fiscal = await login(client, "fiscal", users["fiscal"]["password"])
    sample_id = str(uuid4())
    grant = await issue_signature(
        client,
        fiscal["access_token"],
        users["fiscal"]["password"],
        entity_type="DeviceSample",
        entity_id=sample_id,
    )

    # O JWT da assinatura continua válido; quem expira é o registro no banco.
    # Avançamos o relógio apenas no serviço para exercitar essa checagem sem
    # alterar a linha protegida pelo trigger de imutabilidade.
    monkeypatch.setattr(
        signature_service,
        "utcnow",
        lambda: utcnow() + timedelta(minutes=10),
    )

    response = await client.post(
        f"{API}/samples",
        headers=signed(fiscal["access_token"], grant["token"]),
        json=sample_body(sample_id, serial="SN-EXP", lot="L-EXP"),
    )
    assert response.status_code == 401
    assert "expirad" in response.json()["detail"].lower()


async def test_only_assigned_tester_can_sign_the_report(
    client: AsyncClient, users
) -> None:
    fiscal = await login(client, "fiscal", users["fiscal"]["password"])
    created = await create_sample(
        client,
        fiscal["access_token"],
        users["fiscal"]["password"],
        serial="SN-OWN",
        lot="L-OWN",
    )
    test = await create_test(
        client,
        fiscal["access_token"],
        users["fiscal"]["password"],
        sample_id=created["sample"]["id"],
        assigned_to_id=users["tecnico"]["id"],
    )

    other_tester = await login(client, "tecnico2", users["tecnico2"]["password"])
    grant = await issue_signature(
        client,
        other_tester["access_token"],
        users["tecnico2"]["password"],
        entity_type="LabTest",
        entity_id=test["id"],
        action="UPDATE",
        meaning="RESPONSABILIDADE_TECNICA",
    )
    denied = await client.patch(
        f"{API}/tests/{test['id']}/result",
        headers=signed(other_tester["access_token"], grant["token"]),
        json={"result_value": 5.0, "version": test["version"]},
    )
    assert denied.status_code == 403

    owner = await login(client, "tecnico", users["tecnico"]["password"])
    owner_grant = await issue_signature(
        client,
        owner["access_token"],
        users["tecnico"]["password"],
        entity_type="LabTest",
        entity_id=test["id"],
        action="UPDATE",
        meaning="RESPONSABILIDADE_TECNICA",
    )
    accepted = await client.patch(
        f"{API}/tests/{test['id']}/result",
        headers=signed(owner["access_token"], owner_grant["token"]),
        json={"result_value": 5.0, "version": test["version"]},
    )
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["result_version"]["outcome"] == "APROVADO"
