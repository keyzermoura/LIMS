"""Rotas de Gestão do Outbox Transacional e Dead-Letter Queue (H3.2).

Conforme ESPECIFICACAO_CAMADA_INTEGRACAO_LIMS.md §4 e ALCOA+.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select

from app.api.deps import DbSession, require_roles
from app.models.enums import UserRole
from app.models.outbox import IntegrationOutbox
from app.models.user import User
from app.schemas.outbox import OutboxDispatchResponse, OutboxEventOut
from app.services import outbox_service

router = APIRouter(prefix="/outbox", tags=["Outbox Transacional e Webhooks (H3.2)"])

AUDIT_ROLES = (UserRole.ADMIN, UserRole.AUDITOR)


@router.get(
    "/pending",
    response_model=list[OutboxEventOut],
    summary="Listar eventos pendentes de publicação",
)
async def list_pending_events(
    db: DbSession,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    current_user: User = Depends(require_roles(*AUDIT_ROLES)),
) -> list[OutboxEventOut]:
    stmt = (
        select(IntegrationOutbox)
        .where(
            IntegrationOutbox.published_at.is_(None),
            IntegrationOutbox.dead_lettered_at.is_(None),
        )
        .order_by(IntegrationOutbox.created_at.asc())
        .limit(limit)
    )
    result = await db.scalars(stmt)
    return [OutboxEventOut.model_validate(e) for e in result.all()]


@router.get(
    "/dead-letter",
    response_model=list[OutboxEventOut],
    summary="Listar eventos retidos em Dead-Letter Queue (DLQ)",
)
async def list_dead_letter_events(
    db: DbSession,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    current_user: User = Depends(require_roles(*AUDIT_ROLES)),
) -> list[OutboxEventOut]:
    stmt = (
        select(IntegrationOutbox)
        .where(IntegrationOutbox.dead_lettered_at.is_not(None))
        .order_by(IntegrationOutbox.dead_lettered_at.desc())
        .limit(limit)
    )
    result = await db.scalars(stmt)
    return [OutboxEventOut.model_validate(e) for e in result.all()]


@router.post(
    "/dispatch",
    response_model=OutboxDispatchResponse,
    summary="Acionar ciclo de processamento e envio do outbox (Admin)",
)
async def trigger_dispatch(
    db: DbSession,
    batch_size: Annotated[int, Query(ge=1, le=100)] = 50,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
) -> OutboxDispatchResponse:
    dispatched = await outbox_service.dispatch_pending_outbox(db, batch_size=batch_size)
    return OutboxDispatchResponse(dispatched_count=dispatched)


@router.post(
    "/{outbox_id}/retry",
    response_model=OutboxEventOut,
    summary="Reenfileirar evento de Dead-Letter para retentativa (Admin)",
)
async def retry_event(
    outbox_id: UUID,
    db: DbSession,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
) -> OutboxEventOut:
    event = await outbox_service.retry_dead_letter(db, outbox_id=outbox_id)
    return OutboxEventOut.model_validate(event)


__all__ = ["router"]
