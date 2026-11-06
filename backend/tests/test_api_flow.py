"""Fluxos HTTP ponta a ponta: autenticação, assinatura, custódia, laudo e CAPA.

Estes testes sobem a aplicação FastAPI real (middlewares, dependências, RBAC,
handlers de erro) sobre um banco isolado por teste: SQLite por padrão ou
PostgreSQL quando `LIMS_TEST_DATABASE_URL` está definido.
"""

from __future__ import annotations

import io
import json
import os
import zipfile
from datetime import timedelta
from typing import Any
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import settings
from app.core.security import hmac_sha256, sha256_hex
from app.core.serialization import canonical_json
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
    assigned_to_id: str | None = None,
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
    body: dict[str, Any] = {
        "id": test_id,
        "device_sample_id": sample_id,
        "name": "Vazão de infusão",
        "method": "Gravimetria",
        "parameters": {"temperatura": "23 °C"},
        "unit": "ml/h",
        "lower_limit": lower,
        "upper_limit": upper,
        "acceptance_criteria": "Vazão dentro de ±10% do ajuste.",
    }
    if assigned_to_id is not None:
        body["assigned_to_id"] = assigned_to_id
    response = await client.post(
        f"{API}/tests",
        headers=signed(access_token, grant["token"]),
        json=body,
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

    # A conclusão da CAPA é uma atualização assinada (PATCH /capas/{id}).
    close_grant = await issue_signature(
        client,
        fiscal["access_token"],
        users["fiscal"]["password"],
        entity_type="CapaAction",
        entity_id=capa["id"],
        action="UPDATE",
        meaning="VERIFICACAO",
    )
    closed = await client.patch(
        f"{API}/capas/{capa['id']}",
        headers=signed(fiscal["access_token"], close_grant["token"]),
        json={
            "status": "CONCLUIDA",
            "effectiveness_check": (
                "Lote reensaiado após a ação corretiva; resultados dentro do limite."
            ),
            "version": capa["version"],
        },
    )
    assert closed.status_code == 200, closed.text
    assert closed.json()["status"] == "CONCLUIDA"
    assert closed.json()["closed_at"] is not None

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


async def test_fiscal_created_test_without_assignee_can_be_signed_by_technician(
    client: AsyncClient, users
) -> None:
    """Ensaio programado por FISCAL sem designação fica aberto para o técnico.

    O fiscal não tem competência para assinar laudos; se a criação o marcasse
    como testador responsável, o ensaio ficaria permanentemente sem assinatura.
    """
    fiscal = await login(client, "fiscal", users["fiscal"]["password"])
    created = await create_sample(
        client,
        fiscal["access_token"],
        users["fiscal"]["password"],
        serial="SN-OPEN",
        lot="L-OPEN",
    )
    test = await create_test(
        client,
        fiscal["access_token"],
        users["fiscal"]["password"],
        sample_id=created["sample"]["id"],
    )
    assert test["tested_by"] is None
    assert test["assigned_to_id"] is None

    tecnico = await login(client, "tecnico", users["tecnico"]["password"])
    grant = await issue_signature(
        client,
        tecnico["access_token"],
        users["tecnico"]["password"],
        entity_type="LabTest",
        entity_id=test["id"],
        action="UPDATE",
        meaning="RESPONSABILIDADE_TECNICA",
    )
    signed_response = await client.patch(
        f"{API}/tests/{test['id']}/result",
        headers=signed(tecnico["access_token"], grant["token"]),
        json={"result_value": 5.0, "version": test["version"]},
    )
    assert signed_response.status_code == 200, signed_response.text
    assert signed_response.json()["result_version"]["outcome"] == "APROVADO"
    assert signed_response.json()["test"]["tested_by"]["username"] == "tecnico"


# ---------------------------------------------------------------------------
# Bloqueio por tentativas de senha e rate limiting
# ---------------------------------------------------------------------------
def _wrong_sign_payload(password: str = "SenhaErrada@2026") -> dict[str, str]:
    return {
        "password": password,
        "meaning": "RESPONSABILIDADE_TECNICA",
        "reason": "Teste de bloqueio por tentativas de reautenticacao.",
        "entity_type": "LabTest",
        "entity_id": str(uuid4()),
        "action": "UPDATE",
    }


async def test_sign_wrong_password_locks_account(client: AsyncClient, users) -> None:
    tecnico = await login(client, "tecnico", users["tecnico"]["password"])
    payload = _wrong_sign_payload()

    statuses: list[int] = []
    for _ in range(settings.MAX_LOGIN_ATTEMPTS):
        response = await client.post(
            f"{API}/auth/sign", headers=auth(tecnico["access_token"]), json=payload
        )
        statuses.append(response.status_code)

    # As primeiras falhas devolvem 401; a ultima bloqueia a conta (403).
    assert statuses[:-1] == [401] * (settings.MAX_LOGIN_ATTEMPTS - 1), statuses
    assert statuses[-1] == 403, statuses

    # Com a conta bloqueada nem a senha correta emite assinatura...
    locked = await client.post(
        f"{API}/auth/sign",
        headers=auth(tecnico["access_token"]),
        json=_wrong_sign_payload(users["tecnico"]["password"]),
    )
    assert locked.status_code == 403
    assert "bloqueada" in locked.json()["detail"].lower()

    # ...nem o login.
    denied = await client.post(
        f"{API}/auth/login",
        data={"username": "tecnico", "password": users["tecnico"]["password"]},
    )
    assert denied.status_code == 403
    assert "bloqueada" in denied.json()["detail"].lower()


async def test_successful_signature_resets_failed_attempts(
    client: AsyncClient, users
) -> None:
    tecnico = await login(client, "tecnico", users["tecnico"]["password"])
    wrong = _wrong_sign_payload()

    for _ in range(settings.MAX_LOGIN_ATTEMPTS - 1):
        response = await client.post(
            f"{API}/auth/sign", headers=auth(tecnico["access_token"]), json=wrong
        )
        assert response.status_code == 401

    grant = await issue_signature(
        client,
        tecnico["access_token"],
        users["tecnico"]["password"],
        entity_type="LabTest",
        entity_id=str(uuid4()),
    )
    assert grant["token"]

    # A reautenticacao correta zerou o contador: novas falhas continuam em 401
    # em vez de bloquear a conta.
    for _ in range(settings.MAX_LOGIN_ATTEMPTS - 1):
        response = await client.post(
            f"{API}/auth/sign", headers=auth(tecnico["access_token"]), json=wrong
        )
        assert response.status_code == 401, response.text


async def test_login_rate_limit_returns_429(
    client: AsyncClient,
    users,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "LOGIN_RATE_LIMIT", 2)

    responses = [
        await client.post(
            f"{API}/auth/login",
            data={"username": "fiscal", "password": "SenhaErrada@2026"},
        )
        for _ in range(3)
    ]

    assert [r.status_code for r in responses[:2]] == [403, 403]
    limited = responses[2]
    assert limited.status_code == 429
    assert limited.json()["code"] == "RATE_LIMITED"
    assert int(limited.headers["Retry-After"]) >= 1


async def test_sign_rate_limit_returns_429(
    client: AsyncClient,
    users,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "SIGN_RATE_LIMIT", 1)
    tecnico = await login(client, "tecnico", users["tecnico"]["password"])
    payload = _wrong_sign_payload()

    first = await client.post(
        f"{API}/auth/sign", headers=auth(tecnico["access_token"]), json=payload
    )
    assert first.status_code == 401

    limited = await client.post(
        f"{API}/auth/sign", headers=auth(tecnico["access_token"]), json=payload
    )
    assert limited.status_code == 429
    assert limited.json()["code"] == "RATE_LIMITED"
    assert int(limited.headers["Retry-After"]) >= 1

def _rewrite_zip(content: bytes, replacements: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(content)) as source, zipfile.ZipFile(
        buffer, "w", compression=zipfile.ZIP_DEFLATED
    ) as target:
        for info in source.infolist():
            target.writestr(info, replacements.get(info.filename, source.read(info.filename)))
    return buffer.getvalue()


def _bundle_entries(content: bytes) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        records = [
            json.loads(line)
            for line in archive.read("events.jsonl").decode("utf-8").splitlines()
            if line.strip()
        ]
    return manifest, records


async def test_audit_export_bundle_is_verifiable(client: AsyncClient, users) -> None:
    fiscal = await login(client, "fiscal", users["fiscal"]["password"])
    await create_sample(
        client,
        fiscal["access_token"],
        users["fiscal"]["password"],
        serial="SN-EXP1",
        lot="L-EXP1",
    )
    auditor = await login(client, "auditor", users["auditor"]["password"])

    response = await client.post(
        f"{API}/audit/export",
        headers=auth(auditor["access_token"]),
        json={"format": "csv"},
    )
    assert response.status_code == 200, response.text
    assert response.headers["content-type"] == "application/zip"
    assert "attachment" in response.headers["content-disposition"]
    assert response.headers["x-audit-export-id"]
    assert response.headers["x-audit-export-manifest-hash"]

    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        names = set(archive.namelist())
        assert {"manifest.json", "events.jsonl", "events.csv"} <= names
        manifest = json.loads(archive.read("manifest.json"))
        data_bytes = archive.read("events.jsonl")
        records = [
            json.loads(line)
            for line in data_bytes.decode("utf-8").splitlines()
            if line.strip()
        ]

    assert manifest["format"] == "lims-audit-export-v1"
    assert manifest["presentation"] == "csv"
    assert manifest["record_count"] == len(records) >= 1
    assert manifest["data_sha256"] == sha256_hex(data_bytes)
    key = settings.AUDIT_HMAC_KEY.get_secret_value()
    assert manifest["data_hmac"] == hmac_sha256(key, manifest["data_sha256"])
    core = {
        field: value
        for field, value in manifest.items()
        if field not in {"manifest_hash", "hmac"}
    }
    assert manifest["manifest_hash"] == sha256_hex(canonical_json(core))
    assert manifest["hmac"] == hmac_sha256(key, manifest["manifest_hash"])

    for record in records:
        expected_hash = sha256_hex(
            f"{record['sequence']}:{record['prev_hash']}:"
            f"{canonical_json(record['payload'])}"
        )
        assert record["hash"] == expected_hash
        assert record["hmac"] == hmac_sha256(key, record["hash"])

    verification = await client.post(
        f"{API}/audit/export/verify",
        headers=auth(auditor["access_token"]),
        files={"file": ("trilha.zip", response.content, "application/zip")},
    )
    assert verification.status_code == 200, verification.text
    report = verification.json()
    assert report["ok"] is True, report
    assert report["checked"] == len(records)
    assert report["manifest_hash_ok"] is True
    assert report["data_hash_ok"] is True
    assert report["chain_ok"] is True
    assert report["matches_database"] is True

    exports = await client.get(
        f"{API}/audit",
        params={"action": "EXPORT"},
        headers=auth(auditor["access_token"]),
    )
    assert exports.json()["total"] >= 1
    checks = await client.get(
        f"{API}/audit",
        params={"action": "EXPORT_VERIFIED"},
        headers=auth(auditor["access_token"]),
    )
    assert checks.json()["total"] >= 1


async def test_audit_export_honors_filters_and_rbac(client: AsyncClient, users) -> None:
    fiscal = await login(client, "fiscal", users["fiscal"]["password"])
    await create_sample(
        client,
        fiscal["access_token"],
        users["fiscal"]["password"],
        serial="SN-EXP2",
        lot="L-EXP2",
    )
    auditor = await login(client, "auditor", users["auditor"]["password"])

    filtered = await client.post(
        f"{API}/audit/export",
        headers=auth(auditor["access_token"]),
        json={"format": "json", "action": "LOGIN", "search": "auditor"},
    )
    assert filtered.status_code == 200, filtered.text
    with zipfile.ZipFile(io.BytesIO(filtered.content)) as archive:
        assert "events.json" in archive.namelist()
        assert "events.csv" not in archive.namelist()
        manifest = json.loads(archive.read("manifest.json"))
        records = [
            json.loads(line)
            for line in archive.read("events.jsonl").decode("utf-8").splitlines()
            if line.strip()
        ]
    assert manifest["scope"]["action"] == "LOGIN"
    assert records
    assert all(record["action"] == "LOGIN" for record in records)
    assert all(record["actor_username"] == "auditor" for record in records)

    verified = await client.post(
        f"{API}/audit/export/verify",
        headers=auth(auditor["access_token"]),
        files={"file": ("filtrado.zip", filtered.content, "application/zip")},
    )
    assert verified.status_code == 200, verified.text
    assert verified.json()["ok"] is True, verified.json()

    empty = await client.post(
        f"{API}/audit/export",
        headers=auth(auditor["access_token"]),
        json={
            "format": "csv",
            "date_from": (utcnow() + timedelta(days=1)).isoformat(),
        },
    )
    assert empty.status_code == 200, empty.text
    empty_manifest, empty_records = _bundle_entries(empty.content)
    assert empty_manifest["record_count"] == 0
    assert empty_records == []
    empty_verification = await client.post(
        f"{API}/audit/export/verify",
        headers=auth(auditor["access_token"]),
        files={"file": ("vazio.zip", empty.content, "application/zip")},
    )
    assert empty_verification.status_code == 200
    assert empty_verification.json()["ok"] is True

    tecnico = await login(client, "tecnico", users["tecnico"]["password"])
    denied = await client.post(
        f"{API}/audit/export",
        headers=auth(tecnico["access_token"]),
        json={"format": "csv"},
    )
    assert denied.status_code == 403

    admin = await login(client, "admin", users["admin"]["password"])
    allowed = await client.post(
        f"{API}/audit/export",
        headers=auth(admin["access_token"]),
        json={"format": "csv"},
    )
    assert allowed.status_code == 200


async def test_audit_export_verification_detects_tampering(
    client: AsyncClient, users
) -> None:
    fiscal = await login(client, "fiscal", users["fiscal"]["password"])
    await create_sample(
        client,
        fiscal["access_token"],
        users["fiscal"]["password"],
        serial="SN-EXP3",
        lot="L-EXP3",
    )
    auditor = await login(client, "auditor", users["auditor"]["password"])
    exported = await client.post(
        f"{API}/audit/export",
        headers=auth(auditor["access_token"]),
        json={"format": "csv"},
    )
    assert exported.status_code == 200, exported.text

    # 1. Alterar o dado canônico sem atualizar o manifesto.
    with zipfile.ZipFile(io.BytesIO(exported.content)) as archive:
        data_bytes = archive.read("events.jsonl")
    assert b'"action":"LOGIN"' in data_bytes
    tampered_data = data_bytes.replace(b'"action":"LOGIN"', b'"action":"DELETE"', 1)
    data_bundle = _rewrite_zip(exported.content, {"events.jsonl": tampered_data})
    data_report = await client.post(
        f"{API}/audit/export/verify",
        headers=auth(auditor["access_token"]),
        files={"file": ("adulterado.zip", data_bundle, "application/zip")},
    )
    assert data_report.status_code == 200
    assert data_report.json()["ok"] is False
    assert data_report.json()["data_hash_ok"] is False
    assert any(
        issue["type"] == "DATA_HASH_MISMATCH"
        for issue in data_report.json()["issues"]
    )

    # 2. Alterar o manifesto sem recalcular o hash.
    with zipfile.ZipFile(io.BytesIO(exported.content)) as archive:
        manifest = json.loads(archive.read("manifest.json"))
    manifest["record_count"] += 1
    tampered_manifest = (
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    manifest_bundle = _rewrite_zip(
        exported.content, {"manifest.json": tampered_manifest}
    )
    manifest_report = await client.post(
        f"{API}/audit/export/verify",
        headers=auth(auditor["access_token"]),
        files={"file": ("manifesto.zip", manifest_bundle, "application/zip")},
    )
    assert manifest_report.status_code == 200
    assert manifest_report.json()["ok"] is False
    assert manifest_report.json()["manifest_hash_ok"] is False

    # 3. Adulterar um registro e recalcular toda a assinatura do arquivo:
    #    a cadeia interna ainda denuncia o elo quebrado.
    manifest, records = _bundle_entries(exported.content)
    key = settings.AUDIT_HMAC_KEY.get_secret_value()
    target = records[0]
    assert len(records) > 1
    target["payload"] = {**target["payload"], "reason": "CONTEÚDO ADULTERADO"}
    target["hash"] = sha256_hex(
        f"{target['sequence']}:{target['prev_hash']}:"
        f"{canonical_json(target['payload'])}"
    )
    target["hmac"] = hmac_sha256(key, target["hash"])
    new_data = (
        "".join(canonical_json(record) + "\n" for record in records)
    ).encode("utf-8")
    manifest["data_sha256"] = sha256_hex(new_data)
    manifest["data_hmac"] = hmac_sha256(key, manifest["data_sha256"])
    manifest["files"] = [
        entry
        if entry["name"] != "events.jsonl"
        else {
            **entry,
            "sha256": manifest["data_sha256"],
            "size": len(new_data),
        }
        for entry in manifest["files"]
    ]
    core = {
        field: value
        for field, value in manifest.items()
        if field not in {"manifest_hash", "hmac"}
    }
    manifest["manifest_hash"] = sha256_hex(canonical_json(core))
    manifest["hmac"] = hmac_sha256(key, manifest["manifest_hash"])
    resigned_manifest = (
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    chain_bundle = _rewrite_zip(
        exported.content,
        {"manifest.json": resigned_manifest, "events.jsonl": new_data},
    )
    chain_report = await client.post(
        f"{API}/audit/export/verify",
        headers=auth(auditor["access_token"]),
        files={"file": ("cadeia.zip", chain_bundle, "application/zip")},
    )
    assert chain_report.status_code == 200
    body = chain_report.json()
    assert body["ok"] is False
    assert body["manifest_hash_ok"] is True
    assert body["data_hash_ok"] is True
    assert body["chain_ok"] is False
    assert any(issue["type"] == "PREV_HASH_MISMATCH" for issue in body["issues"])
