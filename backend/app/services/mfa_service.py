"""Serviço de Autenticação Multifator (MFA TOTP) e Códigos de Recuperação.

Atende a requisitos de segurança reforçada e integridade 21 CFR Part 11 / ISO 27001:
- Geração determinística de segredos base32 (RFC 6238).
- QR Code compatível com Google Authenticator, Microsoft Authenticator e 1Password.
- 8 códigos de recuperação de uso único (armazenados em hash SHA-256).
- Auditoria append-only de ativação e revogação.
"""

from __future__ import annotations

import base64
import hashlib
import io
import secrets

import pyotp
import qrcode
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.core.context import RequestContext
from app.core.security import verify_password
from app.models.enums import AuditAction, AuditEntity
from app.models.user import User
from app.services import audit_service


def generate_totp_secret() -> str:
    """Gera um segredo Base32 seguro de 160 bits para TOTP."""
    return pyotp.random_base32()


def generate_qr_code_base64(otpauth_url: str) -> str:
    """Gera imagem PNG codificada em Base64 do QR Code da URI otpauth."""
    qr = qrcode.QRCode(
        version=1,
        box_size=8,
        border=2,
    )
    qr.add_data(otpauth_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def setup_mfa(user: User) -> tuple[str, str, str]:
    """Inicia o processo de pareamento MFA para o usuário autenticado.

    Retorna: (secret, otpauth_url, qr_code_base64)
    """
    secret = generate_totp_secret()
    totp = pyotp.TOTP(secret)
    otpauth_url = totp.provisioning_uri(
        name=user.email,
        issuer_name="LIMS SEFI/FUNED",
    )
    qr_code_base64 = generate_qr_code_base64(otpauth_url)
    return secret, otpauth_url, qr_code_base64


def verify_totp_code(secret: str, code: str) -> bool:
    """Verifica código TOTP com tolerância de janela de ±30 segundos."""
    if not secret or not code:
        return False
    normalized = code.strip().replace(" ", "").replace("-", "")
    totp = pyotp.TOTP(secret)
    return bool(totp.verify(normalized, valid_window=1))


def hash_recovery_code(code: str) -> str:
    """Gera hash SHA-256 normalizado para armazenamento do código de recuperação."""
    normalized = code.strip().upper().replace(" ", "")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def generate_recovery_codes(n: int = 8) -> tuple[list[str], list[str]]:
    """Gera N códigos de recuperação legíveis (XXXX-XXXX) e seus respectivos hashes."""
    plain_codes: list[str] = []
    hashes: list[str] = []
    for _ in range(n):
        token = secrets.token_hex(4).upper()
        formatted = f"{token[:4]}-{token[4:]}"
        plain_codes.append(formatted)
        hashes.append(hash_recovery_code(formatted))
    return plain_codes, hashes


def verify_and_consume_recovery_code(user: User, code: str) -> bool:
    """Valida e invalida (uso único) um código de recuperação descartável."""
    if not user.mfa_recovery_codes or not code:
        return False
    target_hash = hash_recovery_code(code)
    existing_hashes = list(user.mfa_recovery_codes)
    if target_hash in existing_hashes:
        existing_hashes.remove(target_hash)
        user.mfa_recovery_codes = existing_hashes
        return True
    return False


def verify_user_mfa(user: User, code_or_recovery: str | None) -> bool:
    """Valida segundo fator de autenticação (TOTP ou recovery code).

    Se o usuário não tem MFA ativado, retorna True.
    Se o MFA está ativo, valida código de 6 dígitos ou recovery code.
    """
    if not user.mfa_enabled:
        return True
    if not code_or_recovery:
        return False

    # 1. Tentar validação via TOTP
    if user.mfa_secret and verify_totp_code(user.mfa_secret, code_or_recovery):
        return True

    # 2. Tentar validação via Recovery Code (descartável)
    return bool(verify_and_consume_recovery_code(user, code_or_recovery))


async def enable_mfa(
    db: AsyncSession,
    *,
    user: User,
    secret: str,
    code: str,
    password: str,
    context: RequestContext,
) -> list[str]:
    """Ativa formalmente o MFA para o usuário após validar a senha e o primeiro token TOTP.

    Retorna a lista de 8 códigos de recuperação para exibição única ao usuário.
    """
    valid_pwd = await run_in_threadpool(verify_password, password, user.hashed_password)
    if not valid_pwd:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Senha incorreta. Não foi possível ativar o MFA.",
        )

    if not verify_totp_code(secret, code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código de autenticação TOTP inválido ou expirado.",
        )

    plain_recovery, recovery_hashes = generate_recovery_codes(8)

    old_snapshot = audit_service.snapshot(user)
    user.mfa_enabled = True
    user.mfa_secret = secret
    user.mfa_recovery_codes = recovery_hashes
    await db.flush()

    await audit_service.append(
        db,
        action=AuditAction.UPDATE,
        entity_type=AuditEntity.USER.value,
        entity_id=user.id,
        old_value=old_snapshot,
        new_value=audit_service.snapshot(user),
        reason="Ativação de autenticação multifator (MFA TOTP) e geração de códigos de recuperação.",
        context=context,
    )
    await db.commit()

    return plain_recovery


async def disable_mfa(
    db: AsyncSession,
    *,
    user: User,
    password: str,
    code: str,
    context: RequestContext,
) -> None:
    """Desativa o MFA do usuário mediante conferência da senha atual e token/recovery code."""
    valid_pwd = await run_in_threadpool(verify_password, password, user.hashed_password)
    if not valid_pwd:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Senha incorreta. Não foi possível desativar o MFA.",
        )

    if not verify_user_mfa(user, code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código TOTP ou de recuperação inválido.",
        )

    old_snapshot = audit_service.snapshot(user)
    user.mfa_enabled = False
    user.mfa_secret = None
    user.mfa_recovery_codes = None
    await db.flush()

    await audit_service.append(
        db,
        action=AuditAction.UPDATE,
        entity_type=AuditEntity.USER.value,
        entity_id=user.id,
        old_value=old_snapshot,
        new_value=audit_service.snapshot(user),
        reason="Desativação voluntária de autenticação multifator (MFA TOTP).",
        context=context,
    )
    await db.commit()
