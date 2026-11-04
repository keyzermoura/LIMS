"""Autenticação, sessões e gestão de usuários."""

from __future__ import annotations

import logging
import secrets
from datetime import UTC, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.core.context import RequestContext
from app.core.errors import ConflictError, ForbiddenError, NotFoundError
from app.core.rbac import ROLE_PERMISSIONS
from app.core.security import (
    TokenError,
    burn_password_check,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    sha256_hex,
    verify_password,
)
from app.models.base import utcnow
from app.models.electronic_signature import ElectronicSignature
from app.models.enums import AuditAction, AuditEntity, UserRole
from app.models.user import RefreshToken, User
from app.services import audit_service, signature_service

logger = logging.getLogger(__name__)

INVALID_CREDENTIALS = "Usuário ou senha inválidos."


async def login(
    db: AsyncSession,
    *,
    username: str,
    password: str,
    context: RequestContext,
) -> tuple[User, str, str]:
    # `FOR UPDATE` serializa tentativas concorrentes do mesmo usuário para que
    # o contador de falhas e o bloqueio não sejam perdidos (lost update).
    user = await db.scalar(
        select(User)
        .where(User.username == username.strip().lower())
        .with_for_update()
    )

    if user is None:
        # Consome tempo equivalente ao Argon2 para não revelar existência da conta.
        await run_in_threadpool(burn_password_check, password)
        await _audit_failed_login(db, None, username, "Usuário inexistente.", context)
        raise _invalid_credentials()

    if user.is_locked:
        await _audit_failed_login(
            db, user, username, "Conta temporariamente bloqueada por tentativas.", context
        )
        raise ForbiddenError(
            "Conta bloqueada temporariamente após tentativas inválidas. "
            f"Tente novamente em até {settings.LOGIN_LOCKOUT_MINUTES} minutos."
        )

    valid = await run_in_threadpool(verify_password, password, user.hashed_password)
    if not valid:
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
            user.locked_until = utcnow() + timedelta(
                minutes=settings.LOGIN_LOCKOUT_MINUTES
            )
            user.failed_login_attempts = 0
            reason = "Limite de tentativas atingido — conta bloqueada."
        else:
            reason = "Senha inválida."
        await _audit_failed_login(db, user, username, reason, context)
        raise _invalid_credentials()

    if not user.is_active:
        await _audit_failed_login(db, user, username, "Usuário inativo.", context)
        raise ForbiddenError("Usuário inativo. Contate o administrador.")

    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = utcnow()

    access_token, refresh_token = await _issue_pair(db, user, context)
    await audit_service.append(
        db,
        action=AuditAction.LOGIN,
        entity_type=AuditEntity.USER.value,
        entity_id=user.id,
        actor=user,
        new_value={"username": user.username, "role": user.role.value},
        reason="Autenticação bem-sucedida.",
        context=context,
    )
    await db.commit()
    return user, access_token, refresh_token


async def refresh(
    db: AsyncSession, *, refresh_token: str, context: RequestContext
) -> tuple[User, str, str]:
    try:
        claims = decode_token(refresh_token, expected_type="refresh")
    except TokenError as exc:
        raise ForbiddenError(f"Sessão inválida: {exc}") from exc

    jti = claims["jti"]
    stored = await db.scalar(
        select(RefreshToken).where(RefreshToken.jti == jti).with_for_update()
    )
    if stored is None:
        raise ForbiddenError("Sessão não reconhecida. Autentique-se novamente.")

    user = await db.get(User, stored.user_id)

    if stored.revoked_at is not None:
        # Possível reutilização de token roubado: invalida todas as sessões,
        # inclusive os access tokens já emitidos (via `token_version`).
        await _revoke_all(db, stored.user_id, "REUSE_DETECTED")
        if user is not None:
            user.token_version += 1
        await audit_service.append(
            db,
            action=AuditAction.REFRESH,
            entity_type=AuditEntity.USER.value,
            entity_id=stored.user_id,
            actor_username="SYSTEM",
            new_value={"event": "REFRESH_TOKEN_REUSE", "jti": jti},
            reason="Refresh token reutilizado — todas as sessões foram revogadas.",
            context=context,
        )
        await db.commit()
        raise ForbiddenError(
            "Sessão revogada por suspeita de reutilização. Autentique-se novamente."
        )

    expires_at = stored.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at <= utcnow():
        raise ForbiddenError("Sessão expirada. Autentique-se novamente.")

    if user is None or not user.is_active or user.is_locked:
        raise ForbiddenError("Usuário indisponível. Autentique-se novamente.")

    new_jti = secrets.token_urlsafe(24)
    stored.revoked_at = utcnow()
    stored.revoked_reason = "ROTATED"
    stored.replaced_by_jti = new_jti

    access = create_access_token(user.id, user.role.value, user.password_version)
    new_refresh = create_refresh_token(user.id, new_jti)
    db.add(
        RefreshToken(
            jti=new_jti,
            user_id=user.id,
            expires_at=utcnow()
            + timedelta(hours=settings.REFRESH_TOKEN_EXPIRE_HOURS),
            ip_address=context.ip_address,
            user_agent=context.user_agent,
        )
    )
    await audit_service.append(
        db,
        action=AuditAction.REFRESH,
        entity_type=AuditEntity.USER.value,
        entity_id=user.id,
        actor=user,
        new_value={"rotated_from": jti, "rotated_to": new_jti},
        reason="Rotação de sessão.",
        context=context,
    )
    await db.commit()
    return user, access, new_refresh


async def logout(
    db: AsyncSession, *, refresh_token: str, user: User, context: RequestContext
) -> None:
    try:
        claims = decode_token(refresh_token, expected_type="refresh")
        jti = claims["jti"]
    except TokenError:
        jti = None

    if jti:
        stored = await db.scalar(select(RefreshToken).where(RefreshToken.jti == jti))
        # Só o próprio dono da sessão pode revogá-la.
        if stored and stored.user_id == user.id and stored.revoked_at is None:
            stored.revoked_at = utcnow()
            stored.revoked_reason = "LOGOUT"

    await audit_service.append(
        db,
        action=AuditAction.LOGOUT,
        entity_type=AuditEntity.USER.value,
        entity_id=user.id,
        actor=user,
        reason="Encerramento de sessão.",
        context=context,
    )
    await db.commit()


async def change_password(
    db: AsyncSession,
    *,
    user: User,
    current_password: str,
    new_password: str,
    context: RequestContext,
) -> None:
    valid = await run_in_threadpool(verify_password, current_password, user.hashed_password)
    if not valid:
        await _audit_failed_login(
            db, user, user.username, "Senha atual incorreta na troca de senha.", context
        )
        raise ForbiddenError("Senha atual incorreta.")

    if new_password == current_password:
        raise ConflictError("A nova senha deve ser diferente da atual.")

    user.hashed_password = await run_in_threadpool(hash_password, new_password)
    user.password_changed_at = utcnow()
    user.token_version += 1  # invalida imediatamente todos os access tokens
    await _revoke_all(db, user.id, "PASSWORD_CHANGED")
    await audit_service.append(
        db,
        action=AuditAction.UPDATE,
        entity_type=AuditEntity.USER.value,
        entity_id=user.id,
        actor=user,
        new_value={"event": "PASSWORD_CHANGED"},
        reason="Troca de senha — sessões anteriores invalidadas.",
        context=context,
    )
    await db.commit()


async def create_user(
    db: AsyncSession,
    *,
    actor: User,
    user_id: UUID,
    username: str,
    email: str,
    full_name: str,
    role: UserRole,
    password: str,
    registration_number: str | None,
    signature: ElectronicSignature,
    context: RequestContext,
) -> User:
    username = username.strip().lower()
    email = email.strip().lower()

    exists = await db.scalar(
        select(func.count())
        .select_from(User)
        .where((User.username == username) | (User.email == email))
    )
    if exists:
        raise ConflictError("Username ou e-mail já cadastrado.")

    user = User(
        id=user_id,
        username=username,
        email=email,
        full_name=full_name.strip(),
        role=role,
        registration_number=registration_number,
        hashed_password=await run_in_threadpool(hash_password, password),
        password_changed_at=utcnow(),
    )
    db.add(user)
    await db.flush()

    await signature_service.bind_record(
        db, signature, {"user": audit_service.snapshot(user)}
    )

    await audit_service.append(
        db,
        action=AuditAction.CREATE,
        entity_type=AuditEntity.USER.value,
        entity_id=user.id,
        actor=actor,
        new_value=audit_service.snapshot(user),
        reason="Criação de usuário.",
        context=context,
        signature_id=signature.id,
    )
    await db.commit()
    return user


async def get_user(db: AsyncSession, user_id) -> User:
    user = await db.get(User, user_id)
    if user is None:
        raise NotFoundError("Usuário não encontrado.")
    return user


async def list_users(
    db: AsyncSession, *, role: UserRole | None = None, active_only: bool = True
) -> list[User]:
    stmt = select(User)
    if role is not None:
        stmt = stmt.where(User.role == role)
    if active_only:
        stmt = stmt.where(User.is_active.is_(True))
    stmt = stmt.order_by(User.full_name.asc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


def permissions_for(role: UserRole) -> list[str]:
    return ROLE_PERMISSIONS.get(role, [])


# --------------------------------------------------------------------------
# Internos
# --------------------------------------------------------------------------
async def _issue_pair(
    db: AsyncSession, user: User, context: RequestContext
) -> tuple[str, str]:
    access = create_access_token(user.id, user.role.value, user.password_version)
    jti = secrets.token_urlsafe(24)
    refresh = create_refresh_token(user.id, jti)
    db.add(
        RefreshToken(
            jti=jti,
            user_id=user.id,
            expires_at=utcnow() + timedelta(hours=settings.REFRESH_TOKEN_EXPIRE_HOURS),
            ip_address=context.ip_address,
            user_agent=context.user_agent,
        )
    )
    return access, refresh


async def _revoke_all(db: AsyncSession, user_id, reason: str) -> None:
    tokens = await db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None)
        )
    )
    now = utcnow()
    for token in tokens.scalars():
        token.revoked_at = now
        token.revoked_reason = reason


async def _audit_failed_login(
    db: AsyncSession,
    user: User | None,
    username: str,
    reason: str,
    context: RequestContext,
) -> None:
    """Registra a falha na MESMA transação dos contadores de tentativa.

    Não executamos `rollback` antes do append: os incrementos de
    `failed_login_attempts` / `locked_until` feitos por `login` precisam ser
    persistidos junto com o evento de auditoria, de forma atômica. O commit
    também garante que a trilha sobreviva ao 401/403 devolvido em seguida.
    """
    try:
        await audit_service.append(
            db,
            action=AuditAction.LOGIN_FAILED,
            entity_type=AuditEntity.USER.value,
            entity_id=user.id if user else sha256_hex(username.lower())[:32],
            actor=user,
            actor_username=user.username if user else username[:64],
            new_value={"attempted_username": username[:64], "reason": reason},
            reason=reason,
            context=context,
        )
        await db.commit()
    except Exception:  # a falha de auditoria nunca deve mascarar o 401/403
        logger.exception(
            "Falha ao auditar tentativa de login malsucedida (username=%s).",
            username[:64],
        )
        await db.rollback()


def _invalid_credentials() -> ForbiddenError:
    return ForbiddenError(INVALID_CREDENTIALS)
