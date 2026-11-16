"""Rotas de Notificações e Alertas em Tempo Real (Fase 5 / Sprint 5.2).

Conforme ISO/IEC 17025:2017 (§7.11/§8.7) e 21 CFR Part 11.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.deps import CurrentUser, DbSession
from app.models.enums import NotificationSeverity
from app.schemas.notification import (
    AlertCheckResult,
    NotificationCreateIn,
    NotificationOut,
    NotificationSummary,
)
from app.services import notification_service

router = APIRouter(
    prefix="/notifications",
    tags=["Notificações e Alertas em Tempo Real (Fase 5)"],
)


@router.get("", response_model=list[NotificationOut])
async def list_notifications(
    db: DbSession,
    current_user: CurrentUser,
    unread_only: Annotated[bool, Query(description="Filtrar apenas não lidas")] = False,
    severity: Annotated[NotificationSeverity | None, Query(description="Filtrar por severidade")] = None,
    limit: Annotated[int, Query(ge=1, le=100, description="Limite de registros")] = 50,
) -> list[NotificationOut]:
    """Lista notificações visíveis para o usuário corrente e seu respectivo perfil."""
    items = await notification_service.list_notifications(
        db=db,
        user_id=current_user.id,
        role=current_user.role,
        unread_only=unread_only,
        severity=severity,
        limit=limit,
    )
    return [NotificationOut.model_validate(it) for it in items]


@router.get("/summary", response_model=NotificationSummary)
async def get_notifications_summary(
    db: DbSession,
    current_user: CurrentUser,
) -> NotificationSummary:
    """Retorna o resumo de notificações não lidas e a distribuição por severidade."""
    return await notification_service.get_notification_summary(
        db=db, user_id=current_user.id, role=current_user.role
    )


@router.patch("/{notification_id}/read", response_model=NotificationOut)
async def mark_notification_as_read(
    notification_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> NotificationOut:
    """Marca uma notificação individual como lida."""
    notification = await notification_service.mark_as_read(
        db=db, notification_id=notification_id, user_id=current_user.id
    )
    return NotificationOut.model_validate(notification)


@router.post("/read-all")
async def mark_all_notifications_as_read(
    db: DbSession,
    current_user: CurrentUser,
) -> dict[str, int]:
    """Marca todas as notificações pendentes do usuário como lidas."""
    count = await notification_service.mark_all_as_read(
        db=db, user_id=current_user.id, role=current_user.role
    )
    return {"marked_count": count}


@router.post("/check-alerts", response_model=AlertCheckResult)
async def check_and_generate_alerts(
    db: DbSession,
    _: CurrentUser,
) -> AlertCheckResult:
    """Executa a rotina de varredura proativa de desvios laboratoriais e emite alertas automáticos."""
    return await notification_service.check_and_generate_system_alerts(db)


@router.post(
    "",
    response_model=NotificationOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_custom_notification(
    payload: NotificationCreateIn,
    db: DbSession,
    _: CurrentUser,
) -> NotificationOut:
    """Emite uma nova notificação no laboratório."""
    notification = await notification_service.create_notification(db, payload)
    return NotificationOut.model_validate(notification)
