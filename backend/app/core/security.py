"""Primitivas criptográficas: hash de senha, JWT e tokens de assinatura.

Decisões relevantes para 21 CFR Part 11 / RDC 665:
  * Senhas com Argon2id (memória 64 MiB, 3 iterações) e rehash automático.
  * JWT de acesso curto (30 min) + refresh rotativo de uso único.
  * Token de assinatura eletrônica é de uso único, curto (5 min), vinculado
    ao usuário, à entidade, à ação e ao significado da assinatura.
"""

from __future__ import annotations

import contextlib
import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from uuid import UUID, uuid4

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from app.core.config import settings

# Parâmetros OWASP para Argon2id.
_password_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=2,
    hash_len=32,
    salt_len=16,
)

TokenType = Literal["access", "refresh", "esign", "sample_qr"]


class TokenError(Exception):
    """Token ausente, expirado, adulterado ou de tipo inesperado."""


# --------------------------------------------------------------------------
# Senhas
# --------------------------------------------------------------------------
def hash_password(plain_password: str) -> str:
    _validate_password_policy(plain_password)
    return _password_hasher.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return _password_hasher.verify(password_hash, plain_password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


_DUMMY_HASH = _password_hasher.hash(secrets.token_urlsafe(32))


def burn_password_check(plain_password: str) -> None:
    """Verificação descartável: equaliza o tempo de resposta quando o
    usuário não existe (mitiga enumeração de contas)."""
    with contextlib.suppress(VerifyMismatchError, VerificationError, InvalidHashError):
        _password_hasher.verify(_DUMMY_HASH, plain_password)


def password_needs_rehash(password_hash: str) -> bool:
    try:
        return _password_hasher.check_needs_rehash(password_hash)
    except InvalidHashError:
        return True


def _validate_password_policy(password: str) -> None:
    from app.core.errors import ValidationDomainError

    if len(password) < settings.PASSWORD_MIN_LENGTH:
        raise ValidationDomainError(
            f"A senha deve ter ao menos {settings.PASSWORD_MIN_LENGTH} caracteres."
        )
    classes = [
        any(c.islower() for c in password),
        any(c.isupper() for c in password),
        any(c.isdigit() for c in password),
        any(not c.isalnum() for c in password),
    ]
    if sum(classes) < 3:
        raise ValidationDomainError(
            "A senha deve combinar ao menos 3 classes: minúsculas, maiúsculas, "
            "dígitos e caracteres especiais."
        )


# --------------------------------------------------------------------------
# JWT
# --------------------------------------------------------------------------
def _encode(claims: dict[str, Any], ttl: timedelta, token_type: TokenType) -> str:
    now = datetime.now(UTC)
    payload = {
        **claims,
        "typ": token_type,
        "iat": now,
        "nbf": now,
        "exp": now + ttl,
        "jti": claims.get("jti") or str(uuid4()),
    }
    return jwt.encode(
        payload,
        settings.JWT_SECRET.get_secret_value(),
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_token(token: str, *, expected_type: TokenType) -> dict[str, Any]:
    try:
        claims = jwt.decode(
            token,
            settings.JWT_SECRET.get_secret_value(),
            algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["exp", "iat", "sub", "typ", "jti"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise TokenError("Token expirado.") from exc
    except jwt.InvalidTokenError as exc:
        raise TokenError("Token inválido.") from exc

    if claims.get("typ") != expected_type:
        raise TokenError("Tipo de token inesperado.")
    return claims


def create_access_token(user_id: UUID, role: str, password_version: int) -> str:
    """`password_version` invalida sessões quando a senha é trocada."""
    return _encode(
        {"sub": str(user_id), "role": role, "pwdv": password_version},
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "access",
    )


def create_refresh_token(user_id: UUID, jti: str | None = None) -> str:
    claims: dict[str, Any] = {"sub": str(user_id)}
    if jti:
        claims["jti"] = jti  # preservado para rotação determinística
    return _encode(claims, timedelta(hours=settings.REFRESH_TOKEN_EXPIRE_HOURS), "refresh")


def create_esign_token(
    *,
    signature_id: UUID,
    user_id: UUID,
    entity_type: str,
    entity_id: str,
    action: str,
    meaning: str,
    jti: str,
) -> str:
    return _encode(
        {
            "sid": str(signature_id),
            "sub": str(user_id),
            "ent": entity_type,
            "eid": entity_id,
            "act": action,
            "mean": meaning,
            "jti": jti,
        },
        timedelta(seconds=settings.ESIGNATURE_TTL_SECONDS),
        "esign",
    )


def decode_esign_token(token: str) -> dict[str, Any]:
    return decode_token(token, expected_type="esign")


# --------------------------------------------------------------------------
# QR Code lógico (assinado, não apenas um UUID adivinhável)
# --------------------------------------------------------------------------
def sign_qr_payload(sample_id: UUID, accession_number: str) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "typ": "sample_qr",
            "sub": str(sample_id),
            "acc": accession_number,
            "iat": now,
            "jti": secrets.token_urlsafe(8),
        },
        settings.QR_SIGNING_KEY.get_secret_value(),
        algorithm="HS256",
    )


def verify_qr_payload(token: str) -> dict[str, Any]:
    try:
        claims = jwt.decode(
            token,
            settings.QR_SIGNING_KEY.get_secret_value(),
            algorithms=["HS256"],
            options={"require": ["sub", "acc", "typ"], "verify_exp": False},
        )
    except jwt.InvalidTokenError as exc:
        raise TokenError("QR Code inválido ou adulterado.") from exc
    if claims.get("typ") != "sample_qr":
        raise TokenError("QR Code não pertence a uma amostra.")
    return claims


def sha256_hex(value: str | bytes) -> str:
    data = value.encode("utf-8") if isinstance(value, str) else value
    return hashlib.sha256(data).hexdigest()


def hmac_sha256(key: str, value: str) -> str:
    return hmac.new(key.encode("utf-8"), value.encode("utf-8"), hashlib.sha256).hexdigest()


def constant_time_equals(left: str, right: str) -> bool:
    return hmac.compare_digest(left.encode("utf-8"), right.encode("utf-8"))
