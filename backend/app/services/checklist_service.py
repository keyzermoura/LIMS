"""Serviço de Checklist, Critérios Regulatórios e Respostas de Conferência (Fase 1 / M1.2)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.context import RequestContext
from app.core.errors import NotFoundError, ValidationDomainError
from app.models.checklist import ChecklistAnswer, ChecklistCriterion, ChecklistTemplate
from app.models.enums import (
    AuditAction,
    AuditEntity,
    ChecklistResult,
    ConferenceStatus,
    CriterionClass,
)
from app.models.receipt import ReceiptItem
from app.models.user import User
from app.schemas.checklist import ChecklistAnswerCreate
from app.services import audit_service

DEFAULT_TEMPLATES_SPEC: list[dict[str, Any]] = [
    {
        "code": "CKL-DISP-GERAL",
        "name": "Checklist Geral de Recebimento de Dispositivos Médicos",
        "category": "Dispositivo Médico",
        "version": 1,
        "criteria": [
            {
                "code": "E01",
                "description": "Integridade física da embalagem primária e do lacre oficial de fiscalização",
                "criterion_class": CriterionClass.ELIMINATORIO,
                "is_mandatory": True,
                "order": 1,
            },
            {
                "code": "E02",
                "description": "Presença de identificação inequívoca de fabricante, lote e/ou número de série",
                "criterion_class": CriterionClass.ELIMINATORIO,
                "is_mandatory": True,
                "order": 2,
            },
            {
                "code": "S01",
                "description": "Conformidade entre quantidade física apresentada e quantidade declarada na solicitação",
                "criterion_class": CriterionClass.SANEAVEL,
                "is_mandatory": True,
                "order": 3,
            },
            {
                "code": "S02",
                "description": "Acondicionamento e integridade das instruções de uso e rotulagem",
                "criterion_class": CriterionClass.SANEAVEL,
                "is_mandatory": True,
                "order": 4,
            },
            {
                "code": "I01",
                "description": "Registro fotográfico das condições de chegada e embalagem secundária",
                "criterion_class": CriterionClass.INFORMATIVO,
                "is_mandatory": False,
                "order": 5,
            },
        ],
    }
]


async def ensure_default_templates(db: AsyncSession) -> None:
    """Garante a existência de templates padrão de checklist."""
    for spec in DEFAULT_TEMPLATES_SPEC:
        existing = await db.scalar(
            select(ChecklistTemplate).where(ChecklistTemplate.code == spec["code"])
        )
        if existing is None:
            template = ChecklistTemplate(
                code=spec["code"],
                name=spec["name"],
                category=spec["category"],
                version=spec["version"],
                is_active=True,
            )
            for crit_data in spec["criteria"]:
                criterion = ChecklistCriterion(
                    code=crit_data["code"],
                    description=crit_data["description"],
                    criterion_class=crit_data["criterion_class"],
                    is_mandatory=crit_data["is_mandatory"],
                    order=crit_data["order"],
                )
                template.criteria.append(criterion)
            db.add(template)
    await db.commit()


async def list_templates(
    db: AsyncSession,
    *,
    category: str | None = None,
    only_active: bool = True,
) -> list[ChecklistTemplate]:
    """Lista templates cadastrados, garantindo sementes se banco estiver vazio."""
    await ensure_default_templates(db)
    stmt = select(ChecklistTemplate).options(selectinload(ChecklistTemplate.criteria))
    if only_active:
        stmt = stmt.where(ChecklistTemplate.is_active.is_(True))
    if category:
        stmt = stmt.where(ChecklistTemplate.category == category)
    stmt = stmt.order_by(ChecklistTemplate.code.asc())
    result = await db.scalars(stmt)
    return list(result.all())


async def get_template(db: AsyncSession, template_id: UUID) -> ChecklistTemplate:
    """Retorna template por ID com critérios ordenados ou 404."""
    stmt = (
        select(ChecklistTemplate)
        .options(selectinload(ChecklistTemplate.criteria))
        .where(ChecklistTemplate.id == template_id)
    )
    template = await db.scalar(stmt)
    if template is None:
        raise NotFoundError("Template de checklist não encontrado.")
    return template


async def submit_checklist_answers(
    db: AsyncSession,
    receipt_item_id: UUID,
    answers_payload: list[ChecklistAnswerCreate],
    *,
    actor: User,
    context: RequestContext | None = None,
) -> tuple[list[ChecklistAnswer], ConferenceStatus, int]:
    """Registra as respostas do checklist, avalia a conformidade regulatória e atualiza o item."""
    stmt = (
        select(ReceiptItem)
        .options(
            selectinload(ReceiptItem.checklist_answers),
            selectinload(ReceiptItem.receipt),
        )
        .where(ReceiptItem.id == receipt_item_id)
    )
    receipt_item = await db.scalar(stmt)
    if receipt_item is None:
        raise NotFoundError("Item de recebimento não encontrado.")

    # Remove respostas prévias para substituição idempotente
    receipt_item.checklist_answers.clear()
    await db.flush()

    saved_answers: list[ChecklistAnswer] = []
    has_eliminatory_failure = False
    has_remediable_failure = False

    for item_ans in answers_payload:
        criterion = await db.get(ChecklistCriterion, item_ans.criterion_id)
        if criterion is None:
            raise NotFoundError(f"Critério {item_ans.criterion_id} não encontrado.")

        if criterion.is_mandatory and item_ans.result == ChecklistResult.NAO_APLICAVEL:
            raise ValidationDomainError(
                f"O critério obrigatório '{criterion.code}' não pode ser respondido como NÃO APLICÁVEL."
            )

        if item_ans.result == ChecklistResult.NAO_CONFORME and not item_ans.justification:
            raise ValidationDomainError(
                f"Justificativa obrigatória para o critério não conforme '{criterion.code}'."
            )

        if item_ans.result == ChecklistResult.NAO_CONFORME:
            if criterion.criterion_class == CriterionClass.ELIMINATORIO:
                has_eliminatory_failure = True
            elif criterion.criterion_class == CriterionClass.SANEAVEL:
                has_remediable_failure = True

        answer = ChecklistAnswer(
            receipt_item_id=receipt_item.id,
            criterion_id=criterion.id,
            result=item_ans.result,
            justification=item_ans.justification,
            evaluated_by_id=actor.id,
        )
        receipt_item.checklist_answers.append(answer)
        saved_answers.append(answer)

    # Avaliação do status de conferência derivado
    if has_eliminatory_failure:
        derived_status = ConferenceStatus.NAO_CONFORME
    elif has_remediable_failure:
        derived_status = ConferenceStatus.COM_RESSALVA
    else:
        derived_status = ConferenceStatus.CONFORME

    receipt_item.conference_status = derived_status
    receipt_item.version += 1

    new_snapshot = {
        "receipt_item_id": str(receipt_item.id),
        "conference_status": derived_status.value,
        "answers_count": len(saved_answers),
    }

    audit_entry = await audit_service.append(
        db,
        action=AuditAction.UPDATE,
        entity_type=AuditEntity.CHECKLIST.value,
        entity_id=receipt_item.id,
        actor=actor,
        new_value=new_snapshot,
        reason=f"Avaliação de checklist concluída: {derived_status.value}",
        context=context,
    )

    await db.commit()

    refreshed_answers = await get_answers_for_item(db, receipt_item_id)
    return refreshed_answers, derived_status, audit_entry.sequence


async def get_answers_for_item(
    db: AsyncSession, receipt_item_id: UUID
) -> list[ChecklistAnswer]:
    """Retorna respostas de checklist vinculadas ao item com critérios carregados."""
    stmt = (
        select(ChecklistAnswer)
        .options(
            selectinload(ChecklistAnswer.criterion),
            selectinload(ChecklistAnswer.evaluated_by),
        )
        .where(ChecklistAnswer.receipt_item_id == receipt_item_id)
        .order_by(ChecklistAnswer.created_at.asc())
    )
    result = await db.scalars(stmt)
    return list(result.all())
