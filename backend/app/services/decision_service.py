"""Serviço de Decisões Técnicas de Recebimento e Revisão da Coordenação (Fase 1 / M1.2)."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.context import RequestContext
from app.core.errors import NotFoundError, ValidationDomainError
from app.models.base import utcnow
from app.models.decision import CoordinationReview, ReceiptDecision
from app.models.enums import (
    AuditAction,
    AuditEntity,
    CoordinationReviewStatus,
    ReceiptDecisionEnum,
)
from app.models.receipt import ReceiptItem
from app.models.user import User
from app.schemas.decision import CoordinationReviewAction, ReceiptDecisionCreate
from app.services import audit_service
from app.services.audit_service import snapshot


async def record_receipt_decision(
    db: AsyncSession,
    receipt_item_id: UUID,
    *,
    payload: ReceiptDecisionCreate,
    actor: User,
    context: RequestContext | None = None,
) -> tuple[ReceiptDecision, int]:
    """Registra decisão técnica sobre item e abre revisão da coordenação se houver ressalva/recusa."""
    receipt_item = await db.get(ReceiptItem, receipt_item_id)
    if receipt_item is None:
        raise NotFoundError("Item de recebimento não encontrado.")

    requires_review = payload.decision in {
        ReceiptDecisionEnum.PENDING,
        ReceiptDecisionEnum.REJECTED,
    }

    decision = ReceiptDecision(
        receipt_item_id=receipt_item.id,
        custody_object_id=payload.custody_object_id,
        decision=payload.decision,
        justification=payload.justification,
        decided_by_id=actor.id,
        requires_coordination_review=requires_review,
        version=1,
    )

    if requires_review:
        review = CoordinationReview(
            status=CoordinationReviewStatus.PENDENTE,
        )
        decision.coordination_review = review

    # Atualiza decisão no item
    receipt_item.decision = payload.decision
    receipt_item.version += 1

    db.add(decision)
    new_snapshot = snapshot(decision)
    await db.flush()

    audit_entry = await audit_service.append(
        db,
        action=AuditAction.CREATE,
        entity_type=AuditEntity.RECEIPT_DECISION.value,
        entity_id=decision.id,
        actor=actor,
        new_value=new_snapshot,
        reason=f"Decisão técnica registrada: {payload.decision.value}",
        context=context,
    )

    await db.commit()

    refreshed = await get_decision(db, decision.id)
    return refreshed, audit_entry.sequence


async def get_decision(db: AsyncSession, decision_id: UUID) -> ReceiptDecision:
    """Retorna decisão por ID com coordenação e custodiante carregados."""
    stmt = (
        select(ReceiptDecision)
        .options(
            selectinload(ReceiptDecision.coordination_review).selectinload(CoordinationReview.reviewed_by),
            selectinload(ReceiptDecision.decided_by),
        )
        .where(ReceiptDecision.id == decision_id)
    )
    decision = await db.scalar(stmt)
    if decision is None:
        raise NotFoundError("Decisão de recebimento não encontrada.")
    return decision


async def get_decisions_for_item(
    db: AsyncSession, receipt_item_id: UUID
) -> list[ReceiptDecision]:
    """Retorna histórico de decisões do item de recebimento."""
    stmt = (
        select(ReceiptDecision)
        .options(
            selectinload(ReceiptDecision.coordination_review).selectinload(CoordinationReview.reviewed_by),
            selectinload(ReceiptDecision.decided_by),
        )
        .where(ReceiptDecision.receipt_item_id == receipt_item_id)
        .order_by(ReceiptDecision.created_at.desc())
    )
    result = await db.scalars(stmt)
    return list(result.all())


async def review_coordination_decision(
    db: AsyncSession,
    review_id: UUID,
    *,
    payload: CoordinationReviewAction,
    reviewer: User,
    context: RequestContext | None = None,
) -> tuple[CoordinationReview, int]:
    """Validação independente da coordenação (D10 / Segregação de Funções)."""
    stmt = (
        select(CoordinationReview)
        .options(selectinload(CoordinationReview.decision))
        .where(CoordinationReview.id == review_id)
    )
    review = await db.scalar(stmt)
    if review is None:
        raise NotFoundError("Revisão da coordenação não encontrada.")

    # Regra D10: Segregação estrita de funções (4-eyes principle)
    if review.decision.decided_by_id == reviewer.id:
        raise ValidationDomainError(
            "Segregação de funções violada: o revisor da coordenação não pode ser o mesmo usuário que formalizou a decisão técnica."
        )

    if review.status != CoordinationReviewStatus.PENDENTE:
        raise ValidationDomainError(
            f"A revisão já foi finalizada com status {review.status.value}."
        )

    old_snapshot = snapshot(review)
    review.status = payload.status
    review.reviewed_by_id = reviewer.id
    review.reviewed_by = reviewer
    review.reviewed_at = utcnow()
    review.review_notes = payload.review_notes

    if payload.status == CoordinationReviewStatus.APROVADO:
        review.decision.requires_coordination_review = False
        review.decision.version += 1

    new_snapshot = snapshot(review)
    await db.flush()

    audit_entry = await audit_service.append(
        db,
        action=AuditAction.UPDATE,
        entity_type=AuditEntity.COORDINATION_REVIEW.value,
        entity_id=review.id,
        actor=reviewer,
        old_value=old_snapshot,
        new_value=new_snapshot,
        reason=f"Revisão da coordenação concluída: {payload.status.value}",
        context=context,
    )

    await db.commit()

    # Recarrega objeto revisado
    refreshed_stmt = (
        select(CoordinationReview)
        .options(
            selectinload(CoordinationReview.reviewed_by),
            selectinload(CoordinationReview.decision),
        )
        .where(CoordinationReview.id == review_id)
    )
    refreshed = await db.scalar(refreshed_stmt)
    assert refreshed is not None
    return refreshed, audit_entry.sequence


async def list_pending_reviews(db: AsyncSession) -> list[CoordinationReview]:
    """Lista revisões da coordenação aguardando deliberação."""
    stmt = (
        select(CoordinationReview)
        .options(
            selectinload(CoordinationReview.decision).selectinload(ReceiptDecision.decided_by),
            selectinload(CoordinationReview.reviewed_by),
        )
        .where(CoordinationReview.status == CoordinationReviewStatus.PENDENTE)
        .order_by(CoordinationReview.created_at.asc())
    )
    result = await db.scalars(stmt)
    return list(result.all())
