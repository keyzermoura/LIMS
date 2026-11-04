"""Trilha de auditoria — leitura restrita e verificação de integridade."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request

from app.api.deps import CurrentUser, DbSession, require_roles
from app.core.context import RequestContext
from app.models.audit_log import AuditLog
from app.models.enums import AuditAction, AuditEntity, UserRole
from app.models.user import User
from app.schemas.audit import (
    AuditLogDetailOut,
    AuditLogOut,
    AuditVerifyResponse,
)
from app.schemas.common import Page
from app.services import audit_service

router = APIRouter(prefix="/audit", tags=["Trilha de Auditoria"])

AUDIT_ROLES = (UserRole.ADMIN, UserRole.AUDITOR)


@router.get(
    "",
    response_model=Page[AuditLogOut],
    summary="Consultar trilha de auditoria",
    description=(
        "Somente leitura, restrita a AUDITOR e ADMIN. A ordenação padrão é "
        "decrescente por sequência (evento mais recente primeiro)."
    ),
)
async def list_audit_logs(
    db: DbSession,
    user: CurrentUser,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    entity_type: str | None = Query(None, max_length=64),
    entity_id: str | None = Query(None, max_length=64),
    actor_id: UUID | None = Query(None),
    action: AuditAction | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    search: str | None = Query(None, max_length=120),
    _role: User = Depends(require_roles(*AUDIT_ROLES)),
) -> Page[AuditLogOut]:
    from sqlalchemy import func, or_, select

    stmt = select(AuditLog)
    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    if entity_id:
        stmt = stmt.where(AuditLog.entity_id == entity_id)
    if actor_id:
        stmt = stmt.where(AuditLog.actor_id == actor_id)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if date_from:
        stmt = stmt.where(AuditLog.occurred_at >= date_from)
    if date_to:
        stmt = stmt.where(AuditLog.occurred_at <= date_to)
    if search:
        term = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                AuditLog.actor_username.ilike(term),
                AuditLog.entity_id.ilike(term),
                AuditLog.reason.ilike(term),
            )
        )

    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    stmt = (
        stmt.order_by(AuditLog.sequence.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return Page[AuditLogOut].build(
        [AuditLogOut.model_validate(row) for row in rows], int(total), page, size
    )


@router.get(
    "/{log_id}",
    response_model=AuditLogDetailOut,
    summary="Detalhar evento de auditoria (inclui payload canônico)",
)
async def get_audit_log(
    log_id: int,
    db: DbSession,
    user: CurrentUser,
    _role: User = Depends(require_roles(*AUDIT_ROLES)),
) -> AuditLogDetailOut:
    from app.core.errors import NotFoundError

    row = await db.get(AuditLog, log_id)
    if row is None:
        raise NotFoundError("Evento de auditoria não encontrado.")
    return AuditLogDetailOut.model_validate(row)


@router.post(
    "/verify",
    response_model=AuditVerifyResponse,
    summary="Verificar integridade da cadeia de auditoria",
    description=(
        "Recalcula SHA-256 e HMAC de cada registro, valida a sequência e o "
        "encadeamento. A própria verificação é registrada na trilha."
    ),
)
async def verify_audit_chain(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    from_sequence: int = Query(1, ge=1),
    _role: User = Depends(require_roles(*AUDIT_ROLES)),
) -> AuditVerifyResponse:
    report = await audit_service.verify_chain(db, from_sequence=from_sequence)

    await audit_service.append(
        db,
        action=AuditAction.INTEGRITY_CHECK,
        entity_type=AuditEntity.AUDIT_LOG.value,
        entity_id="chain",
        actor=user,
        new_value={
            "ok": report["ok"],
            "checked": report["checked"],
            "last_sequence": report["last_sequence"],
            "issues": len(report["issues"]),
        },
        reason="Verificação de integridade da trilha de auditoria.",
        context=RequestContext.from_request(request),
    )
    await db.commit()
    return AuditVerifyResponse.model_validate(report)
