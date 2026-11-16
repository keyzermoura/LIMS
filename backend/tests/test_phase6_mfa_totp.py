"""Testes automatizados do Horizonte 1 — Sprint 6.2: MFA TOTP e Assinatura Reforçada (21 CFR Part 11)."""

from __future__ import annotations

import base64
from typing import Any
from uuid import UUID, uuid4

import pyotp
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

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
async def test_mfa_setup_generates_valid_totp_and_qr(
    client: AsyncClient,
    users: dict[str, dict[str, Any]],
) -> None:
    """Valida endpoint /auth/mfa/setup gerando secret base32, URI otpauth e QR code PNG."""
    login_data = await login(client, "admin", "Admin@Lims2026")
    token = login_data["access_token"]

    resp = await client.post(f"{API}/auth/mfa/setup", headers=auth(token))
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert "secret" in data
    assert len(data["secret"]) >= 16
    assert "otpauth_url" in data
    assert "otpauth://totp/" in data["otpauth_url"]
    assert "admin" in data["otpauth_url"]
    assert "secret=" in data["otpauth_url"]
    assert "qr_code_base64" in data

    # Validar que o base64 é de fato um arquivo PNG válido (header PNG: \x89PNG)
    png_bytes = base64.b64decode(data["qr_code_base64"])
    assert png_bytes[:4] == b"\x89PNG"


@pytest.mark.asyncio
async def test_mfa_enable_and_disable_lifecycle(
    client: AsyncClient,
    users: dict[str, dict[str, Any]],
    db_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Valida o ciclo de ativação com senha e token TOTP, e desativação de MFA."""
    login_data = await login(client, "admin", "Admin@Lims2026")
    token = login_data["access_token"]
    user_id = UUID(login_data["user"]["id"])

    # 1. Setup para obter segredo
    setup_resp = await client.post(f"{API}/auth/mfa/setup", headers=auth(token))
    secret = setup_resp.json()["secret"]

    # 2. Tentar ativar com senha incorreta
    totp = pyotp.TOTP(secret)
    valid_code = totp.now()

    bad_pwd_resp = await client.post(
        f"{API}/auth/mfa/enable",
        headers=auth(token),
        json={"secret": secret, "code": valid_code, "password": "SenhaErrada@999"},
    )
    assert bad_pwd_resp.status_code == 401

    # 3. Tentar ativar com código inválido
    bad_code_resp = await client.post(
        f"{API}/auth/mfa/enable",
        headers=auth(token),
        json={"secret": secret, "code": "000000", "password": "Admin@Lims2026"},
    )
    assert bad_code_resp.status_code == 400

    # 4. Ativar com sucesso
    enable_resp = await client.post(
        f"{API}/auth/mfa/enable",
        headers=auth(token),
        json={"secret": secret, "code": valid_code, "password": "Admin@Lims2026"},
    )
    assert enable_resp.status_code == 200
    enable_data = enable_resp.json()
    recovery_codes = enable_data["recovery_codes"]
    assert len(recovery_codes) == 8
    for c in recovery_codes:
        assert len(c) == 9  # Formato XXXX-XXXX

    # Checar no banco
    async with db_factory() as db:
        user = await db.get(User, user_id)
        assert user is not None
        assert user.mfa_enabled is True
        assert user.mfa_secret == secret
        assert len(user.mfa_recovery_codes or []) == 8

    # 5. Desativar MFA com senha e código TOTP
    disable_code = totp.now()
    disable_resp = await client.post(
        f"{API}/auth/mfa/disable",
        headers=auth(token),
        json={"password": "Admin@Lims2026", "code": disable_code},
    )
    assert disable_resp.status_code == 204

    # Checar no banco que desativou
    async with db_factory() as db:
        user = await db.get(User, user_id)
        assert user is not None
        assert user.mfa_enabled is False
        assert user.mfa_secret is None
        assert user.mfa_recovery_codes is None


@pytest.mark.asyncio
async def test_esignature_enforces_mfa_when_enabled(
    client: AsyncClient,
    users: dict[str, dict[str, Any]],
    db_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Garante que a assinatura eletrônica (21 CFR Part 11) exija TOTP ou Recovery Code se MFA ativo."""
    login_data = await login(client, "admin", "Admin@Lims2026")
    token = login_data["access_token"]
    user_id = UUID(login_data["user"]["id"])

    # 1. Ativar MFA no usuário
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    enable_resp = await client.post(
        f"{API}/auth/mfa/enable",
        headers=auth(token),
        json={"secret": secret, "code": totp.now(), "password": "Admin@Lims2026"},
    )
    assert enable_resp.status_code == 200
    recovery_codes = enable_resp.json()["recovery_codes"]

    sign_payload = {
        "password": "Admin@Lims2026",
        "meaning": "RESPONSABILIDADE_TECNICA",
        "reason": "Assinatura técnica pericial do laudo toxicológico oficial.",
        "entity_type": "official_reports",
        "entity_id": str(uuid4()),
        "action": "CREATE",
    }

    # 2. Tentativa de assinar sem fornecer totp_code deve ser rejeitada (401)
    no_mfa_resp = await client.post(f"{API}/auth/sign", headers=auth(token), json=sign_payload)
    assert no_mfa_resp.status_code == 401
    assert "MFA" in no_mfa_resp.json()["detail"]

    # 3. Tentativa de assinar com totp_code incorreto deve ser rejeitada (401)
    bad_mfa_payload = {**sign_payload, "totp_code": "123456"}
    bad_mfa_resp = await client.post(f"{API}/auth/sign", headers=auth(token), json=bad_mfa_payload)
    assert bad_mfa_resp.status_code == 401

    # 4. Assinatura com totp_code correto (6 dígitos) tem sucesso
    good_mfa_payload = {**sign_payload, "totp_code": totp.now()}
    good_mfa_resp = await client.post(f"{API}/auth/sign", headers=auth(token), json=good_mfa_payload)
    assert good_mfa_resp.status_code == 200
    manifest = good_mfa_resp.json()["manifest"]
    assert manifest["method"] == "PASSWORD+MFA_TOTP"
    assert manifest["mfa_verified"] is True

    # 5. Assinatura utilizando código de recuperação descartável
    backup_code = recovery_codes[0]
    recovery_sign_payload = {
        **sign_payload,
        "entity_id": str(uuid4()),
        "totp_code": backup_code,
    }
    recovery_resp = await client.post(
        f"{API}/auth/sign", headers=auth(token), json=recovery_sign_payload
    )
    assert recovery_resp.status_code == 200

    # 6. Tentar reusar o mesmo código de recuperação deve falhar (descartável)
    reuse_resp = await client.post(
        f"{API}/auth/sign", headers=auth(token), json=recovery_sign_payload
    )
    assert reuse_resp.status_code == 401

    # 7. Verificar que a quantidade de recovery codes no banco caiu de 8 para 7
    async with db_factory() as db:
        user = await db.get(User, user_id)
        assert user is not None
        assert len(user.mfa_recovery_codes or []) == 7
