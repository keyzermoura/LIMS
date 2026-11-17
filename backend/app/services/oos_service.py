"""Serviço de Investigação de Desvios Analíticos OOS e OOT (Sprint 7.2).

Implementa os fluxos formais de conformidade regulatória:
- Fase I: Investigação Laboratorial Imediata (checagem de cálculos, instrumentos, insumos).
- Fase II: Amostragem, Re-ensaio e Determinação de Causa Raiz (FDA Guidance / ISO 17025 §7.10).
- Vínculo obrigatório com o módulo de Ações Corretivas e Preventivas (CAPA).
- Trilha de auditoria ALCOA+ e intertravamento em laudos oficiais.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.context import RequestContext
from app.db.dialect import next_sequence
from app.models.base import utcnow
from app.models.capa_action import CapaAction
from app.models.enums import (
    AuditAction,
    AuditEntity,
    CapaSourceType,
    CapaStatus,
    DeviationType,
    OOSInvestigationStatus,
)
from app.models.lab_test import LabTest
from app.models.oos_investigation import OOSInvestigation
from app.models.test_execution import TestExecution
from app.models.user import User
from app.schemas.oos_investigation import (
    OOSCloseRequest,
    OOSInvestigationCreate,
    OOSPhase1Update,
    OOSPhase2Update,
)
from app.services import audit_service, outbox_service


async def create_investigation(
    db: AsyncSession,
    *,
    payload: OOSInvestigationCreate,
    actor: User,
    context: RequestContext,
) -> OOSInvestigation:
    """Abre formalmente uma investigação de desvio analítico OOS/OOT."""
    lab_test = await db.get(LabTest, payload.lab_test_id)
    if not lab_test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ensaio laboratorial não encontrado.",
        )

    execution: TestExecution | None = None
    if payload.execution_id:
        execution = await db.get(TestExecution, payload.execution_id)
        if not execution or execution.lab_test_id != lab_test.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A execução informada não pertence ao ensaio indicado.",
            )

    # Gera número sequencial anual OOS-YYYY-XXXX
    seq = await next_sequence(db, "oos_investigation_seq")
    year = utcnow().year
    investigation_number = f"OOS-{year}-{int(seq):04d}"

    # Preenche dados padrão a partir do ensaio/execução se não fornecidos
    initial_res = (
        payload.initial_result
        if payload.initial_result is not None
        else (execution.result_value if execution else lab_test.result_value)
    )
    initial_text = (
        payload.initial_result_text
        if payload.initial_result_text is not None
        else (execution.result_text if execution else lab_test.result_text)
    )
    spec_min = (
        payload.specification_min if payload.specification_min is not None else lab_test.lower_limit
    )
    spec_max = (
        payload.specification_max if payload.specification_max is not None else lab_test.upper_limit
    )
    spec_text = payload.specification_text

    investigation = OOSInvestigation(
        investigation_number=investigation_number,
        lab_test_id=lab_test.id,
        execution_id=execution.id if execution else None,
        deviation_type=payload.deviation_type,
        status=OOSInvestigationStatus.PHASE_I_PENDING,
        initial_result=initial_res,
        initial_result_text=initial_text,
        specification_min=spec_min,
        specification_max=spec_max,
        specification_text=spec_text,
        detected_by_id=actor.id,
        detected_at=utcnow(),
        phase_1_checklist={},
        phase_2_required=False,
        phase_2_retest_results=[],
    )
    db.add(investigation)
    await db.flush()

    await audit_service.append(
        db,
        action=AuditAction.CREATE,
        entity_type=AuditEntity.OOS_INVESTIGATION.value,
        entity_id=investigation.id,
        new_value=audit_service.snapshot(investigation),
        reason=(
            f"Abertura formal de investigação {investigation.deviation_type.value} "
            f"#{investigation.investigation_number} para o ensaio {lab_test.name}."
        ),
        context=context,
    )

    await outbox_service.enqueue_event(
        db,
        event_type="oos.opened",
        aggregate_type="OOSInvestigation",
        aggregate_id=str(investigation.id),
        payload={
            "investigation_id": str(investigation.id),
            "investigation_number": investigation.investigation_number,
            "lab_test_id": str(investigation.lab_test_id),
            "deviation_type": investigation.deviation_type.value,
            "status": investigation.status.value,
            "detected_at": investigation.detected_at.isoformat(),
        },
    )

    await db.commit()
    return await get_investigation(db, investigation.id)


async def record_phase_1(
    db: AsyncSession,
    *,
    investigation_id: UUID,
    payload: OOSPhase1Update,
    actor: User,
    context: RequestContext,
) -> OOSInvestigation:
    """Conclui a Fase I (Investigação Laboratorial Imediata) conforme FDA Guidance."""
    investigation = await get_investigation(db, investigation_id)
    if investigation.status not in (
        OOSInvestigationStatus.PHASE_I_PENDING,
        OOSInvestigationStatus.PHASE_I_COMPLETED,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Investigação no status '{investigation.status.value}' não permite edição da Fase I.",
        )

    old_snapshot = audit_service.snapshot(investigation)

    checklist_data = {
        "calculation_verified": payload.calculation_verified,
        "instrument_verified": payload.instrument_verified,
        "reagent_verified": payload.reagent_verified,
        "analyst_interviewed": payload.analyst_interviewed,
        "sample_integrity_verified": payload.sample_integrity_verified,
        "checklist_notes": payload.checklist_notes,
    }

    investigation.phase_1_checklist = checklist_data
    investigation.phase_1_conclusion = payload.phase_1_conclusion.strip()
    investigation.phase_1_completed_at = utcnow()
    investigation.phase_1_responsible_id = actor.id
    investigation.phase_2_required = payload.phase_2_required

    # Determinação do novo status
    if payload.phase_2_required:
        investigation.status = OOSInvestigationStatus.PHASE_II_REQUIRED
    else:
        # Se não requer Fase II, verifica se foi erro de laboratório inequívoco
        all_checks_passed = (
            payload.calculation_verified
            and payload.instrument_verified
            and payload.reagent_verified
            and payload.analyst_interviewed
            and payload.sample_integrity_verified
        )
        if not all_checks_passed:
            investigation.status = OOSInvestigationStatus.CONFIRMED_LAB_ERROR
        else:
            investigation.status = OOSInvestigationStatus.PHASE_I_COMPLETED

    await audit_service.append(
        db,
        action=AuditAction.UPDATE,
        entity_type=AuditEntity.OOS_INVESTIGATION.value,
        entity_id=investigation.id,
        old_value=old_snapshot,
        new_value=audit_service.snapshot(investigation),
        reason=(
            f"Conclusão da Fase I da investigação #{investigation.investigation_number}: "
            f"Fase II requerida = {investigation.phase_2_required}."
        ),
        context=context,
    )
    await db.commit()
    return await get_investigation(db, investigation.id)


async def record_phase_2(
    db: AsyncSession,
    *,
    investigation_id: UUID,
    payload: OOSPhase2Update,
    actor: User,
    context: RequestContext,
) -> OOSInvestigation:
    """Conclui a Fase II (Amostragem / Re-ensaio / Causa Raiz) e vincula ou cria CAPA."""
    investigation = await get_investigation(db, investigation_id)
    if investigation.status not in (
        OOSInvestigationStatus.PHASE_II_REQUIRED,
        OOSInvestigationStatus.PHASE_I_COMPLETED,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Investigação no status '{investigation.status.value}' não está apta para conclusão da Fase II.",
        )

    if payload.confirmed_status not in (
        OOSInvestigationStatus.CONFIRMED_LAB_ERROR,
        OOSInvestigationStatus.CONFIRMED_PRODUCT_FAILURE,
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="O status final da Fase II deve ser CONFIRMED_LAB_ERROR ou CONFIRMED_PRODUCT_FAILURE.",
        )

    old_snapshot = audit_service.snapshot(investigation)

    investigation.phase_2_plan = payload.phase_2_plan.strip()
    investigation.phase_2_retest_results = [r.model_dump() for r in payload.retest_results]
    investigation.root_cause_category = payload.root_cause_category
    investigation.root_cause_description = payload.root_cause_description.strip()
    investigation.status = payload.confirmed_status

    # Gerenciamento de CAPA (ISO 17025 §8.7 / §7.10)
    capa_id = payload.capa_action_id
    if payload.auto_create_capa or (
        capa_id is None
        and payload.confirmed_status == OOSInvestigationStatus.CONFIRMED_PRODUCT_FAILURE
    ):
        lab_test = investigation.lab_test
        capa_seq = await next_sequence(db, "capa_code_seq")
        year = utcnow().year
        capa_code = f"CAPA-{year}-{int(capa_seq):06d}"

        due_date = date.today() + timedelta(days=30)
        new_capa = CapaAction(
            code=capa_code,
            device_sample_id=lab_test.device_sample_id,
            lab_test_id=lab_test.id,
            title=f"Ação Corretiva para {investigation.investigation_number} ({investigation.deviation_type.value})",
            source_type=CapaSourceType.ENSAIO_REPROVADO,
            status=CapaStatus.ABERTA,
            due_date=due_date,
            auto_opened=True,
            root_cause=(
                f"[{payload.root_cause_category.value}] {payload.root_cause_description.strip()}"
            ),
            action_plan=(
                f"Plano investigativo Fase II executado sob {investigation.investigation_number}. "
                f"Implementar contenção do lote e revisão dos controles operacionais."
            ),
            owner_id=actor.id,
            created_by_id=actor.id,
        )
        db.add(new_capa)
        await db.flush()
        capa_id = new_capa.id

        await audit_service.append(
            db,
            action=AuditAction.CREATE,
            entity_type=AuditEntity.CAPA_ACTION.value,
            entity_id=new_capa.id,
            new_value=audit_service.snapshot(new_capa),
            reason=f"Abertura automática de CAPA via investigação {investigation.investigation_number}.",
            context=context,
        )

    investigation.capa_action_id = capa_id

    await audit_service.append(
        db,
        action=AuditAction.UPDATE,
        entity_type=AuditEntity.OOS_INVESTIGATION.value,
        entity_id=investigation.id,
        old_value=old_snapshot,
        new_value=audit_service.snapshot(investigation),
        reason=(
            f"Conclusão da Fase II da investigação #{investigation.investigation_number}: "
            f"Classificação={investigation.status.value}, Causa Raiz={investigation.root_cause_category.value}."
        ),
        context=context,
    )
    await db.commit()
    return await get_investigation(db, investigation.id)


async def close_investigation(
    db: AsyncSession,
    *,
    investigation_id: UUID,
    payload: OOSCloseRequest,
    actor: User,
    context: RequestContext,
) -> OOSInvestigation:
    """Encerra formalmente a investigação de desvio analítico."""
    investigation = await get_investigation(db, investigation_id)
    if investigation.status == OOSInvestigationStatus.CLOSED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A investigação já se encontra encerrada.",
        )

    old_snapshot = audit_service.snapshot(investigation)

    investigation.final_disposition = payload.final_disposition.strip()
    investigation.status = OOSInvestigationStatus.CLOSED
    investigation.closed_at = utcnow()
    investigation.closed_by_id = actor.id

    await audit_service.append(
        db,
        action=AuditAction.STATUS_CHANGE,
        entity_type=AuditEntity.OOS_INVESTIGATION.value,
        entity_id=investigation.id,
        old_value=old_snapshot,
        new_value=audit_service.snapshot(investigation),
        reason=f"Encerramento formal da investigação #{investigation.investigation_number}.",
        context=context,
    )
    await db.commit()
    return await get_investigation(db, investigation.id)


async def get_investigation(db: AsyncSession, investigation_id: UUID) -> OOSInvestigation:
    """Busca investigação OOS detalhada com relacionamentos carregados."""
    stmt = (
        select(OOSInvestigation)
        .options(
            selectinload(OOSInvestigation.lab_test),
            selectinload(OOSInvestigation.execution),
            selectinload(OOSInvestigation.detected_by),
            selectinload(OOSInvestigation.phase_1_responsible),
            selectinload(OOSInvestigation.closed_by),
            selectinload(OOSInvestigation.capa_action),
        )
        .where(OOSInvestigation.id == investigation_id)
    )
    investigation = await db.scalar(stmt)
    if not investigation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investigação de desvio analítico não encontrada.",
        )
    return investigation


async def list_investigations(
    db: AsyncSession,
    *,
    lab_test_id: UUID | None = None,
    status_filter: OOSInvestigationStatus | None = None,
    deviation_type: DeviationType | None = None,
    is_open: bool | None = None,
    search: str | None = None,
) -> Sequence[OOSInvestigation]:
    """Lista investigações de desvios com filtros analíticos."""
    stmt = (
        select(OOSInvestigation)
        .options(
            selectinload(OOSInvestigation.lab_test),
            selectinload(OOSInvestigation.execution),
            selectinload(OOSInvestigation.detected_by),
            selectinload(OOSInvestigation.phase_1_responsible),
            selectinload(OOSInvestigation.closed_by),
            selectinload(OOSInvestigation.capa_action),
        )
        .order_by(OOSInvestigation.created_at.desc())
    )

    if lab_test_id:
        stmt = stmt.where(OOSInvestigation.lab_test_id == lab_test_id)

    if status_filter:
        stmt = stmt.where(OOSInvestigation.status == status_filter)

    if deviation_type:
        stmt = stmt.where(OOSInvestigation.deviation_type == deviation_type)

    if is_open is not None:
        if is_open:
            stmt = stmt.where(OOSInvestigation.status != OOSInvestigationStatus.CLOSED)
        else:
            stmt = stmt.where(OOSInvestigation.status == OOSInvestigationStatus.CLOSED)

    if search:
        s = f"%{search.strip()}%"
        stmt = stmt.where(OOSInvestigation.investigation_number.ilike(s))

    result = await db.scalars(stmt)
    return result.all()
