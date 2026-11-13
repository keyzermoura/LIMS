"""Serviço de Revisão Técnica por Pares (Peer Review / ISO/IEC 17025 / Sprint 3.1)."""

from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.context import RequestContext
from app.core.errors import NotFoundError, ValidationDomainError
from app.models.base import utcnow
from app.models.electronic_signature import ElectronicSignature
from app.models.enums import (
    AuditAction,
    AuditEntity,
    CoordinationReviewStatus,
    SignatureAction,
    TestStatus,
    UserRole,
)
from app.models.lab_test import LabTest
from app.models.test_review import TestReview
from app.models.user import User
from app.schemas.test_review import TestReviewDecisionIn, TestSubmitReviewIn
from app.services import audit_service, signature_service
from app.services.audit_service import snapshot


async def submit_test_for_review(
    db: AsyncSession,
    test_id: UUID,
    *,
    payload: TestSubmitReviewIn | None = None,
    actor: User,
    context: RequestContext | None = None,
) -> tuple[LabTest, int]:
    """Submete um ensaio concluído para revisão técnica colegiada/por pares."""
    test = await db.get(LabTest, test_id)
    if test is None:
        raise NotFoundError("Ensaio laboratorial não encontrado.")

    if test.status != TestStatus.CONCLUIDO:
        raise ValidationDomainError(
            f"Apenas ensaios com status CONCLUIDO podem ser submetidos a revisão. Status atual: {test.status.value}"
        )

    old_state = snapshot(test)
    test.review_status = CoordinationReviewStatus.PENDENTE
    test.version += 1
    new_state = snapshot(test)

    audit_entry = await audit_service.append(
        db,
        action=AuditAction.UPDATE,
        entity_type=AuditEntity.LAB_TEST.value,
        entity_id=test.id,
        actor=actor,
        old_value=old_state,
        new_value=new_state,
        reason="Ensaio submetido para revisão técnica por pares",
        context=context,
    )
    await db.commit()
    return test, audit_entry.sequence


async def record_test_review(
    db: AsyncSession,
    test_id: UUID,
    *,
    payload: TestReviewDecisionIn,
    reviewer: User,
    signature_token: str | None = None,
    context: RequestContext | None = None,
) -> tuple[TestReview, int]:
    """Julgamento técnico do ensaio com segregação de funções e assinatura eletrônica (4-eyes principle)."""
    stmt = (
        select(LabTest)
        .options(selectinload(LabTest.tested_by))
        .where(LabTest.id == test_id)
    )
    test = await db.scalar(stmt)
    if test is None:
        raise NotFoundError("Ensaio laboratorial não encontrado.")

    # Regra ISO/IEC 17025 §7.7 / §7.8: Segregação estrita de funções
    # O revisor técnico NÃO pode ser o analista executor do ensaio.
    if test.tested_by_id == reviewer.id and reviewer.role != UserRole.ADMIN:
        raise ValidationDomainError(
            "Segregação de funções violada: o revisor técnico por pares não pode ser o mesmo analista que executou o ensaio."
        )

    if (
        payload.status == CoordinationReviewStatus.DEVOLVIDO
        and (not payload.justification or len(payload.justification.strip()) < 10)
    ):
        raise ValidationDomainError(
            "Justificativa obrigatória (mínimo 10 caracteres) ao devolver ensaio com ressalva."
        )

    sig_record: ElectronicSignature | None = None
    if signature_token:
        request_ctx = context or RequestContext(
            ip_address="127.0.0.1", user_agent="LIMS-Internal", request_id="internal"
        )
        sig_record = await signature_service.consume(
            db,
            token=signature_token,
            user=reviewer,
            entity_type="LabTest",
            entity_id=str(test.id),
            action=SignatureAction.UPDATE,
            context=request_ctx,
        )

    now = utcnow()
    count_stmt = (
        select(func.count())
        .select_from(TestReview)
        .where(TestReview.lab_test_id == test.id)
    )
    total_reviews = (await db.scalar(count_stmt)) or 0
    review_number = total_reviews + 1

    review = TestReview(
        id=uuid4(),
        lab_test_id=test.id,
        review_number=review_number,
        status=payload.status,
        reviewed_by_id=reviewer.id,
        reviewed_at=now,
        notes=payload.notes,
        justification=payload.justification,
        signature_id=sig_record.id if sig_record else None,
        attributes={"findings": payload.findings},
    )
    db.add(review)

    # Atualiza status de revisão no ensaio
    old_test_state = snapshot(test)
    test.review_status = payload.status
    if payload.status == CoordinationReviewStatus.DEVOLVIDO:
        # Reabre ensaio para retrabalho/correção
        test.status = TestStatus.PENDENTE
    test.version += 1
    new_test_state = snapshot(test)

    # Registra trilha de auditoria append-only
    audit_entry = await audit_service.append(
        db,
        action=AuditAction.CREATE,
        entity_type=AuditEntity.TEST_REVIEW.value,
        entity_id=review.id,
        actor=reviewer,
        old_value=None,
        new_value=snapshot(review),
        reason=f"Parecer de revisão técnica registrado: {payload.status.value}",
        context=context,
        signature_id=sig_record.id if sig_record else None,
    )

    await audit_service.append(
        db,
        action=AuditAction.UPDATE,
        entity_type=AuditEntity.LAB_TEST.value,
        entity_id=test.id,
        actor=reviewer,
        old_value=old_test_state,
        new_value=new_test_state,
        reason=f"Status de revisão do ensaio alterado para {payload.status.value}",
        context=context,
        signature_id=sig_record.id if sig_record else None,
    )

    await db.commit()
    await db.refresh(review, ["reviewed_by"])
    return review, audit_entry.sequence


async def list_pending_reviews(
    db: AsyncSession,
) -> list[LabTest]:
    """Lista ensaios concluídos com revisão pendente."""
    stmt = (
        select(LabTest)
        .options(
            selectinload(LabTest.sample),
            selectinload(LabTest.tested_by),
        )
        .where(
            LabTest.review_status == CoordinationReviewStatus.PENDENTE,
            LabTest.status == TestStatus.CONCLUIDO,
        )
        .order_by(LabTest.tested_at.desc().nullslast())
    )
    res = await db.scalars(stmt)
    return list(res.all())


async def get_test_reviews(
    db: AsyncSession,
    test_id: UUID,
) -> list[TestReview]:
    """Retorna histórico de revisões de um ensaio."""
    stmt = (
        select(TestReview)
        .options(selectinload(TestReview.reviewed_by))
        .where(TestReview.lab_test_id == test_id)
        .order_by(TestReview.reviewed_at.desc())
    )
    res = await db.scalars(stmt)
    return list(res.all())
