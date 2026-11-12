"""Serviço de Solicitações e Itens Declarados (Fase 1 / M1.1)."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.context import RequestContext
from app.core.errors import ConflictError, NotFoundError, ValidationDomainError
from app.db.dialect import next_sequence
from app.models.base import utcnow
from app.models.enums import AuditAction, AuditEntity, SolicitationStatus
from app.models.solicitation import Solicitation, SolicitationItem
from app.models.user import User
from app.schemas.solicitation import (
    SolicitationCreate,
    SolicitationSubmit,
    SolicitationUpdate,
)
from app.services import audit_service
from app.services.audit_service import snapshot
from app.services.workflow import ensure_solicitation_transition


async def create_solicitation(
    db: AsyncSession,
    *,
    payload: SolicitationCreate,
    actor: User,
    context: RequestContext | None = None,
) -> tuple[Solicitation, int]:
    """Cria uma solicitação cadastrada em RASCUNHO com seus itens declarados."""
    sequence = await next_sequence(db, "solicitation_number_seq")
    solicitation_number = f"SOL-{utcnow().year}-{int(sequence):05d}"

    solicitation = Solicitation(
        solicitation_number=solicitation_number,
        requester_name=payload.requester_name,
        requester_email=payload.requester_email,
        requester_document=payload.requester_document,
        requester_organization=payload.requester_organization,
        created_by_id=actor.id,
        purpose=payload.purpose,
        request_type=payload.request_type,
        priority=payload.priority,
        status=SolicitationStatus.RASCUNHO,
        version=1,
    )

    for idx, item_data in enumerate(payload.items, start=1):
        item = SolicitationItem(
            item_number=idx,
            product_name=item_data.product_name,
            category=item_data.category,
            manufacturer=item_data.manufacturer,
            model=item_data.model,
            serial_number=item_data.serial_number,
            lot_number=item_data.lot_number,
            declared_quantity=item_data.declared_quantity,
            unit_of_measure=item_data.unit_of_measure,
            notes=item_data.notes,
        )
        solicitation.items.append(item)

    db.add(solicitation)
    new_snapshot = snapshot(solicitation)
    await db.flush()

    audit_entry = await audit_service.append(
        db,
        action=AuditAction.CREATE,
        entity_type=AuditEntity.SOLICITATION.value,
        entity_id=solicitation.id,
        actor=actor,
        new_value=new_snapshot,
        reason="Criação da solicitação",
        context=context,
    )
    await db.commit()
    refreshed = await get_solicitation(db, solicitation.id)
    return refreshed, audit_entry.sequence


async def get_solicitation(db: AsyncSession, solicitation_id: UUID) -> Solicitation:
    """Retorna uma solicitação com seus itens carregados ou 404."""
    stmt = (
        select(Solicitation)
        .options(
            selectinload(Solicitation.items),
            selectinload(Solicitation.receipt),
        )
        .where(Solicitation.id == solicitation_id)
    )
    solicitation = await db.scalar(stmt)
    if solicitation is None:
        raise NotFoundError("Solicitação não encontrada.")
    return solicitation


async def list_solicitations(
    db: AsyncSession,
    *,
    status: SolicitationStatus | None = None,
    search: str | None = None,
    page: int = 1,
    size: int = 20,
) -> tuple[list[Solicitation], int]:
    """Listagem paginada de solicitações com contagem total."""
    stmt = select(Solicitation).options(
        selectinload(Solicitation.items),
        selectinload(Solicitation.receipt),
    )
    count_stmt = select(func.count()).select_from(Solicitation)

    if status:
        stmt = stmt.where(Solicitation.status == status)
        count_stmt = count_stmt.where(Solicitation.status == status)

    if search:
        term = f"%{search.strip()}%"
        condition = or_(
            Solicitation.solicitation_number.ilike(term),
            Solicitation.requester_name.ilike(term),
            Solicitation.requester_organization.ilike(term),
        )
        stmt = stmt.where(condition)
        count_stmt = count_stmt.where(condition)

    total = int(await db.scalar(count_stmt) or 0)
    stmt = (
        stmt.order_by(Solicitation.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )

    result = await db.scalars(stmt)
    return list(result.all()), total


async def update_solicitation(
    db: AsyncSession,
    solicitation_id: UUID,
    *,
    payload: SolicitationUpdate,
    actor: User,
    context: RequestContext | None = None,
) -> tuple[Solicitation, int]:
    """Atualiza dados cadastrais e itens de uma solicitação em RASCUNHO."""
    solicitation = await get_solicitation(db, solicitation_id)

    if solicitation.status != SolicitationStatus.RASCUNHO:
        raise ValidationDomainError(
            f"Apenas solicitações em RASCUNHO podem ser alteradas. Status atual: {solicitation.status.value}"
        )

    if solicitation.version != payload.version:
        raise ConflictError("A solicitação foi modificada por outro processo. Atualize e tente novamente.")

    old_snapshot = snapshot(solicitation)

    if payload.requester_name is not None:
        solicitation.requester_name = payload.requester_name
    if payload.requester_email is not None:
        solicitation.requester_email = payload.requester_email
    if payload.requester_document is not None:
        solicitation.requester_document = payload.requester_document
    if payload.requester_organization is not None:
        solicitation.requester_organization = payload.requester_organization
    if payload.purpose is not None:
        solicitation.purpose = payload.purpose
    if payload.request_type is not None:
        solicitation.request_type = payload.request_type
    if payload.priority is not None:
        solicitation.priority = payload.priority

    if payload.items is not None:
        if len(payload.items) == 0:
            raise ValidationDomainError("A solicitação deve conter ao menos um item.")
        # Substitui a coleção mantendo integridade
        solicitation.items.clear()
        for idx, item_data in enumerate(payload.items, start=1):
            item = SolicitationItem(
                item_number=idx,
                product_name=item_data.product_name,
                category=item_data.category,
                manufacturer=item_data.manufacturer,
                model=item_data.model,
                serial_number=item_data.serial_number,
                lot_number=item_data.lot_number,
                declared_quantity=item_data.declared_quantity,
                unit_of_measure=item_data.unit_of_measure,
                notes=item_data.notes,
            )
            solicitation.items.append(item)

    solicitation.version += 1
    new_snapshot = snapshot(solicitation)
    await db.flush()

    audit_entry = await audit_service.append(
        db,
        action=AuditAction.UPDATE,
        entity_type=AuditEntity.SOLICITATION.value,
        entity_id=solicitation.id,
        actor=actor,
        old_value=old_snapshot,
        new_value=new_snapshot,
        reason="Atualização da solicitação",
        context=context,
    )
    await db.commit()
    refreshed = await get_solicitation(db, solicitation.id)
    return refreshed, audit_entry.sequence


async def submit_solicitation(
    db: AsyncSession,
    solicitation_id: UUID,
    *,
    payload: SolicitationSubmit,
    actor: User,
    context: RequestContext | None = None,
) -> tuple[Solicitation, int]:
    """Transiciona a solicitação de RASCUNHO para SUBMETIDA."""
    solicitation = await get_solicitation(db, solicitation_id)

    ensure_solicitation_transition(solicitation.status, SolicitationStatus.SUBMETIDA)

    if len(solicitation.items) == 0:
        raise ValidationDomainError("Não é possível submeter uma solicitação sem itens cadastrados.")

    if solicitation.version != payload.version:
        raise ConflictError("A solicitação foi modificada por outro processo. Atualize e tente novamente.")

    old_snapshot = snapshot(solicitation)
    solicitation.status = SolicitationStatus.SUBMETIDA
    solicitation.submitted_at = utcnow()
    solicitation.version += 1
    new_snapshot = snapshot(solicitation)
    await db.flush()

    audit_entry = await audit_service.append(
        db,
        action=AuditAction.STATUS_CHANGE,
        entity_type=AuditEntity.SOLICITATION.value,
        entity_id=solicitation.id,
        actor=actor,
        old_value=old_snapshot,
        new_value=new_snapshot,
        reason=payload.notes or "Submissão da solicitação",
        context=context,
    )
    await db.commit()
    refreshed = await get_solicitation(db, solicitation.id)
    return refreshed, audit_entry.sequence


async def cancel_solicitation(
    db: AsyncSession,
    solicitation_id: UUID,
    *,
    reason: str,
    actor: User,
    version: int,
    context: RequestContext | None = None,
) -> tuple[Solicitation, int]:
    """Cancela a solicitação se não estiver concluída ou com recebimento registrado."""
    solicitation = await get_solicitation(db, solicitation_id)

    ensure_solicitation_transition(solicitation.status, SolicitationStatus.CANCELADA)

    if solicitation.version != version:
        raise ConflictError("A solicitação foi modificada por outro processo. Atualize e tente novamente.")

    old_snapshot = snapshot(solicitation)
    solicitation.status = SolicitationStatus.CANCELADA
    solicitation.version += 1
    new_snapshot = snapshot(solicitation)
    await db.flush()

    audit_entry = await audit_service.append(
        db,
        action=AuditAction.STATUS_CHANGE,
        entity_type=AuditEntity.SOLICITATION.value,
        entity_id=solicitation.id,
        actor=actor,
        old_value=old_snapshot,
        new_value=new_snapshot,
        reason=reason,
        context=context,
    )
    await db.commit()
    refreshed = await get_solicitation(db, solicitation.id)
    return refreshed, audit_entry.sequence
