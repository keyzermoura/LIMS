"""Serviço de Notificações e Alertas em Tempo Real (Fase 5 / Sprint 5.2).

Implementa a emissão, listagem, consolidação e varredura proativa de desvios
laboratoriais (ISO/IEC 17025:2017 §7.11/§8.7 e 21 CFR Part 11).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.models.capa_action import CapaAction
from app.models.capa_action_item import CapaActionItem
from app.models.device_sample import DeviceSample
from app.models.enums import (
    CapaEffectivenessStatus,
    CapaItemStatus,
    CapaStatus,
    EquipmentCalibrationStatus,
    NotificationCategory,
    NotificationSeverity,
    QualificationStatus,
    SampleStatus,
    UserRole,
)
from app.models.equipment import LaboratoryEquipment
from app.models.notification import Notification
from app.models.qualification import AnalystQualification
from app.schemas.notification import (
    AlertCheckResult,
    NotificationCreateIn,
    NotificationSummary,
)


async def create_notification(db: AsyncSession, payload: NotificationCreateIn) -> Notification:
    """Cria e persiste uma nova notificação."""
    notification = Notification(
        user_id=payload.user_id,
        target_role=payload.target_role,
        title=payload.title,
        message=payload.message,
        severity=payload.severity,
        category=payload.category,
        link_url=payload.link_url,
    )
    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    return notification


async def list_notifications(
    db: AsyncSession,
    user_id: UUID,
    role: UserRole,
    unread_only: bool = False,
    severity: NotificationSeverity | None = None,
    limit: int = 50,
) -> list[Notification]:
    """Lista notificações visíveis para o usuário e seu perfil."""
    stmt = select(Notification).where(
        or_(
            Notification.user_id == user_id,
            Notification.target_role == role,
            and_(Notification.user_id.is_(None), Notification.target_role.is_(None)),
        )
    )

    if unread_only:
        stmt = stmt.where(Notification.is_read == False)  # noqa: E712

    if severity:
        stmt = stmt.where(Notification.severity == severity)

    stmt = stmt.order_by(Notification.created_at.desc()).limit(limit)
    return list((await db.scalars(stmt)).all())


async def get_notification_summary(
    db: AsyncSession, user_id: UUID, role: UserRole
) -> NotificationSummary:
    """Calcula o sumário de notificações não lidas por severidade."""
    base_filter = or_(
        Notification.user_id == user_id,
        Notification.target_role == role,
        and_(Notification.user_id.is_(None), Notification.target_role.is_(None)),
    )

    unread_stmt = select(func.count(Notification.id)).where(
        base_filter,
        Notification.is_read == False,  # noqa: E712
    )
    total_unread = (await db.scalar(unread_stmt)) or 0

    critical_stmt = select(func.count(Notification.id)).where(
        base_filter,
        Notification.is_read == False,  # noqa: E712
        Notification.severity == NotificationSeverity.CRITICAL,
    )
    critical_unread = (await db.scalar(critical_stmt)) or 0

    warning_stmt = select(func.count(Notification.id)).where(
        base_filter,
        Notification.is_read == False,  # noqa: E712
        Notification.severity == NotificationSeverity.WARNING,
    )
    warning_unread = (await db.scalar(warning_stmt)) or 0

    info_stmt = select(func.count(Notification.id)).where(
        base_filter,
        Notification.is_read == False,  # noqa: E712
        Notification.severity == NotificationSeverity.INFO,
    )
    info_unread = (await db.scalar(info_stmt)) or 0

    return NotificationSummary(
        unread_count=total_unread,
        critical_count=critical_unread,
        warning_count=warning_unread,
        info_count=info_unread,
    )


async def mark_as_read(db: AsyncSession, notification_id: UUID, user_id: UUID) -> Notification:
    """Marca uma notificação individual como lida."""
    notification = await db.get(Notification, notification_id)
    if not notification:
        raise NotFoundError("Notificação não encontrada.")

    notification.is_read = True
    notification.read_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(notification)
    return notification


async def mark_all_as_read(db: AsyncSession, user_id: UUID, role: UserRole) -> int:
    """Marca todas as notificações visíveis do usuário como lidas."""
    now = datetime.now(UTC)
    stmt = (
        update(Notification)
        .where(
            or_(
                Notification.user_id == user_id,
                Notification.target_role == role,
                and_(Notification.user_id.is_(None), Notification.target_role.is_(None)),
            ),
            Notification.is_read == False,  # noqa: E712
        )
        .values(is_read=True, read_at=now)
    )
    result = await db.execute(stmt)
    await db.commit()
    row_count = getattr(result, "rowcount", 0)
    return int(row_count or 0)


async def _alert_already_emitted_recently(
    db: AsyncSession, title: str, within_hours: int = 24
) -> bool:
    """Evita duplicidade de alertas emitidos pelo sistema dentro da janela configurada."""
    cutoff = datetime.now(UTC) - timedelta(hours=within_hours)
    stmt = select(func.count(Notification.id)).where(
        Notification.title == title,
        Notification.created_at >= cutoff,
    )
    count = (await db.scalar(stmt)) or 0
    return count > 0


async def check_and_generate_system_alerts(db: AsyncSession) -> AlertCheckResult:
    """Varre proativamente o laboratório em busca de desvios e emite alertas automáticos."""
    now = datetime.now(UTC)
    today = now.date()
    alerts_created: list[str] = []

    # -------------------------------------------------------------------------
    # 1. Alertas de Calibração de Equipamentos
    # -------------------------------------------------------------------------
    eq_stmt = select(LaboratoryEquipment)
    equipments = (await db.scalars(eq_stmt)).all()

    for eq in equipments:
        calib_date = eq.calibration_due_date.date() if eq.calibration_due_date else None
        # Vencido
        if eq.calibration_status == EquipmentCalibrationStatus.VENCIDO or (
            calib_date and calib_date < today
        ):
            title = f"Calibração Vencida: {eq.code}"
            if not await _alert_already_emitted_recently(db, title):
                await create_notification(
                    db,
                    NotificationCreateIn(
                        target_role=UserRole.TECNICO,
                        title=title,
                        message=f"Equipamento {eq.code} ({eq.name}) está com calibração vencida. Intertravamento ativo para novos ensaios (ISO 17025 §6.4).",
                        severity=NotificationSeverity.CRITICAL,
                        category=NotificationCategory.CALIBRATION,
                        link_url="/equipment",
                    ),
                )
                alerts_created.append(title)
        # Vencendo em até 15 dias
        elif calib_date and today <= calib_date <= today + timedelta(days=15):
            days_left = (calib_date - today).days
            title = f"Calibração Próxima do Vencimento: {eq.code}"
            if not await _alert_already_emitted_recently(db, title):
                await create_notification(
                    db,
                    NotificationCreateIn(
                        target_role=UserRole.TECNICO,
                        title=title,
                        message=f"Equipamento {eq.code} ({eq.name}) vencerá calibração em {days_left} dias ({calib_date.strftime('%d/%m/%Y')}). Agendar calibração RBC.",
                        severity=NotificationSeverity.WARNING,
                        category=NotificationCategory.CALIBRATION,
                        link_url="/equipment",
                    ),
                )
                alerts_created.append(title)

    # -------------------------------------------------------------------------
    # 2. Alertas de Competência e Qualificação de Analistas (ISO 17025 §6.2)
    # -------------------------------------------------------------------------
    qual_stmt = select(AnalystQualification)
    qualifications = (await db.scalars(qual_stmt)).all()

    for q in qualifications:
        exp_date = q.expires_at.date() if q.expires_at else None
        if q.status == QualificationStatus.EXPIRADO or (exp_date and exp_date < today):
            title = f"Qualificação Expirada: {q.user.full_name}"
            if not await _alert_already_emitted_recently(db, title):
                await create_notification(
                    db,
                    NotificationCreateIn(
                        target_role=UserRole.ADMIN,
                        title=title,
                        message=f"Habilitação de {q.user.full_name} para o método {q.method.code} está expirada. Requalificação necessária.",
                        severity=NotificationSeverity.CRITICAL,
                        category=NotificationCategory.COMPETENCE,
                        link_url="/qualifications",
                    ),
                )
                alerts_created.append(title)
        elif exp_date and today <= exp_date <= today + timedelta(days=30):
            days_left = (exp_date - today).days
            title = f"Qualificação a Expirar: {q.user.full_name}"
            if not await _alert_already_emitted_recently(db, title):
                await create_notification(
                    db,
                    NotificationCreateIn(
                        user_id=q.user_id,
                        target_role=UserRole.ADMIN,
                        title=title,
                        message=f"Sua habilitação para o método {q.method.code} expira em {days_left} dias ({exp_date.strftime('%d/%m/%Y')}).",
                        severity=NotificationSeverity.WARNING,
                        category=NotificationCategory.COMPETENCE,
                        link_url="/qualifications",
                    ),
                )
                alerts_created.append(title)

    # -------------------------------------------------------------------------
    # 3. Alertas de Não Conformidades e CAPA (ISO 17025 §8.7)
    # -------------------------------------------------------------------------
    capa_stmt = select(CapaAction).where(CapaAction.status != CapaStatus.CONCLUIDA)
    capas = (await db.scalars(capa_stmt)).all()

    for c in capas:
        # Eficácia vencida
        if (
            c.target_effectiveness_date
            and c.target_effectiveness_date < today
            and c.effectiveness_status == CapaEffectivenessStatus.PENDENTE
        ):
            title = f"Eficácia CAPA Atrasada: {c.code}"
            if not await _alert_already_emitted_recently(db, title):
                await create_notification(
                    db,
                    NotificationCreateIn(
                        target_role=UserRole.ADMIN,
                        title=title,
                        message=f"CAPA {c.code} ({c.title}) está com avaliação de eficácia pendente desde {c.target_effectiveness_date.strftime('%d/%m/%Y')}.",
                        severity=NotificationSeverity.CRITICAL,
                        category=NotificationCategory.CAPA,
                        link_url="/capas",
                    ),
                )
                alerts_created.append(title)

    # Ações 5W2H atrasadas
    item_stmt = select(CapaActionItem).where(
        CapaActionItem.status != CapaItemStatus.CONCLUIDA,
        CapaActionItem.due_date < today,
    )
    overdue_items = (await db.scalars(item_stmt)).all()

    for it in overdue_items:
        title = f"Ação CAPA em Atraso: {it.title[:30]}"
        if not await _alert_already_emitted_recently(db, title):
            await create_notification(
                db,
                NotificationCreateIn(
                    user_id=it.assigned_to_id,
                    target_role=UserRole.ADMIN,
                    title=title,
                    message=f"Item de ação '{it.title}' venceu em {it.due_date.strftime('%d/%m/%Y')} e ainda não foi concluído.",
                    severity=NotificationSeverity.WARNING,
                    category=NotificationCategory.CAPA,
                    link_url="/capas",
                ),
            )
            alerts_created.append(title)

    # -------------------------------------------------------------------------
    # 4. Alertas de Amostras em Backlog Crítico (> 15 dias)
    # -------------------------------------------------------------------------
    cutoff_15d = now - timedelta(days=15)
    sample_stmt = select(DeviceSample).where(
        DeviceSample.status.in_([SampleStatus.RECEBIDO, SampleStatus.EM_TESTE]),
        DeviceSample.created_at < cutoff_15d,
    )
    delayed_samples = (await db.scalars(sample_stmt)).all()

    for s in delayed_samples:
        title = f"Atraso Crítico em Amostra: {s.serial_number}"
        if not await _alert_already_emitted_recently(db, title):
            await create_notification(
                db,
                NotificationCreateIn(
                    target_role=UserRole.FISCAL,
                    title=title,
                    message=f"Amostra {s.commercial_name} (S/N: {s.serial_number}) está há mais de 15 dias em bancada sem laudo oficial emitido.",
                    severity=NotificationSeverity.CRITICAL,
                    category=NotificationCategory.TAT,
                    link_url="/",
                ),
            )
            alerts_created.append(title)

    return AlertCheckResult(
        alerts_generated=len(alerts_created),
        details=alerts_created,
    )
