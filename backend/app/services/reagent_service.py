"""Serviço de Gestão e Controle Metrológico de Reagentes e Padrões Analíticos (CRMs).

Atende à ISO/IEC 17025:2017 (§6.4 e §6.5):
- Rastreabilidade de padrões certificados e reagentes.
- Intertravamento obrigatório: rejeita consumo de lote vencido, em quarentena ou com saldo insuficiente.
- Baixa de estoque automatizada e auditada em transação atômica.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.context import RequestContext
from app.models.base import utcnow
from app.models.enums import AuditAction, AuditEntity, ReagentBatchStatus, ReagentType
from app.models.reagent import Reagent, ReagentBatch, TestExecutionReagentUsage
from app.models.test_execution import TestExecution
from app.models.user import User
from app.schemas.reagent import ReagentBatchCreate, ReagentCreate
from app.services import audit_service


async def create_reagent(
    db: AsyncSession,
    *,
    payload: ReagentCreate,
    actor: User,
    context: RequestContext,
) -> Reagent:
    """Cadastra um novo reagente químico ou padrão analítico no catálogo mestre."""
    existing = await db.scalar(select(Reagent).where(Reagent.code == payload.code.strip()))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Reagente com o código '{payload.code}' já está cadastrado.",
        )

    reagent = Reagent(
        code=payload.code.strip().upper(),
        name=payload.name.strip(),
        chemical_formula=payload.chemical_formula,
        cas_number=payload.cas_number.strip() if payload.cas_number else None,
        reagent_type=payload.reagent_type,
        grade=payload.grade,
        storage_temperature_min=payload.storage_temperature_min,
        storage_temperature_max=payload.storage_temperature_max,
        hazard_classification=payload.hazard_classification,
        is_active=True,
    )
    db.add(reagent)
    await db.flush()

    await audit_service.append(
        db,
        action=AuditAction.CREATE,
        entity_type=AuditEntity.REAGENT.value,
        entity_id=reagent.id,
        new_value=audit_service.snapshot(reagent),
        reason="Cadastro de novo reagente/padrão analítico no catálogo.",
        context=context,
    )
    await db.commit()
    return reagent


async def list_reagents(
    db: AsyncSession,
    *,
    reagent_type: ReagentType | None = None,
    is_active: bool | None = None,
    search: str | None = None,
) -> Sequence[Reagent]:
    """Lista catálogo de reagentes com filtros opcionais."""
    stmt = select(Reagent).options(selectinload(Reagent.batches)).order_by(Reagent.code)

    if reagent_type:
        stmt = stmt.where(Reagent.reagent_type == reagent_type)
    if is_active is not None:
        stmt = stmt.where(Reagent.is_active == is_active)
    if search:
        pattern = f"%{search.strip()}%"
        stmt = stmt.where(
            (Reagent.code.ilike(pattern))
            | (Reagent.name.ilike(pattern))
            | (Reagent.cas_number.ilike(pattern))
        )

    result = await db.scalars(stmt)
    return result.all()


async def get_reagent(db: AsyncSession, reagent_id: UUID) -> Reagent:
    """Busca reagente por ID."""
    reagent = await db.scalar(
        select(Reagent)
        .options(selectinload(Reagent.batches))
        .where(Reagent.id == reagent_id)
    )
    if not reagent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reagente analítico não encontrado.",
        )
    return reagent


async def create_batch(
    db: AsyncSession,
    *,
    reagent_id: UUID,
    payload: ReagentBatchCreate,
    actor: User,
    context: RequestContext,
) -> ReagentBatch:
    """Registra recebimento de lote físico de reagente/padrão (ISO 17025 §6.4)."""
    reagent = await get_reagent(db, reagent_id)

    # Verifica se já está vencido no momento do cadastro
    is_expired = date.today() > payload.expiration_date
    initial_status = (
        ReagentBatchStatus.EXPIRED if is_expired else ReagentBatchStatus.AVAILABLE
    )

    batch = ReagentBatch(
        reagent_id=reagent.id,
        lot_number=payload.lot_number.strip(),
        manufacturer=payload.manufacturer.strip(),
        catalog_number=payload.catalog_number,
        expiration_date=payload.expiration_date,
        initial_quantity=payload.initial_quantity,
        current_quantity=payload.initial_quantity,
        unit=payload.unit.strip(),
        certificate_number=payload.certificate_number,
        uncertainty_value=payload.uncertainty_value,
        k_factor=payload.k_factor,
        status=initial_status,
        notes=payload.notes,
    )
    db.add(batch)
    await db.flush()

    await audit_service.append(
        db,
        action=AuditAction.CREATE,
        entity_type=AuditEntity.REAGENT_BATCH.value,
        entity_id=batch.id,
        new_value=audit_service.snapshot(batch),
        reason=f"Entrada de lote físico {batch.lot_number} para o reagente {reagent.code}.",
        context=context,
    )
    await db.commit()
    return batch


async def list_batches(
    db: AsyncSession,
    *,
    reagent_id: UUID | None = None,
    available_only: bool = False,
    expiring_days: int | None = None,
) -> Sequence[ReagentBatch]:
    """Lista lotes de insumos com filtros analíticos de validade e disponibilidade."""
    stmt = select(ReagentBatch).options(selectinload(ReagentBatch.reagent)).order_by(ReagentBatch.expiration_date)

    if reagent_id:
        stmt = stmt.where(ReagentBatch.reagent_id == reagent_id)

    if available_only:
        stmt = stmt.where(
            ReagentBatch.status.in_([ReagentBatchStatus.AVAILABLE, ReagentBatchStatus.IN_USE]),
            ReagentBatch.expiration_date >= date.today(),
            ReagentBatch.current_quantity > 0,
        )

    result = await db.scalars(stmt)
    batches = result.all()

    if expiring_days is not None:
        today = date.today()
        batches = [
            b for b in batches
            if 0 <= (b.expiration_date - today).days <= expiring_days
        ]

    return batches


async def consume_reagent_in_execution(
    db: AsyncSession,
    *,
    execution_id: UUID,
    batch_id: UUID,
    quantity_used: float,
    unit: str,
    actor: User,
    context: RequestContext,
) -> TestExecutionReagentUsage:
    """Registra o consumo de um lote de reagente/padrão durante ensaio (ISO 17025 §6.4).

    INTERTRAVAMENTO REGULAMENTAR (21 CFR Part 11 / ISO 17025):
    - Bloqueia com 422 se o lote estiver expirado.
    - Bloqueia com 422 se o lote estiver em quarentena.
    - Bloqueia com 422 se o saldo for insuficiente.
    """
    execution = await db.get(TestExecution, execution_id)
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execução de ensaio não encontrada.",
        )

    batch = await db.scalar(
        select(ReagentBatch)
        .options(selectinload(ReagentBatch.reagent))
        .where(ReagentBatch.id == batch_id)
    )
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lote de reagente/padrão não encontrado.",
        )

    # 1. Checagem de Validade (ISO 17025 §6.4)
    if batch.is_expired or batch.status == ReagentBatchStatus.EXPIRED:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Lote {batch.lot_number} ({batch.reagent.name}) expirou em "
                f"{batch.expiration_date}. Consumo proibido em ensaios regulamentados (ISO/IEC 17025 §6.4)."
            ),
        )

    # 2. Checagem de Quarentena
    if batch.status == ReagentBatchStatus.QUARANTINE:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Lote {batch.lot_number} está retido em QUARENTENA.",
        )

    # 3. Checagem de Saldo em Estoque
    if batch.current_quantity < quantity_used:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Saldo insuficiente no lote {batch.lot_number}. "
                f"Disponível: {batch.current_quantity}{batch.unit}, solicitado: {quantity_used}{unit}."
            ),
        )

    old_batch_snapshot = audit_service.snapshot(batch)

    # Baixa do estoque e abertura de frasco se primeiro uso
    batch.current_quantity -= quantity_used
    if batch.opened_at is None:
        batch.opened_at = utcnow()
        batch.status = ReagentBatchStatus.IN_USE

    if batch.current_quantity == 0:
        batch.status = ReagentBatchStatus.DEPLETED

    usage = TestExecutionReagentUsage(
        execution_id=execution.id,
        batch_id=batch.id,
        quantity_used=quantity_used,
        unit=unit,
        consumed_at=utcnow(),
        recorded_by_id=actor.id,
    )
    db.add(usage)
    await db.flush()

    await audit_service.append(
        db,
        action=AuditAction.UPDATE,
        entity_type=AuditEntity.REAGENT_BATCH.value,
        entity_id=batch.id,
        old_value=old_batch_snapshot,
        new_value=audit_service.snapshot(batch),
        reason=(
            f"Consumo analítico de {quantity_used}{unit} do lote {batch.lot_number} "
            f"no ensaio {execution.id}."
        ),
        context=context,
    )
    await db.commit()
    return usage


async def list_execution_usages(
    db: AsyncSession,
    *,
    execution_id: UUID,
) -> Sequence[TestExecutionReagentUsage]:
    """Lista todos os consumos de insumos/padrões registrados em uma execução."""
    stmt = (
        select(TestExecutionReagentUsage)
        .options(
            selectinload(TestExecutionReagentUsage.batch).selectinload(ReagentBatch.reagent),
            selectinload(TestExecutionReagentUsage.recorded_by),
        )
        .where(TestExecutionReagentUsage.execution_id == execution_id)
        .order_by(TestExecutionReagentUsage.consumed_at.desc())
    )
    result = await db.scalars(stmt)
    return result.all()

