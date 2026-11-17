"""Serviço de CAPA (Gestão de Não Conformidades, Ações Corretivas e Eficácia - ISO/IEC 17025 §8.7)."""

from __future__ import annotations

from datetime import date
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.errors import ConflictError, ForbiddenError, NotFoundError, ValidationDomainError
from app.db.dialect import next_sequence
from app.models.base import utcnow
from app.models.capa_action import CapaAction
from app.models.capa_action_item import CapaActionItem
from app.models.device_sample import DeviceSample
from app.models.electronic_signature import ElectronicSignature
from app.models.enums import (
    AuditAction,
    AuditEntity,
    CapaEffectivenessStatus,
    CapaItemStatus,
    CapaSourceType,
    CapaStatus,
    UserRole,
)
from app.models.lab_test import LabTest
from app.models.uncertainty import UncertaintyBudget
from app.models.user import User
from app.schemas.capa import (
    CapaActionItemCreate,
    CapaActionItemUpdate,
    CapaCreate,
    CapaEffectivenessEvaluationIn,
    CapaUpdate,
)
from app.services import audit_service, signature_service

FINAL_STATUSES = {CapaStatus.CONCLUIDA, CapaStatus.CANCELADA}
EDITOR_ROLES = {UserRole.ADMIN, UserRole.FISCAL}
OWNER_ROLES = {UserRole.ADMIN, UserRole.FISCAL, UserRole.TECNICO}


async def create_capa(
    db: AsyncSession,
    *,
    payload: CapaCreate,
    actor: User,
    signature: ElectronicSignature,
    context: RequestContext,
) -> tuple[CapaAction, int]:
    if (
        payload.device_sample_id is not None
        and await db.get(DeviceSample, payload.device_sample_id) is None
    ):
        raise NotFoundError("Amostra de origem não encontrada.")

    if payload.lab_test_id is not None:
        lab_test = await db.get(LabTest, payload.lab_test_id)
        if lab_test is None:
            raise NotFoundError("Ensaio de origem não encontrado.")
        if (
            payload.device_sample_id is not None
            and lab_test.device_sample_id != payload.device_sample_id
        ):
            raise ValidationDomainError(
                "O ensaio informado não pertence à amostra de origem da CAPA."
            )

    owner = await db.get(User, payload.owner_id)
    if owner is None or not owner.is_active:
        raise NotFoundError("Responsável pela CAPA não encontrado ou inativo.")
    if owner.role not in OWNER_ROLES:
        raise ValidationDomainError(
            f"O perfil {owner.role.value} não pode ser responsável por uma CAPA."
        )

    if payload.due_date <= date.today():
        raise ValidationDomainError("O prazo da CAPA deve ser uma data futura.")

    if payload.target_effectiveness_date and payload.target_effectiveness_date <= payload.due_date:
        raise ValidationDomainError(
            "A data de avaliação de eficácia deve ser posterior ao prazo de conclusão do plano de ação."
        )

    if await db.get(CapaAction, payload.id) is not None:
        raise ConflictError("Já existe uma CAPA com o identificador informado.")

    sequence = await next_sequence(db, "capa_code_seq")
    capa = CapaAction(
        id=payload.id,
        code=f"CAPA-{utcnow().year}-{int(sequence):06d}",
        device_sample_id=payload.device_sample_id,
        lab_test_id=payload.lab_test_id,
        source_type=payload.source_type,
        title=payload.title.strip(),
        containment_action=payload.containment_action.strip()
        if payload.containment_action
        else None,
        ishikawa_causes=payload.ishikawa_causes,
        five_whys=payload.five_whys,
        root_cause=payload.root_cause.strip(),
        action_plan=payload.action_plan.strip(),
        owner_id=owner.id,
        owner=owner,
        status=CapaStatus.ABERTA,
        due_date=payload.due_date,
        target_effectiveness_date=payload.target_effectiveness_date,
        effectiveness_status=CapaEffectivenessStatus.PENDENTE,
        auto_opened=False,
        created_by_id=actor.id,
        signature_id=signature.id,
    )
    db.add(capa)
    await db.flush()

    if payload.action_items:
        for item_data in payload.action_items:
            assigned = await db.get(User, item_data.assigned_to_id)
            if assigned is None or not assigned.is_active:
                raise NotFoundError(f"Usuário atribuído {item_data.assigned_to_id} não encontrado.")
            item = CapaActionItem(
                id=uuid4(),
                capa_id=capa.id,
                title=item_data.title.strip(),
                description=item_data.description.strip(),
                action_type=item_data.action_type,
                assigned_to_id=assigned.id,
                due_date=item_data.due_date,
                status=CapaItemStatus.PENDENTE,
            )
            db.add(item)
        await db.flush()

    await signature_service.bind_record(db, signature, {"capa": audit_service.snapshot(capa)})

    log = await audit_service.append(
        db,
        action=AuditAction.CREATE,
        entity_type=AuditEntity.CAPA_ACTION.value,
        entity_id=capa.id,
        actor=actor,
        new_value=audit_service.snapshot(capa),
        reason="Abertura manual de CAPA com análise de causa raiz.",
        context=context,
        signature_id=signature.id,
    )
    await db.commit()

    refreshed = await db.scalar(select(CapaAction).where(CapaAction.id == capa.id))
    assert refreshed is not None
    return refreshed, log.id


async def update_capa(
    db: AsyncSession,
    *,
    capa_id: UUID,
    payload: CapaUpdate,
    actor: User,
    signature: ElectronicSignature,
    context: RequestContext,
) -> tuple[CapaAction, int]:
    capa = await db.scalar(select(CapaAction).where(CapaAction.id == capa_id).with_for_update())
    if capa is None:
        raise NotFoundError("CAPA não encontrada.")

    if capa.version != payload.version:
        raise ConflictError(
            "A CAPA foi alterada por outro usuário. Recarregue antes de prosseguir.",
            details={"current_version": capa.version},
        )

    if capa.status in FINAL_STATUSES:
        raise ConflictError("CAPA concluída ou cancelada não pode ser editada.")

    if actor.role not in EDITOR_ROLES and capa.owner_id != actor.id:
        raise ForbiddenError("Somente o responsável pela CAPA (ou gestão) pode alterá-la.")

    old_values = audit_service.snapshot(capa)

    if payload.status == CapaStatus.CONCLUIDA:
        if not payload.effectiveness_check and not capa.effectiveness_check:
            raise ValidationDomainError("Para concluir a CAPA, registre a verificação de eficácia.")
        # Verifica se todas as ações estão concluídas ou canceladas
        pending_items = await db.scalars(
            select(CapaActionItem).where(
                CapaActionItem.capa_id == capa.id,
                CapaActionItem.status.in_([CapaItemStatus.PENDENTE, CapaItemStatus.EM_ANDAMENTO]),
            )
        )
        if list(pending_items):
            raise ValidationDomainError(
                "Não é possível concluir a CAPA enquanto houver ações pendentes ou em andamento."
            )
        capa.closed_at = utcnow()
        capa.closed_by_id = actor.id
    elif payload.status == CapaStatus.CANCELADA:
        capa.closed_at = utcnow()
        capa.closed_by_id = actor.id

    if payload.owner_id is not None:
        new_owner = await db.get(User, payload.owner_id)
        if new_owner is None or not new_owner.is_active:
            raise NotFoundError("Novo responsável não encontrado ou inativo.")
        if new_owner.role not in OWNER_ROLES:
            raise ValidationDomainError(
                f"O perfil {new_owner.role.value} não pode ser responsável por uma CAPA."
            )
        capa.owner_id = new_owner.id
        capa.owner = new_owner

    if (
        payload.due_date is not None
        and payload.due_date != capa.due_date
        and payload.due_date <= date.today()
    ):
        raise ValidationDomainError("O prazo da CAPA deve ser uma data futura.")

    capa.signature_id = signature.id

    changes = payload.model_dump(exclude_unset=True, exclude={"version"})
    for field, value in changes.items():
        if value is not None:
            setattr(capa, field, value)

    capa.version += 1
    capa.updated_at = utcnow()
    await db.flush()

    await signature_service.bind_record(
        db, signature, {"capa": audit_service.snapshot(capa), "changes": changes}
    )

    log = await audit_service.append(
        db,
        action=AuditAction.UPDATE,
        entity_type=AuditEntity.CAPA_ACTION.value,
        entity_id=capa.id,
        actor=actor,
        old_value=old_values,
        new_value=audit_service.snapshot(capa),
        reason="Atualização de CAPA.",
        context=context,
        signature_id=signature.id,
    )
    await db.commit()

    refreshed = await db.scalar(select(CapaAction).where(CapaAction.id == capa.id))
    assert refreshed is not None
    return refreshed, log.id


async def add_action_item(
    db: AsyncSession,
    *,
    capa_id: UUID,
    payload: CapaActionItemCreate,
    actor: User,
    context: RequestContext,
) -> tuple[CapaActionItem, int]:
    capa = await db.get(CapaAction, capa_id)
    if capa is None:
        raise NotFoundError("CAPA não encontrada.")
    if capa.status in FINAL_STATUSES:
        raise ConflictError("Não é possível adicionar ações a uma CAPA finalizada.")
    if actor.role not in EDITOR_ROLES and capa.owner_id != actor.id:
        raise ForbiddenError("Somente o responsável pela CAPA (ou gestão) pode incluir ações.")

    assigned = await db.get(User, payload.assigned_to_id)
    if assigned is None or not assigned.is_active:
        raise NotFoundError("Usuário atribuído não encontrado ou inativo.")

    item = CapaActionItem(
        id=uuid4(),
        capa_id=capa.id,
        title=payload.title.strip(),
        description=payload.description.strip(),
        action_type=payload.action_type,
        assigned_to_id=assigned.id,
        due_date=payload.due_date,
        status=CapaItemStatus.PENDENTE,
    )
    db.add(item)
    await db.flush()

    log = await audit_service.append(
        db,
        action=AuditAction.CREATE,
        entity_type=AuditEntity.CAPA_ACTION_ITEM.value,
        entity_id=item.id,
        actor=actor,
        new_value=audit_service.snapshot(item),
        reason=f"Inclusão de ação {item.action_type.value} na CAPA {capa.code}.",
        context=context,
    )
    await db.commit()
    refreshed = await db.scalar(select(CapaActionItem).where(CapaActionItem.id == item.id))
    assert refreshed is not None
    return refreshed, log.id


async def update_action_item(
    db: AsyncSession,
    *,
    capa_id: UUID,
    item_id: UUID,
    payload: CapaActionItemUpdate,
    actor: User,
    context: RequestContext,
) -> tuple[CapaActionItem, int]:
    item = await db.scalar(
        select(CapaActionItem).where(
            CapaActionItem.id == item_id,
            CapaActionItem.capa_id == capa_id,
        )
    )
    if item is None:
        raise NotFoundError("Item de ação não encontrado.")

    capa = await db.get(CapaAction, capa_id)
    assert capa is not None
    if capa.status in FINAL_STATUSES:
        raise ConflictError("Não é possível modificar ações de uma CAPA finalizada.")

    if (
        actor.role not in EDITOR_ROLES
        and capa.owner_id != actor.id
        and item.assigned_to_id != actor.id
    ):
        raise ForbiddenError(
            "Somente o responsável pela ação, dono da CAPA ou gestão pode editá-la."
        )

    old_values = audit_service.snapshot(item)

    if payload.status == CapaItemStatus.CONCLUIDA:
        if not payload.completion_evidence and not item.completion_evidence:
            raise ValidationDomainError("Para concluir a ação, informe a evidência de conclusão.")
        item.completed_at = utcnow()
    elif payload.status == CapaItemStatus.CANCELADA:
        item.completed_at = utcnow()

    if payload.assigned_to_id is not None:
        new_assigned = await db.get(User, payload.assigned_to_id)
        if new_assigned is None or not new_assigned.is_active:
            raise NotFoundError("Novo responsável atribuído não encontrado.")
        item.assigned_to_id = new_assigned.id

    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        if value is not None and field != "assigned_to_id":
            setattr(item, field, value)

    item.updated_at = utcnow()
    await db.flush()

    log = await audit_service.append(
        db,
        action=AuditAction.UPDATE,
        entity_type=AuditEntity.CAPA_ACTION_ITEM.value,
        entity_id=item.id,
        actor=actor,
        old_value=old_values,
        new_value=audit_service.snapshot(item),
        reason=f"Atualização do item de ação {item.id} na CAPA {capa.code}.",
        context=context,
    )
    await db.commit()
    refreshed = await db.scalar(select(CapaActionItem).where(CapaActionItem.id == item.id))
    assert refreshed is not None
    return refreshed, log.id


async def delete_action_item(
    db: AsyncSession,
    *,
    capa_id: UUID,
    item_id: UUID,
    actor: User,
    context: RequestContext,
) -> int:
    item = await db.scalar(
        select(CapaActionItem).where(
            CapaActionItem.id == item_id,
            CapaActionItem.capa_id == capa_id,
        )
    )
    if item is None:
        raise NotFoundError("Item de ação não encontrado.")

    capa = await db.get(CapaAction, capa_id)
    assert capa is not None
    if capa.status in FINAL_STATUSES:
        raise ConflictError("Não é possível remover ações de uma CAPA finalizada.")
    if actor.role not in EDITOR_ROLES and capa.owner_id != actor.id:
        raise ForbiddenError("Somente o responsável pela CAPA ou gestão pode remover ações.")

    if item.status != CapaItemStatus.PENDENTE:
        raise ValidationDomainError("Apenas ações com status PENDENTE podem ser removidas.")

    old_values = audit_service.snapshot(item)
    await db.delete(item)
    await db.flush()

    log = await audit_service.append(
        db,
        action=AuditAction.DELETE,
        entity_type=AuditEntity.CAPA_ACTION_ITEM.value,
        entity_id=item.id,
        actor=actor,
        old_value=old_values,
        reason=f"Remoção de ação pendente da CAPA {capa.code}.",
        context=context,
    )
    await db.commit()
    return log.id


async def evaluate_effectiveness(
    db: AsyncSession,
    *,
    capa_id: UUID,
    payload: CapaEffectivenessEvaluationIn,
    actor: User,
    signature: ElectronicSignature,
    context: RequestContext,
) -> tuple[CapaAction, CapaAction | None, int]:
    """Avaliação formal de eficácia temporal (ISO/IEC 17025:2017 §8.7.3)."""
    capa = await db.scalar(select(CapaAction).where(CapaAction.id == capa_id).with_for_update())
    if capa is None:
        raise NotFoundError("CAPA não encontrada.")
    if capa.status == CapaStatus.CANCELADA:
        raise ConflictError("Não é possível avaliar eficácia de uma CAPA cancelada.")

    if actor.role not in EDITOR_ROLES and capa.owner_id != actor.id:
        raise ForbiddenError(
            "Somente o responsável pela CAPA ou gestão da qualidade pode avaliar eficácia."
        )

    # Verifica se existem ações pendentes ou em andamento
    pending_items = await db.scalars(
        select(CapaActionItem).where(
            CapaActionItem.capa_id == capa.id,
            CapaActionItem.status.in_([CapaItemStatus.PENDENTE, CapaItemStatus.EM_ANDAMENTO]),
        )
    )
    if list(pending_items):
        raise ValidationDomainError(
            "Todas as ações do plano devem estar concluídas ou canceladas antes da avaliação de eficácia."
        )

    old_values = audit_service.snapshot(capa)
    now = utcnow()

    capa.effectiveness_status = payload.effectiveness_status
    capa.effectiveness_evaluator_id = actor.id
    capa.effectiveness_evaluated_at = now
    capa.recurrence_detected = payload.recurrence_detected
    capa.effectiveness_check = payload.justification.strip()
    capa.signature_id = signature.id
    capa.version += 1
    capa.updated_at = now

    new_derived_capa: CapaAction | None = None

    if (
        payload.effectiveness_status == CapaEffectivenessStatus.EFICAZ
        and not payload.recurrence_detected
    ):
        capa.status = CapaStatus.CONCLUIDA
        capa.closed_at = now
        capa.closed_by_id = actor.id
    else:
        # Se ineficaz ou reincidente, abre automaticamente nova CAPA de reincidência
        sequence = await next_sequence(db, "capa_code_seq")
        new_derived_capa = CapaAction(
            id=uuid4(),
            code=f"CAPA-{now.year}-{int(sequence):06d}",
            device_sample_id=capa.device_sample_id,
            lab_test_id=capa.lab_test_id,
            source_type=CapaSourceType.AUDITORIA_INTERNA,
            title=f"Reincidência / Ineficácia da {capa.code}: {capa.title}"[:200],
            containment_action="Reavaliação imediata de contenção após falha na eficácia anterior.",
            root_cause=f"Ineficácia detectada na CAPA anterior ({capa.code}). Justificativa: {payload.justification}",
            action_plan="Reabertura do ciclo de análise de causa raiz e novos planos de ação corretiva.",
            owner_id=capa.owner_id,
            owner=capa.owner,
            status=CapaStatus.ABERTA,
            due_date=date.fromordinal(date.today().toordinal() + 30),
            auto_opened=True,
            created_by_id=actor.id,
            opened_at=now,
        )
        db.add(new_derived_capa)

    await db.flush()

    await signature_service.bind_record(
        db,
        signature,
        {
            "capa": audit_service.snapshot(capa),
            "effectiveness_status": payload.effectiveness_status.value,
            "recurrence_detected": payload.recurrence_detected,
            "derived_capa_id": str(new_derived_capa.id) if new_derived_capa else None,
        },
    )

    log = await audit_service.append(
        db,
        action=AuditAction.UPDATE,
        entity_type=AuditEntity.CAPA_ACTION.value,
        entity_id=capa.id,
        actor=actor,
        old_value=old_values,
        new_value=audit_service.snapshot(capa),
        reason=f"Avaliação formal de eficácia temporal da CAPA {capa.code} ({payload.effectiveness_status.value}).",
        context=context,
        signature_id=signature.id,
    )
    await db.commit()

    refreshed = await db.scalar(select(CapaAction).where(CapaAction.id == capa.id))
    assert refreshed is not None
    return refreshed, new_derived_capa, log.id


async def open_capa_from_uncertainty(
    db: AsyncSession,
    *,
    budget: UncertaintyBudget,
    actor: User,
    context: RequestContext,
) -> CapaAction:
    """Gatilho automático de CAPA quando a incerteza metrológica reprova (ISO 17025 §7.6 e §8.7)."""
    now = utcnow()
    sequence = await next_sequence(db, "capa_code_seq")
    code = f"CAPA-{now.year}-{int(sequence):06d}"

    sample_id: UUID | None = None
    if budget.lab_test and budget.lab_test.device_sample_id:
        sample_id = budget.lab_test.device_sample_id

    test_title = (
        budget.lab_test.name if budget.lab_test else f"Ensaio {budget.lab_test_id or budget.id}"
    )

    capa = CapaAction(
        id=uuid4(),
        code=code,
        device_sample_id=sample_id,
        lab_test_id=budget.lab_test_id,
        source_type=CapaSourceType.INCERTEZA_METROLOGICA,
        title=f"Desvio Metrológico (Incerteza): {test_title} - {budget.conformity_status.value}"[
            :200
        ],
        containment_action="Segregação da amostra e suspensão da liberação do resultado metrológico.",
        root_cause=f"Resultado metrológico '{budget.conformity_status.value}' frente aos limites especificados. Declaração: {budget.conformity_statement or 'N/A'}",
        action_plan="Investigar repetibilidade dos ensaios, calibração do instrumento e estabilidade ambiental.",
        owner_id=actor.id,
        owner=actor,
        status=CapaStatus.ABERTA,
        due_date=date.fromordinal(date.today().toordinal() + 30),
        opened_at=now,
        auto_opened=True,
        created_by_id=actor.id,
    )
    db.add(capa)
    await db.flush()

    await audit_service.append(
        db,
        action=AuditAction.CAPA_AUTO_OPEN,
        entity_type=AuditEntity.CAPA_ACTION.value,
        entity_id=capa.id,
        actor=actor,
        new_value=audit_service.snapshot(capa),
        reason=f"Abertura automática de CAPA por desvio metrológico de incerteza ({budget.conformity_status.value}).",
        context=context,
    )
    await db.commit()
    refreshed = await db.scalar(select(CapaAction).where(CapaAction.id == capa.id))
    assert refreshed is not None
    return refreshed


async def get_capa(db: AsyncSession, capa_id: UUID) -> CapaAction:
    capa = await db.scalar(select(CapaAction).where(CapaAction.id == capa_id))
    if capa is None:
        raise NotFoundError("CAPA não encontrada.")
    return capa


async def list_capas(
    db: AsyncSession,
    *,
    status: CapaStatus | None = None,
    source_type: CapaSourceType | None = None,
    sample_id: UUID | None = None,
    page: int = 1,
    size: int = 50,
) -> tuple[list[CapaAction], int]:
    stmt = select(CapaAction)
    if status is not None:
        stmt = stmt.where(CapaAction.status == status)
    if source_type is not None:
        stmt = stmt.where(CapaAction.source_type == source_type)
    if sample_id is not None:
        stmt = stmt.where(CapaAction.device_sample_id == sample_id)

    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    stmt = stmt.order_by(CapaAction.opened_at.desc()).offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)
    return list(result.scalars().all()), int(total)
