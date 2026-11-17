"""Testes automatizados do Horizonte 3 — Sprint 8.1: Contas de Serviço, OAuth2 M2M e Idempotência (H3.1).

Conforme ESPECIFICACAO_CAMADA_INTEGRACAO_LIMS.md §1-3 e ALCOA+.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.security import decode_token
from app.models.enums import EquipmentCalibrationStatus
from app.models.equipment import LaboratoryEquipment
from app.models.user import User

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
async def test_service_client_creation_and_m2m_token_issuance(
    db_factory: async_sessionmaker[AsyncSession],
    client: AsyncClient,
    users: dict[str, dict[str, Any]],
) -> None:
    """Valida cadastro de cliente de serviço por admin e obtenção de token OAuth2 client credentials."""
    login_admin = await login(client, "admin", "Admin@Lims2026")
    admin_headers = auth(login_admin["access_token"])

    # 1. Admin cria cliente de serviço M2M
    create_payload = {
        "name": "Agente HPLC Laboratório Central",
        "scopes": ["instrument:write", "samples:read"],
        "expires_in_days": 60,
    }
    res_create = await client.post(
        f"{API}/service-clients",
        json=create_payload,
        headers=admin_headers,
    )
    assert res_create.status_code == 201, res_create.text
    client_data = res_create.json()
    assert client_data["client_id"].startswith("svc_")
    assert "client_secret" in client_data
    client_id = client_data["client_id"]
    client_secret = client_data["client_secret"]
    assert "instrument:write" in client_data["scopes"]

    # 2. Cliente M2M obtém token via OAuth2 Client Credentials (JSON)
    token_req = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "instrument:write",
    }
    res_token = await client.post(f"{API}/auth/service-token", json=token_req)
    assert res_token.status_code == 200, res_token.text
    token_data = res_token.json()
    assert token_data["token_type"] == "bearer"
    assert token_data["expires_in"] == 900
    assert "instrument:write" in token_data["scope"]
    svc_token = token_data["access_token"]

    # Valida claims do token
    claims = decode_token(svc_token, expected_type="service")
    assert claims["typ"] == "service"
    assert claims["sub"] == f"client:{client_id}"
    assert "instrument:write" in claims["scp"]

    # 3. Cliente M2M obtém token via Form urlencoded (RFC 6749)
    res_form = await client.post(
        f"{API}/auth/service-token",
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
    )
    assert res_form.status_code == 200, res_form.text
    assert "access_token" in res_form.json()


@pytest.mark.asyncio
async def test_service_client_interactive_login_forbidden(
    db_factory: async_sessionmaker[AsyncSession],
    client: AsyncClient,
    users: dict[str, dict[str, Any]],
) -> None:
    """Garante que contas de serviço não podem realizar login interativo em /auth/login."""
    login_admin = await login(client, "admin", "Admin@Lims2026")
    admin_headers = auth(login_admin["access_token"])

    # Cria cliente de serviço
    res_create = await client.post(
        f"{API}/service-clients",
        json={"name": "Agente GC-MS", "scopes": ["instrument:write"]},
        headers=admin_headers,
    )
    assert res_create.status_code == 201
    created = res_create.json()

    # Busca username do usuário de serviço
    async with db_factory() as db:
        svc_user = await db.get(User, UUID(created["service_user_id"]))
        assert svc_user is not None
        svc_username = svc_user.username

    # Tenta login interativo
    res_login = await client.post(
        f"{API}/auth/login",
        data={"username": svc_username, "password": created["client_secret"]},
    )
    assert res_login.status_code == 403
    assert "Contas de serviço não podem realizar login interativo" in res_login.text


@pytest.mark.asyncio
async def test_service_client_secret_rotation(
    db_factory: async_sessionmaker[AsyncSession],
    client: AsyncClient,
    users: dict[str, dict[str, Any]],
) -> None:
    """Valida rotação de segredo com janela de sobreposição para não interromper agentes em campo."""
    login_admin = await login(client, "admin", "Admin@Lims2026")
    admin_headers = auth(login_admin["access_token"])

    # Cria cliente
    res_create = await client.post(
        f"{API}/service-clients",
        json={"name": "Balança Analítica", "scopes": ["instrument:write"]},
        headers=admin_headers,
    )
    assert res_create.status_code == 201
    old_data = res_create.json()
    client_id = old_data["client_id"]
    old_secret = old_data["client_secret"]

    # Rotaciona segredo
    res_rotate = await client.post(
        f"{API}/service-clients/{client_id}/rotate",
        headers=admin_headers,
    )
    assert res_rotate.status_code == 200, res_rotate.text
    new_data = res_rotate.json()
    new_secret = new_data["new_client_secret"]
    assert new_secret != old_secret

    # 1. Novo segredo deve autenticar com sucesso
    res_new_auth = await client.post(
        f"{API}/auth/service-token",
        json={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": new_secret,
        },
    )
    assert res_new_auth.status_code == 200, res_new_auth.text

    # 2. Segredo antigo continua válido durante a janela de transição (sobreposição)
    res_old_auth = await client.post(
        f"{API}/auth/service-token",
        json={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": old_secret,
        },
    )
    assert res_old_auth.status_code == 200, res_old_auth.text

    # 3. Segredo inválido é sumariamente rejeitado
    res_bad = await client.post(
        f"{API}/auth/service-token",
        json={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": "segredo-falso-1234567890",
        },
    )
    assert res_bad.status_code == 401


@pytest.mark.asyncio
async def test_service_client_revocation_blocks_access(
    db_factory: async_sessionmaker[AsyncSession],
    client: AsyncClient,
    users: dict[str, dict[str, Any]],
) -> None:
    """Valida revogação imediata de cliente de serviço e invalidação no consumo de APIs."""
    login_admin = await login(client, "admin", "Admin@Lims2026")
    admin_headers = auth(login_admin["access_token"])

    # Cria cliente e obtém token
    res_create = await client.post(
        f"{API}/service-clients",
        json={"name": "Cliente Temporário", "scopes": ["samples:read"]},
        headers=admin_headers,
    )
    assert res_create.status_code == 201
    c_data = res_create.json()
    client_id = c_data["client_id"]

    res_tok = await client.post(
        f"{API}/auth/service-token",
        json={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": c_data["client_secret"],
        },
    )
    assert res_tok.status_code == 200
    token = res_tok.json()["access_token"]
    svc_headers = auth(token)

    # Chamada com cliente ativo tem sucesso
    res_samples = await client.get(f"{API}/samples", headers=svc_headers)
    assert res_samples.status_code == 200

    # Revoga o cliente
    res_del = await client.delete(f"{API}/service-clients/{client_id}", headers=admin_headers)
    assert res_del.status_code == 200
    assert res_del.json()["is_active"] is False

    # 1. Nova solicitação de token é rejeitada
    res_tok_after = await client.post(
        f"{API}/auth/service-token",
        json={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": c_data["client_secret"],
        },
    )
    assert res_tok_after.status_code == 401

    # 2. Token existente é rejeitado imediatamente em get_current_user
    res_samples_after = await client.get(f"{API}/samples", headers=svc_headers)
    assert res_samples_after.status_code == 401
    assert "Cliente de serviço inexistente ou inativo" in res_samples_after.text


@pytest.mark.asyncio
async def test_idempotent_instrument_upload_and_replay(
    db_factory: async_sessionmaker[AsyncSession],
    client: AsyncClient,
    users: dict[str, dict[str, Any]],
) -> None:
    """Valida que envios com Idempotency-Key retornam resposta idêntica (replay) e não duplicam registros."""
    login_admin = await login(client, "admin", "Admin@Lims2026")
    admin_headers = auth(login_admin["access_token"])

    # Cria equipamento calibrado
    async with db_factory() as db:
        equip = LaboratoryEquipment(
            id=uuid4(),
            code=f"BAL-IDEMP-{uuid4().hex[:4].upper()}",
            name="Balança Mettler Toledo XPE205",
            manufacturer="Mettler Toledo",
            model="XPE205",
            serial_number=f"MT-{uuid4().hex[:6]}",
            calibration_status=EquipmentCalibrationStatus.CALIBRADO,
            is_active=True,
        )
        db.add(equip)
        await db.commit()
        equip_id = str(equip.id)

    idemp_key = f"key-idemp-{uuid4().hex}"
    raw_payload = {
        "equipment_id": equip_id,
        "file_name": "balanca_lote_01.txt",
        "file_format": "BALANCA_ASCII",
        "raw_content": "Net: 12.3456 g\nTare: 1.0000 g\nGross: 13.3456 g\n",
    }

    # Primeiro envio com Idempotency-Key
    headers_1 = {**admin_headers, "Idempotency-Key": idemp_key}
    res_1 = await client.post(
        f"{API}/instrument-data/upload-raw", json=raw_payload, headers=headers_1
    )
    assert res_1.status_code == 201, res_1.text
    body_1 = res_1.json()
    record_id = body_1["id"]

    # Segundo envio com a MESMA Idempotency-Key e MESMO payload
    res_2 = await client.post(
        f"{API}/instrument-data/upload-raw", json=raw_payload, headers=headers_1
    )
    assert res_2.status_code == 201, res_2.text
    body_2 = res_2.json()
    assert body_2["id"] == record_id, "O replay deve retornar o mesmo registro sem duplicar"

    # Terceiro envio com a MESMA Idempotency-Key porém payload DIFERENTE (deve conflitar 409)
    altered_payload = {**raw_payload, "raw_content": "Net: 99.9999 g\n"}
    res_3 = await client.post(
        f"{API}/instrument-data/upload-raw", json=altered_payload, headers=headers_1
    )
    assert res_3.status_code == 409, res_3.text
    assert "payload divergente" in res_3.text


@pytest.mark.asyncio
async def test_instrument_deduplication_via_unique_sha256(
    db_factory: async_sessionmaker[AsyncSession],
    client: AsyncClient,
    users: dict[str, dict[str, Any]],
) -> None:
    """Valida rejeição de arquivo duplicado para o mesmo equipamento mesmo sem Idempotency-Key (ALCOA+)."""
    login_admin = await login(client, "admin", "Admin@Lims2026")
    admin_headers = auth(login_admin["access_token"])

    # Cria equipamento calibrado
    async with db_factory() as db:
        equip = LaboratoryEquipment(
            id=uuid4(),
            code=f"BAL-DEDUP-{uuid4().hex[:4].upper()}",
            name="Balança Sartorius Quintix",
            manufacturer="Sartorius",
            model="Quintix",
            serial_number=f"SAR-{uuid4().hex[:6]}",
            calibration_status=EquipmentCalibrationStatus.CALIBRADO,
            is_active=True,
        )
        db.add(equip)
        await db.commit()
        equip_id = str(equip.id)

    raw_payload = {
        "equipment_id": equip_id,
        "file_name": "leitura_unica.txt",
        "file_format": "BALANCA_ASCII",
        "raw_content": "S S 25.1234 g\n",
    }

    # Primeiro envio sem chave de idempotência
    res_1 = await client.post(
        f"{API}/instrument-data/upload-raw", json=raw_payload, headers=admin_headers
    )
    assert res_1.status_code == 201, res_1.text

    # Segundo envio idêntico sem chave de idempotência -> Conflito 409 por deduplicação metrológica
    res_2 = await client.post(
        f"{API}/instrument-data/upload-raw", json=raw_payload, headers=admin_headers
    )
    assert res_2.status_code == 409, res_2.text
    assert "Arquivo já importado anteriormente" in res_2.text
