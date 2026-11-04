"""Assinatura eletrônica em duas etapas (21 CFR Part 11 §11.200).

Etapa 1 — `issue`: o usuário reautentica (senha) e declara o significado e
o motivo da assinatura. A API emite um token de uso único, curto e vinculado
ao registro (`entity_type`, `entity_id`, `action`).

Etapa 2 — `consume`: a requisição de negócio apresenta o token; o serviço
valida a intenção, consome o token e o vincula ao payload exato gravado.

Uma assinatura nunca pode ser reutilizada, reaproveitada em outro registro
ou aplicada por outro usuário.
"""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from typing import Any, NoReturn
from uuid import UUID, uuid4

from fastapi import status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.core.context import RequestContext
from app.core.security import (
    TokenError,
    create_esign_token,
    decode_esign_token,
    sha256_hex,
    verify_password,
)
from app.core.serialization import canonical_json, jsonable
from app.models.base import utcnow
from app.models.electronic_signature import ElectronicSignature
from app.models.enums import (
    AuditAction,
    AuditEntity,
    SignatureAction,
    SignatureMeaning,
)
from app.models.user import User
from app.services import audit_service
from app.services.errors import SignatureRejectedError

MIN_REASON_LENGTH = 10


async def issue(
    db: AsyncSession,
    *,
    user: User,
    password: str,
    meaning: SignatureMeaning,
    reason: str,
    entity_type: str,
    entity_id: str,
    action: SignatureAction,
    context: RequestContext,
) -> tuple[ElectronicSignature, str]:
    reason = reason.strip()
    if len(reason) < MIN_REASON_LENGTH:
        raise SignatureRejectedError(
            f"O motivo da assinatura deve ter ao menos {MIN_REASON_LENGTH} caracteres.",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            audit=False,
        )

    valid_password = await run_in_threadpool(verify_password, password, user.hashed_password)
    if not valid_password or not user.is_active:
        await _record_rejection(
            db,
            user=user,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            reason="Falha de reautenticação na emissão de assinatura eletrônica.",
            context=context,
        )
        raise SignatureRejectedError("Senha inválida. Assinatura não emitida.")

    now = datetime.now(UTC)
    expires_at = now + timedelta(seconds=settings.ESIGNATURE_TTL_SECONDS)
    signature_id = uuid4()
    jti = secrets.token_urlsafe(24)

    manifest = {
        "manifest_version": "1.0",
        "signature_id": str(signature_id),
        "user": {
            "id": str(user.id),
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role.value,
            "registration_number": user.registration_number,
        },
        "entity": {"type": entity_type, "id": entity_id},
        "action": action.value,
        "meaning": meaning.value,
        "reason": reason,
        "method": "PASSWORD",
        "signed_at": now.isoformat(),
        "ip_address": context.ip_address,
        "request_id": context.request_id,
    }

    record = ElectronicSignature(
        id=signature_id,
        user_id=user.id,
        username_snapshot=user.username,
        full_name_snapshot=user.full_name,
        role_snapshot=user.role.value,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        meaning=meaning,
        reason=reason,
        method="PASSWORD",
        manifest=jsonable(manifest),
        manifest_hash=sha256_hex(canonical_json(manifest)),
        ip_address=context.ip_address,
        user_agent=context.user_agent,
        request_id=context.request_id,
        token_jti=jti,
        signed_at=now,
        expires_at=expires_at,
    )
    db.add(record)
    await db.flush()

    await audit_service.append(
        db,
        action=AuditAction.SIGNATURE_ISSUED,
        entity_type=AuditEntity.ELECTRONIC_SIGNATURE.value,
        entity_id=record.id,
        actor=user,
        new_value={
            "meaning": meaning.value,
            "reason": reason,
            "target_entity": entity_type,
            "target_id": entity_id,
            "target_action": action.value,
            "expires_at": expires_at.isoformat(),
        },
        reason=reason,
        context=context,
        signature_id=record.id,
    )
    await db.commit()

    token = create_esign_token(
        signature_id=record.id,
        user_id=user.id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action.value,
        meaning=meaning.value,
        jti=jti,
    )
    return record, token


async def consume(
    db: AsyncSession,
    *,
    token: str,
    user: User,
    entity_type: str,
    entity_id: str | UUID,
    action: SignatureAction,
    context: RequestContext,
) -> ElectronicSignature:
    """Valida e consome um token de assinatura. Não faz commit.

    O commit acontece junto com a alteração de negócio, garantindo que
    "assinatura consumida" e "registro assinado" sejam atômicos.
    """
    entity_id = str(entity_id)

    try:
        claims = decode_esign_token(token)
    except TokenError as exc:
        await _reject(
            db,
            user=user,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            reason=f"Token de assinatura inválido: {exc}",
            context=context,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    if claims.get("sub") != str(user.id):
        await _reject(
            db,
            user=user,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            reason="Token de assinatura emitido para outro usuário.",
            context=context,
            status_code=status.HTTP_403_FORBIDDEN,
        )

    if (
        claims.get("ent") != entity_type
        or claims.get("eid") != entity_id
        or claims.get("act") != action.value
    ):
        await _reject(
            db,
            user=user,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            reason="Token de assinatura não corresponde ao registro/ação solicitados.",
            context=context,
            status_code=status.HTTP_403_FORBIDDEN,
        )

    record = await db.get(
        ElectronicSignature, UUID(claims["sid"]), with_for_update=True
    )
    if record is None:
        await _reject(
            db,
            user=user,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            reason="Assinatura eletrônica inexistente.",
            context=context,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    now = utcnow()
    if record.consumed_at is not None:
        await _reject(
            db,
            user=user,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            reason="Tentativa de reutilizar uma assinatura já consumida.",
            context=context,
            status_code=status.HTTP_409_CONFLICT,
        )

    expires_at = record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at <= now:
        await _reject(
            db,
            user=user,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            reason="Assinatura expirada. Reautentique para assinar novamente.",
            context=context,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    if record.token_jti != claims.get("jti") or record.user_id != user.id:
        await _reject(
            db,
            user=user,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            reason="Token de assinatura inconsistente com o manifesto gravado.",
            context=context,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    record.consumed_at = now
    record.consumed_ip = context.ip_address
    record.consumed_user_agent = context.user_agent
    record.consumed_request_id = context.request_id
    await db.flush()
    return record


async def bind_record(
    db: AsyncSession, signature: ElectronicSignature, record: dict[str, Any]
) -> None:
    """Vincula criptograficamente a assinatura ao conteúdo exato gravado."""
    snapshot = jsonable(record)
    signature.payload_snapshot = snapshot
    signature.payload_hash = sha256_hex(canonical_json(snapshot))
    await db.flush()


# --------------------------------------------------------------------------
# Rejeições — auditadas em transação separada para sobreviver ao rollback
# --------------------------------------------------------------------------
async def _reject(
    db: AsyncSession,
    *,
    user: User,
    entity_type: str,
    entity_id: str,
    action: SignatureAction,
    reason: str,
    context: RequestContext,
    status_code: int = status.HTTP_401_UNAUTHORIZED,
) -> NoReturn:
    # `rollback` expira TODOS os objetos da sessão. Capturamos a identidade
    # antes e recarregamos o usuário para que a auditoria da rejeição não
    # tente um lazy-load síncrono (MissingGreenlet) no meio do fluxo async.
    user_id = user.id
    await db.rollback()
    fresh_user = await db.get(User, user_id)
    await _record_rejection(
        db,
        user=fresh_user,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        reason=reason,
        context=context,
    )
    raise SignatureRejectedError(reason, status_code=status_code)


async def _record_rejection(
    db: AsyncSession,
    *,
    user: User | None,
    entity_type: str,
    entity_id: str,
    action: SignatureAction,
    reason: str,
    context: RequestContext,
) -> None:
    try:
        await audit_service.append(
            db,
            action=AuditAction.SIGNATURE_REJECTED,
            entity_type=entity_type,
            entity_id=entity_id,
            actor=user,
            actor_username=user.username if user else "ANONYMOUS",
            new_value={"attempted_action": action.value, "rejection_reason": reason},
            reason=reason,
            context=context,
        )
        await db.commit()
    except Exception:  # a falha de auditoria nunca deve mascarar o 401/403
        await db.rollback()


async def consumed_signatures_for(
    db: AsyncSession, entity_type: str, entity_id: str
) -> list[ElectronicSignature]:
    result = await db.execute(
        select(ElectronicSignature)
        .where(
            ElectronicSignature.entity_type == entity_type,
            ElectronicSignature.entity_id == entity_id,
            ElectronicSignature.consumed_at.is_not(None),
        )
        .order_by(ElectronicSignature.signed_at.asc())
    )
    return list(result.scalars().all())
