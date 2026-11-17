"""Serviço de Contas de Serviço (M2M) e Autenticação OAuth2 Client Credentials.

Conforme ESPECIFICACAO_CAMADA_INTEGRACAO_LIMS.md §2 e ALCOA+.
"""

from __future__ import annotations

import logging
import secrets
from datetime import UTC, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.errors import ConflictError, ForbiddenError, NotFoundError
from app.core.rbac import ROLE_PERMISSIONS
from app.core.security import (
    create_service_token,
    hash_secret,
    verify_password,
)
from app.models.base import utcnow
from app.models.enums import AuditAction, AuditEntity, UserRole
from app.models.service_client import ServiceClient
from app.models.user import User
from app.schemas.service_client import ServiceClientCreate
from app.services import audit_service
from app.services.errors import AuthError

logger = logging.getLogger(__name__)

DEFAULT_SERVICE_TOKEN_TTL_MINUTES = 15


async def create_service_client(
    db: AsyncSession,
    *,
    payload: ServiceClientCreate,
    created_by: User,
    context: RequestContext,
) -> tuple[ServiceClient, str]:
    """Cria uma conta de serviço M2M, usuário de serviço associado e credenciais iniciais."""
    if created_by.role != UserRole.ADMIN:
        raise ForbiddenError("Apenas administradores podem cadastrar contas de serviço.")

    # Gera identificadores e segredo forte
    raw_secret = secrets.token_urlsafe(32)
    client_id = f"svc_{secrets.token_hex(12)}"

    # Garante que o usuário de serviço existe ou cria um dedicado
    username = (
        payload.service_username.strip().lower() if payload.service_username else f"usr_{client_id}"
    )

    existing_user = await db.scalar(select(User).where(User.username == username))
    if existing_user:
        if existing_user.role != UserRole.SERVICE:
            raise ConflictError(f"O usuário {username} já existe e não é uma conta de serviço.")
        service_user = existing_user
    else:
        service_user = User(
            username=username,
            email=f"{username}@integrations.lims.local",
            full_name=f"Service Account: {payload.name}",
            role=UserRole.SERVICE,
            hashed_password=hash_secret(secrets.token_urlsafe(32)),
            is_active=True,
        )
        db.add(service_user)
        await db.flush()

    # Filtra escopos permitidos para o papel SERVICE
    allowed_scopes = set(ROLE_PERMISSIONS.get(UserRole.SERVICE, []))
    if "*" in allowed_scopes:
        granted_scopes = payload.scopes
    else:
        granted_scopes = [s for s in payload.scopes if s in allowed_scopes]
    if not granted_scopes:
        granted_scopes = list(allowed_scopes)

    expires_at = utcnow() + timedelta(days=payload.expires_in_days)
    secret_hash = hash_secret(raw_secret)

    client = ServiceClient(
        client_id=client_id,
        name=payload.name,
        secret_hash=secret_hash,
        scopes=granted_scopes,
        service_user_id=service_user.id,
        is_active=True,
        expires_at=expires_at,
        created_by_id=created_by.id,
        ip_allowlist=payload.ip_allowlist,
    )
    db.add(client)
    await db.flush()
    await db.refresh(client)

    await audit_service.append(
        db,
        action=AuditAction.CREATE,
        entity_type=AuditEntity.SERVICE_CLIENT.value,
        entity_id=str(client.id),
        actor=created_by,
        new_value={
            "client_id": client.client_id,
            "name": client.name,
            "scopes": client.scopes,
            "service_user_id": str(service_user.id),
            "expires_at": expires_at.isoformat(),
        },
        reason=f"Criação de conta de serviço M2M para {client.name}.",
        context=context,
    )
    await db.commit()
    return client, raw_secret


async def rotate_service_client_secret(
    db: AsyncSession,
    *,
    client_id: str,
    actor: User,
    context: RequestContext,
) -> tuple[ServiceClient, str]:
    """Rotaciona o segredo mantendo o anterior como secundário durante a janela de transição."""
    if actor.role != UserRole.ADMIN:
        raise ForbiddenError("Apenas administradores podem rotacionar credenciais de serviço.")

    client = await db.scalar(select(ServiceClient).where(ServiceClient.client_id == client_id))
    if not client:
        raise NotFoundError("Cliente de serviço não encontrado.")

    new_raw_secret = secrets.token_urlsafe(32)
    new_hash = hash_secret(new_raw_secret)

    # Move o segredo atual para secundário para permitir sobreposição de 7 dias sem downtime
    client.secondary_secret_hash = client.secret_hash
    client.secret_hash = new_hash
    client.expires_at = utcnow() + timedelta(days=90)

    await audit_service.append(
        db,
        action=AuditAction.UPDATE,
        entity_type=AuditEntity.SERVICE_CLIENT.value,
        entity_id=str(client.id),
        actor=actor,
        new_value={
            "client_id": client.client_id,
            "event": "SECRET_ROTATED",
            "expires_at": client.expires_at.isoformat(),
        },
        reason=f"Rotação de segredo da conta de serviço {client.client_id}.",
        context=context,
    )
    await db.commit()
    await db.refresh(client)
    return client, new_raw_secret


async def deactivate_service_client(
    db: AsyncSession,
    *,
    client_id: str,
    actor: User,
    context: RequestContext,
) -> ServiceClient:
    """Revoga imediatamente uma conta de serviço."""
    if actor.role != UserRole.ADMIN:
        raise ForbiddenError("Apenas administradores podem desativar contas de serviço.")

    client = await db.scalar(select(ServiceClient).where(ServiceClient.client_id == client_id))
    if not client:
        raise NotFoundError("Cliente de serviço não encontrado.")

    client.is_active = False
    await audit_service.append(
        db,
        action=AuditAction.STATUS_CHANGE,
        entity_type=AuditEntity.SERVICE_CLIENT.value,
        entity_id=str(client.id),
        actor=actor,
        new_value={"client_id": client.client_id, "is_active": False},
        reason=f"Revogação imediata da conta de serviço {client.client_id}.",
        context=context,
    )
    await db.commit()
    await db.refresh(client)
    return client


async def list_service_clients(
    db: AsyncSession,
    *,
    actor: User,
) -> list[ServiceClient]:
    """Lista todas as contas de serviço cadastradas."""
    if actor.role != UserRole.ADMIN:
        raise ForbiddenError("Apenas administradores podem visualizar contas de serviço.")

    result = await db.scalars(select(ServiceClient).order_by(ServiceClient.created_at.desc()))
    return list(result.all())


async def issue_service_token(
    db: AsyncSession,
    *,
    client_id: str,
    client_secret: str,
    requested_scope: str | None = None,
    context: RequestContext,
) -> tuple[str, list[str], int]:
    """Autentica o cliente M2M via OAuth2 Client Credentials e emite JWT de curta duração."""
    client = await db.scalar(select(ServiceClient).where(ServiceClient.client_id == client_id))
    if not client or not client.is_active:
        logger.warning("Falha de autenticação M2M: cliente %s inexistente ou inativo.", client_id)
        raise AuthError("Credenciais de serviço inválidas.")

    # Verifica validade temporal
    expires_at = client.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at <= utcnow():
        logger.warning("Falha de autenticação M2M: credencial do cliente %s expirada.", client_id)
        raise AuthError("Credencial de serviço expirada.")

    # Verifica segredo (primário ou secundário em sobreposição)
    is_valid = verify_password(client_secret, client.secret_hash)
    if not is_valid and client.secondary_secret_hash:
        is_valid = verify_password(client_secret, client.secondary_secret_hash)

    if not is_valid:
        logger.warning("Falha de autenticação M2M: segredo inválido para cliente %s.", client_id)
        raise AuthError("Credenciais de serviço inválidas.")

    # Valida usuário de serviço associado
    service_user = await db.get(User, client.service_user_id)
    if not service_user or not service_user.is_active or service_user.role != UserRole.SERVICE:
        logger.error(
            "Falha de autenticação M2M: usuário de serviço para cliente %s indisponível.", client_id
        )
        raise AuthError("Conta de serviço associada inválida.")

    # Interseção de escopos
    granted_scopes = set(client.scopes)
    if requested_scope:
        req_set = set(requested_scope.strip().split())
        effective_scopes = list(req_set.intersection(granted_scopes))
        if not effective_scopes:
            effective_scopes = list(granted_scopes)
    else:
        effective_scopes = list(granted_scopes)

    # Atualiza timestamp de uso
    client.last_used_at = utcnow()
    await db.commit()

    ttl_minutes = DEFAULT_SERVICE_TOKEN_TTL_MINUTES
    token = create_service_token(
        client_id=client.client_id,
        user_id=service_user.id,
        scopes=effective_scopes,
        ttl=timedelta(minutes=ttl_minutes),
    )
    return token, effective_scopes, ttl_minutes * 60
