"""Serviço de Execução de Ensaios e Gestão de Tentativas de Bancada (Fase 2 / M2.1)."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.context import RequestContext
from app.core.errors import ConflictError, NotFoundError
from app.models.base import utcnow
from app.models.enums import (
    AuditAction,
    AuditEntity,
    ExecutionStatus,
)
from app.models.equipment import LaboratoryEquipment
from app.models.lab_test import LabTest
from app.models.test_execution import TestExecution
from app.models.user import User
from app.schemas.test_execution import (
    TestExecutionComplete,
    TestExecutionInterrupt,
    TestExecutionRecordData,
    TestExecutionStart,
)
from app.services import audit_service, equipment_service


async def get_execution(db: AsyncSession, execution_id: UUID) -> TestExecution:
    execution = await db.scalar(
        select(TestExecution)
        .options(
            selectinload(TestExecution.executed_by),
            selectinload(TestExecution.equipment),
        )
        .where(TestExecution.id == execution_id)
    )
    if execution is None:
        raise NotFoundError("Execução de ensaio não encontrada.")
    return execution


async def list_executions_for_test(
    db: AsyncSession, test_id: UUID
) -> list[TestExecution]:
    test = await db.get(LabTest, test_id)
    if test is None:
        raise NotFoundError("Ensaio laboratorial não encontrado.")

    result = await db.scalars(
        select(TestExecution)
        .options(
            selectinload(TestExecution.executed_by),
            selectinload(TestExecution.equipment),
        )
        .where(TestExecution.lab_test_id == test_id)
        .order_by(TestExecution.execution_number.asc())
    )
    return list(result.all())


async def start_execution(
    db: AsyncSession,
    test_id: UUID,
    *,
    payload: TestExecutionStart,
    actor: User,
    context: RequestContext | None = None,
) -> tuple[TestExecution, int]:
    """Inicia uma nova execução/tentativa de ensaio de bancada com validação metrológica rigorosa."""
    test = await db.scalar(
        select(LabTest).where(LabTest.id == test_id).with_for_update()
    )
    if test is None:
        raise NotFoundError("Ensaio laboratorial não encontrado.")

    if test.is_signed:
        raise ConflictError(
            "Este ensaio já possui laudo assinado eletronicamente. "
            "Para novos testes, proceda via retificação ou novo ensaio."
        )

    # 1. Verifica se já existe execução em andamento para este ensaio
    active_execution = await db.scalar(
        select(TestExecution).where(
            TestExecution.lab_test_id == test_id,
            TestExecution.status == ExecutionStatus.EM_ANDAMENTO,
        )
    )
    if active_execution is not None:
        raise ConflictError(
            f"Já existe a {active_execution.attempt_label} em andamento para este ensaio. "
            "Conclua ou interrompa a tentativa atual antes de iniciar uma nova."
        )

    # 2. Resolução e validação do equipamento
    equipment_to_use_id = payload.equipment_id or test.equipment_id
    equipment_obj: LaboratoryEquipment | None = None
    if equipment_to_use_id is not None:
        equipment_obj = await db.get(LaboratoryEquipment, equipment_to_use_id)
        if equipment_obj is None:
            raise NotFoundError("Equipamento especificado não foi encontrado.")
        # Validação metrológica: bloqueia se vencido ou em manutenção
        equipment_service.validate_equipment_for_use(equipment_obj)
        # Sincroniza no ensaio principal se não estava definido
        if test.equipment_id is None:
            test.equipment_id = equipment_obj.id

    # 3. Determina o próximo número de tentativa
    max_num = await db.scalar(
        select(func.coalesce(func.max(TestExecution.execution_number), 0)).where(
            TestExecution.lab_test_id == test_id
        )
    )
    next_number = (max_num or 0) + 1

    # 4. Cria o registro de execução
    execution = TestExecution(
        lab_test_id=test.id,
        execution_number=next_number,
        status=ExecutionStatus.EM_ANDAMENTO,
        executed_by_id=actor.id,
        executed_by=actor,
        equipment_id=equipment_to_use_id,
        equipment=equipment_obj,
        started_at=utcnow(),
        temperature_celsius=payload.temperature_celsius,
        humidity_percent=payload.humidity_percent,
        pressure_hpa=payload.pressure_hpa,
        notes=payload.notes,
    )
    db.add(execution)

    await db.flush()

    audit_entry = await audit_service.append(
        db,
        action=AuditAction.CREATE,
        entity_type=AuditEntity.TEST_EXECUTION.value,
        entity_id=execution.id,
        actor=actor,
        new_value=audit_service.snapshot(execution),
        reason=f"Início de execução de bancada ({execution.attempt_label})",
        context=context,
    )
    refreshed = await get_execution(db, execution.id)
    return refreshed, audit_entry.sequence


async def record_readings(
    db: AsyncSession,
    execution_id: UUID,
    *,
    payload: TestExecutionRecordData,
    actor: User,
    context: RequestContext | None = None,
) -> tuple[TestExecution, int]:
    """Salva leituras parciais e medições brutas em tempo real durante o ensaio."""
    execution = await get_execution(db, execution_id)
    if execution.status != ExecutionStatus.EM_ANDAMENTO:
        raise ConflictError(
            f"Não é possível gravar leituras em uma execução com status '{execution.status.value}'."
        )

    old_value = audit_service.snapshot(execution)

    if payload.temperature_celsius is not None:
        execution.temperature_celsius = payload.temperature_celsius
    if payload.humidity_percent is not None:
        execution.humidity_percent = payload.humidity_percent
    if payload.pressure_hpa is not None:
        execution.pressure_hpa = payload.pressure_hpa
    if payload.raw_data:
        current_data = dict(execution.raw_data or {})
        current_data.update(payload.raw_data)
        execution.raw_data = current_data
    if payload.result_value is not None:
        execution.result_value = payload.result_value
    if payload.result_text is not None:
        execution.result_text = payload.result_text
    if payload.notes is not None:
        execution.notes = payload.notes

    await db.flush()

    audit_entry = await audit_service.append(
        db,
        action=AuditAction.UPDATE,
        entity_type=AuditEntity.TEST_EXECUTION.value,
        entity_id=execution.id,
        actor=actor,
        old_value=old_value,
        new_value=audit_service.snapshot(execution),
        reason=f"Registro de dados e medições de bancada ({execution.attempt_label})",
        context=context,
    )
    refreshed = await get_execution(db, execution.id)
    return refreshed, audit_entry.sequence


async def complete_execution(
    db: AsyncSession,
    execution_id: UUID,
    *,
    payload: TestExecutionComplete,
    actor: User,
    context: RequestContext | None = None,
) -> tuple[TestExecution, int]:
    """Finaliza a execução com os resultados consolidados e parecer preliminar."""
    execution = await get_execution(db, execution_id)
    if execution.status != ExecutionStatus.EM_ANDAMENTO:
        raise ConflictError(
            f"Não é possível concluir uma execução com status '{execution.status.value}'."
        )

    old_value = audit_service.snapshot(execution)

    execution.status = ExecutionStatus.CONCLUIDA
    execution.finished_at = utcnow()
    execution.outcome = payload.outcome
    if payload.raw_data:
        execution.raw_data = payload.raw_data
    if payload.result_value is not None:
        execution.result_value = payload.result_value
    if payload.result_text is not None:
        execution.result_text = payload.result_text
    if payload.temperature_celsius is not None:
        execution.temperature_celsius = payload.temperature_celsius
    if payload.humidity_percent is not None:
        execution.humidity_percent = payload.humidity_percent
    if payload.pressure_hpa is not None:
        execution.pressure_hpa = payload.pressure_hpa
    if payload.notes is not None:
        execution.notes = payload.notes

    await db.flush()

    audit_entry = await audit_service.append(
        db,
        action=AuditAction.UPDATE,
        entity_type=AuditEntity.TEST_EXECUTION.value,
        entity_id=execution.id,
        actor=actor,
        old_value=old_value,
        new_value=audit_service.snapshot(execution),
        reason=f"Conclusão de execução de bancada ({execution.attempt_label})",
        context=context,
    )
    refreshed = await get_execution(db, execution.id)
    return refreshed, audit_entry.sequence


async def interrupt_execution(
    db: AsyncSession,
    execution_id: UUID,
    *,
    payload: TestExecutionInterrupt,
    actor: User,
    context: RequestContext | None = None,
) -> tuple[TestExecution, int]:
    """Interrompe uma execução preservando todo o histórico (Princípio ALCOA+)."""
    execution = await get_execution(db, execution_id)
    if execution.status != ExecutionStatus.EM_ANDAMENTO:
        raise ConflictError(
            f"Apenas execuções em andamento podem ser interrompidas (status atual: '{execution.status.value}')."
        )

    old_value = audit_service.snapshot(execution)

    execution.status = ExecutionStatus.INTERROMPIDA
    execution.finished_at = utcnow()
    execution.interruption_reason = payload.reason.strip()

    await db.flush()

    audit_entry = await audit_service.append(
        db,
        action=AuditAction.UPDATE,
        entity_type=AuditEntity.TEST_EXECUTION.value,
        entity_id=execution.id,
        actor=actor,
        old_value=old_value,
        new_value=audit_service.snapshot(execution),
        reason=f"Interrupção técnica de execução ({execution.attempt_label})",
        context=context,
    )
    refreshed = await get_execution(db, execution.id)
    return refreshed, audit_entry.sequence
