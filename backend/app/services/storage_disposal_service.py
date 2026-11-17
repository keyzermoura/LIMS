"""Serviço de Cadeia Física de Armazenamento, Contraprova Pericial e Descarte (H2.3 & H2.4).

Implementa os controles de conformidade:
- ISO/IEC 17025:2017 §7.4 (Manuseio e guarda de itens de ensaio/contraprova)
- 21 CFR Part 11 §11.200 (Dupla assinatura eletrônica rastreável para descarte irreversível)
- RDC 665/2022 / ANVISA (Rastreabilidade de amostras e laudo de destinação/descarte)
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.context import RequestContext
from app.db.dialect import next_sequence
from app.models.base import utcnow
from app.models.device_sample import DeviceSample
from app.models.enums import (
    AuditAction,
    AuditEntity,
    RetentionStatus,
    SampleStatus,
    SignatureAction,
    SignatureMeaning,
    StorageLocationType,
)
from app.models.storage_and_disposal import (
    SampleDisposalRecord,
    SampleRetention,
    SampleStorageMovement,
    StorageLocation,
)
from app.models.user import User
from app.schemas.storage_and_disposal import (
    SampleDisposalCreate,
    SampleRetentionCreate,
    SampleRetentionUpdate,
    SampleStorageMovementCreate,
    StorageDashboardSummary,
    StorageLocationCreate,
    StorageLocationUpdate,
)
from app.services import audit_service, signature_service

# ---------------------------------------------------------------------------
# Gestão de Locais Físicos de Armazenamento (StorageLocation)
# ---------------------------------------------------------------------------


async def create_location(
    db: AsyncSession,
    *,
    payload: StorageLocationCreate,
    actor: User,
    context: RequestContext,
) -> StorageLocation:
    """Cadastra um novo local físico de custódia (Freezer, Câmara Fria, etc.)."""
    # Valida código único
    existing = await db.scalar(select(StorageLocation).where(StorageLocation.code == payload.code))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Local de armazenamento com código '{payload.code}' já existe.",
        )

    # Valida limites de temperatura
    if payload.temperature_min_celsius > payload.temperature_max_celsius:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Temperatura mínima não pode ser maior que a temperatura máxima.",
        )
    if not (
        payload.temperature_min_celsius
        <= payload.temperature_target_celsius
        <= payload.temperature_max_celsius
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Temperatura alvo (target) deve estar entre a mínima e máxima permitidas.",
        )

    location = StorageLocation(
        code=payload.code,
        name=payload.name,
        location_type=payload.location_type,
        room=payload.room,
        temperature_target_celsius=payload.temperature_target_celsius,
        temperature_min_celsius=payload.temperature_min_celsius,
        temperature_max_celsius=payload.temperature_max_celsius,
        humidity_max_percent=payload.humidity_max_percent,
        capacity_units=payload.capacity_units,
        is_active=True,
        attributes=payload.metadata,
        version=1,
    )
    db.add(location)
    await db.flush()

    await audit_service.append(
        db,
        action=AuditAction.CREATE,
        entity_type=AuditEntity.STORAGE_LOCATION.value,
        entity_id=location.id,
        actor=actor,
        new_value={
            "code": location.code,
            "name": location.name,
            "type": location.location_type.value,
            "room": location.room,
            "temperature_range": f"{location.temperature_min_celsius}°C a {location.temperature_max_celsius}°C",
            "capacity": location.capacity_units,
        },
        reason=f"Cadastro do local de armazenamento {location.code}",
        context=context,
    )
    await db.commit()
    await db.refresh(location)
    return location


async def list_locations(
    db: AsyncSession,
    *,
    is_active: bool | None = None,
    location_type: StorageLocationType | None = None,
) -> Sequence[StorageLocation]:
    """Lista locais físicos de custódia com filtros opcionais."""
    stmt = select(StorageLocation).order_by(StorageLocation.code.asc())
    if is_active is not None:
        stmt = stmt.where(StorageLocation.is_active == is_active)
    if location_type is not None:
        stmt = stmt.where(StorageLocation.location_type == location_type)
    result = await db.scalars(stmt)
    return result.all()


async def get_location(db: AsyncSession, location_id: UUID) -> StorageLocation:
    """Obtém local físico por ID com validação de existência."""
    location = await db.get(StorageLocation, location_id)
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Local de armazenamento não encontrado.",
        )
    return location


async def update_location(
    db: AsyncSession,
    *,
    location_id: UUID,
    payload: StorageLocationUpdate,
    actor: User,
    context: RequestContext,
) -> StorageLocation:
    """Atualiza dados do local físico (capacidade, setpoints térmicos, status)."""
    location = await get_location(db, location_id)
    old_val = {
        "name": location.name,
        "is_active": location.is_active,
        "capacity": location.capacity_units,
    }

    if payload.name is not None:
        location.name = payload.name
    if payload.room is not None:
        location.room = payload.room
    if payload.capacity_units is not None:
        location.capacity_units = payload.capacity_units
    if payload.is_active is not None:
        location.is_active = payload.is_active
    if payload.humidity_max_percent is not None:
        location.humidity_max_percent = payload.humidity_max_percent
    if payload.metadata is not None:
        location.attributes = payload.metadata

    if payload.temperature_min_celsius is not None:
        location.temperature_min_celsius = payload.temperature_min_celsius
    if payload.temperature_max_celsius is not None:
        location.temperature_max_celsius = payload.temperature_max_celsius
    if payload.temperature_target_celsius is not None:
        location.temperature_target_celsius = payload.temperature_target_celsius

    # Revalida consistência térmica
    if location.temperature_min_celsius > location.temperature_max_celsius:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Temperatura mínima não pode exceder a máxima.",
        )

    location.version += 1
    await audit_service.append(
        db,
        action=AuditAction.UPDATE,
        entity_type=AuditEntity.STORAGE_LOCATION.value,
        entity_id=location.id,
        actor=actor,
        old_value=old_val,
        new_value={
            "name": location.name,
            "is_active": location.is_active,
            "capacity": location.capacity_units,
        },
        reason=f"Atualização do local de armazenamento {location.code}",
        context=context,
    )
    await db.commit()
    await db.refresh(location)
    return location


async def get_location_occupancy(db: AsyncSession, location_id: UUID) -> int:
    """Retorna o número de contraprovas ativas armazenadas no local."""
    count = await db.scalar(
        select(func.count(SampleRetention.id)).where(
            SampleRetention.storage_location_id == location_id,
            SampleRetention.status.in_([RetentionStatus.ACTIVE, RetentionStatus.EXTENDED]),
        )
    )
    return int(count or 0)


# ---------------------------------------------------------------------------
# Movimentação Física de Custódia (SampleStorageMovement)
# ---------------------------------------------------------------------------


async def move_sample(
    db: AsyncSession,
    *,
    payload: SampleStorageMovementCreate,
    actor: User,
    context: RequestContext,
) -> SampleStorageMovement:
    """Registra movimentação física de amostra entre locais de custódia."""
    sample = await db.get(DeviceSample, payload.sample_id)
    if not sample:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Amostra de dispositivo não encontrada.",
        )
    if sample.status == SampleStatus.DESCARTADO:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Amostra já descartada não pode ser movimentada.",
        )

    to_location = await get_location(db, payload.to_location_id)
    if not to_location.is_active:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Local de destino '{to_location.code}' está inativo.",
        )

    # Checagem de capacidade
    current_occupancy = await get_location_occupancy(db, to_location.id)
    if current_occupancy >= to_location.capacity_units:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Capacidade máxima do local '{to_location.code}' atingida ({to_location.capacity_units} itens).",
        )

    # Identifica última localização física
    last_movement = await db.scalar(
        select(SampleStorageMovement)
        .where(SampleStorageMovement.sample_id == payload.sample_id)
        .order_by(SampleStorageMovement.moved_at.desc())
        .limit(1)
    )
    from_location_id = last_movement.to_location_id if last_movement else None

    # Verificação de excursão térmica (ISO 17025 §7.4.3)
    notes = payload.notes or ""
    if payload.temperature_at_movement is not None and (
        payload.temperature_at_movement < to_location.temperature_min_celsius
        or payload.temperature_at_movement > to_location.temperature_max_celsius
    ):
        warning = (
            f"[ALERTA DE EXCURSÃO TÉRMICA]: Medição de {payload.temperature_at_movement}°C "
            f"fora da faixa [{to_location.temperature_min_celsius}°C, {to_location.temperature_max_celsius}°C]."
        )
        notes = f"{notes} {warning}".strip()

    movement = SampleStorageMovement(
        sample_id=sample.id,
        from_location_id=from_location_id,
        to_location_id=to_location.id,
        moved_by_id=actor.id,
        moved_at=utcnow(),
        reason=payload.reason,
        temperature_at_movement=payload.temperature_at_movement,
        notes=notes or None,
    )
    db.add(movement)

    # Trilha de auditoria
    await audit_service.append(
        db,
        action=AuditAction.TRANSFER,
        entity_type=AuditEntity.STORAGE_MOVEMENT.value,
        entity_id=movement.id,
        actor=actor,
        new_value={
            "sample_accession": sample.accession_number,
            "from_location_id": str(from_location_id) if from_location_id else None,
            "to_location_code": to_location.code,
            "reason": payload.reason,
            "temperature": payload.temperature_at_movement,
        },
        reason=payload.reason,
        context=context,
    )
    await db.commit()
    await db.refresh(movement)
    return movement


async def list_sample_movements(
    db: AsyncSession, *, sample_id: UUID | None = None
) -> Sequence[SampleStorageMovement]:
    """Lista histórico de movimentações com opções de filtro por amostra."""
    stmt = (
        select(SampleStorageMovement)
        .options(
            selectinload(SampleStorageMovement.sample),
            selectinload(SampleStorageMovement.from_location),
            selectinload(SampleStorageMovement.to_location),
            selectinload(SampleStorageMovement.moved_by),
        )
        .order_by(SampleStorageMovement.moved_at.desc())
    )
    if sample_id is not None:
        stmt = stmt.where(SampleStorageMovement.sample_id == sample_id)
    result = await db.scalars(stmt)
    return result.all()


# ---------------------------------------------------------------------------
# Guarda de Contraprova Pericial (SampleRetention - ISO 17025 §7.4)
# ---------------------------------------------------------------------------


async def retain_sample(
    db: AsyncSession,
    *,
    payload: SampleRetentionCreate,
    actor: User,
    context: RequestContext,
) -> SampleRetention:
    """Institui guarda formal de contraprova pericial sob lacre inviolável."""
    sample = await db.get(DeviceSample, payload.sample_id)
    if not sample:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Amostra de dispositivo não encontrada.",
        )
    if sample.status == SampleStatus.DESCARTADO:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Amostra descartada não pode ser colocada em contraprova.",
        )

    # Checa duplicidade de retenção ativa para a mesma amostra
    existing = await db.scalar(
        select(SampleRetention).where(SampleRetention.sample_id == payload.sample_id)
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Já existe registro de retenção/contraprova para a amostra {sample.accession_number} (Lacre {existing.seal_number}).",
        )

    if payload.retain_until <= date.today():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Data limite legal de retenção deve ser posterior à data atual.",
        )

    location = await get_location(db, payload.storage_location_id)
    if not location.is_active:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Local de armazenamento '{location.code}' está inativo.",
        )

    retention = SampleRetention(
        sample_id=sample.id,
        storage_location_id=location.id,
        retention_type=payload.retention_type,
        retained_at=utcnow(),
        retain_until=payload.retain_until,
        quantity_retained=payload.quantity_retained,
        unit=payload.unit,
        seal_number=payload.seal_number,
        status=RetentionStatus.ACTIVE,
        responsible_id=actor.id,
        notes=payload.notes,
        version=1,
    )
    db.add(retention)
    await db.flush()

    await audit_service.append(
        db,
        action=AuditAction.CREATE,
        entity_type=AuditEntity.SAMPLE_RETENTION.value,
        entity_id=retention.id,
        actor=actor,
        new_value={
            "sample_accession": sample.accession_number,
            "seal_number": retention.seal_number,
            "retain_until": retention.retain_until.isoformat(),
            "location_code": location.code,
            "quantity": f"{retention.quantity_retained} {retention.unit}",
        },
        reason=f"Guarda formal de contraprova com lacre {retention.seal_number}",
        context=context,
    )
    await db.commit()
    await db.refresh(retention)
    return retention


async def list_retentions(
    db: AsyncSession,
    *,
    status_filter: RetentionStatus | None = None,
    location_id: UUID | None = None,
) -> Sequence[SampleRetention]:
    """Lista contraprovas periciais cadastradas."""
    stmt = (
        select(SampleRetention)
        .options(
            selectinload(SampleRetention.sample),
            selectinload(SampleRetention.storage_location),
            selectinload(SampleRetention.responsible),
        )
        .order_by(SampleRetention.retain_until.asc())
    )
    if status_filter is not None:
        stmt = stmt.where(SampleRetention.status == status_filter)
    if location_id is not None:
        stmt = stmt.where(SampleRetention.storage_location_id == location_id)
    result = await db.scalars(stmt)
    return result.all()


async def get_retention(db: AsyncSession, retention_id: UUID) -> SampleRetention:
    """Busca registro de retenção por ID."""
    retention = await db.scalar(
        select(SampleRetention)
        .options(
            selectinload(SampleRetention.sample),
            selectinload(SampleRetention.storage_location),
            selectinload(SampleRetention.responsible),
        )
        .where(SampleRetention.id == retention_id)
    )
    if not retention:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro de retenção de contraprova não encontrado.",
        )
    return retention


async def update_retention(
    db: AsyncSession,
    *,
    retention_id: UUID,
    payload: SampleRetentionUpdate,
    actor: User,
    context: RequestContext,
) -> SampleRetention:
    """Atualiza dados da retenção (extensão de prazo, conferência de lacre)."""
    retention = await get_retention(db, retention_id)
    old_val = {
        "retain_until": retention.retain_until.isoformat(),
        "seal_number": retention.seal_number,
        "status": retention.status.value,
    }

    if payload.retain_until is not None:
        retention.retain_until = payload.retain_until
        if retention.status == RetentionStatus.ACTIVE:
            retention.status = RetentionStatus.EXTENDED
    if payload.seal_number is not None:
        retention.seal_number = payload.seal_number
    if payload.status is not None:
        retention.status = payload.status
    if payload.notes is not None:
        retention.notes = payload.notes

    retention.version += 1
    await audit_service.append(
        db,
        action=AuditAction.UPDATE,
        entity_type=AuditEntity.SAMPLE_RETENTION.value,
        entity_id=retention.id,
        actor=actor,
        old_value=old_val,
        new_value={
            "retain_until": retention.retain_until.isoformat(),
            "seal_number": retention.seal_number,
            "status": retention.status.value,
        },
        reason=f"Atualização da contraprova lacre {retention.seal_number}",
        context=context,
    )
    await db.commit()
    await db.refresh(retention)
    return retention


# ---------------------------------------------------------------------------
# Termo de Descarte com Dupla Assinatura Eletrônica (21 CFR Part 11)
# ---------------------------------------------------------------------------


async def dispose_sample(
    db: AsyncSession,
    *,
    payload: SampleDisposalCreate,
    actor: User,  # Usuário autenticado na requisição (Executor primário)
    context: RequestContext,
) -> SampleDisposalRecord:
    """Lavra o Termo de Descarte Irreversível com Dupla Assinatura Eletrônica (21 CFR Part 11)."""
    sample = await db.get(DeviceSample, payload.sample_id)
    if not sample:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Amostra de dispositivo não encontrada.",
        )
    if sample.status == SampleStatus.DESCARTADO:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Amostra {sample.accession_number} já foi formalmente descartada.",
        )

    # 1. Regra de Segregação: Executor e Testemunha devem ser usuários distintos
    if actor.id == payload.witness_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Dupla assinatura requer dois usuários distintos (o executor não pode testemunhar seu próprio ato).",
        )

    witness_user = await db.get(User, payload.witness_id)
    if not witness_user or not witness_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário testemunha/fiscal não encontrado ou inativo.",
        )

    # 2. Intertravamento de Contraprova Pericial (ISO 17025 §7.4)
    retention = await db.scalar(
        select(SampleRetention).where(SampleRetention.sample_id == sample.id)
    )
    if (
        retention
        and retention.status in [RetentionStatus.ACTIVE, RetentionStatus.EXTENDED]
        and not retention.is_expired
        and not payload.force_legal_override
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                f"BLOQUEIO REGULATÓRIO: Contraprova pericial ativa sob custódia legal até {retention.retain_until.isoformat()} "
                f"(Lacre {retention.seal_number}). Descarte prematuro não autorizado sem liberação expressa."
            ),
        )

    # 3. Validação e Consumo dos Tokens de Assinatura Eletrônica (21 CFR Part 11 §11.200)
    primary_sig = await signature_service.consume(
        db,
        token=payload.primary_esign_token,
        user=actor,
        entity_type=AuditEntity.DEVICE_SAMPLE.value,
        entity_id=sample.id,
        action=SignatureAction.CLOSE,
        context=context,
    )
    if primary_sig.meaning != SignatureMeaning.EXECUCAO_DESCARTE:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Assinatura primária deve ter significado 'EXECUCAO_DESCARTE' (recebido: {primary_sig.meaning.value}).",
        )

    witness_sig = await signature_service.consume(
        db,
        token=payload.witness_esign_token,
        user=witness_user,
        entity_type=AuditEntity.DEVICE_SAMPLE.value,
        entity_id=sample.id,
        action=SignatureAction.CLOSE,
        context=context,
    )
    if witness_sig.meaning != SignatureMeaning.TESTEMUNHA_DESCARTE:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Assinatura da testemunha deve ter significado 'TESTEMUNHA_DESCARTE' (recebido: {witness_sig.meaning.value}).",
        )

    # 4. Geração de Manifesto Rastreável Único
    seq = await next_sequence(db, "sample_disposal_seq")
    current_year = date.today().year
    manifest_number = f"MAN-DESC-{current_year}-{seq:04d}"

    # 5. Criação do Registro de Descarte
    disposal = SampleDisposalRecord(
        sample_id=sample.id,
        retention_id=retention.id if retention else None,
        disposal_manifest_number=manifest_number,
        disposal_method=payload.disposal_method,
        disposed_at=utcnow(),
        disposed_by_id=actor.id,
        witness_id=witness_user.id,
        primary_signature_id=primary_sig.id,
        witness_signature_id=witness_sig.id,
        environmental_license_number=payload.environmental_license_number,
        waste_company_name=payload.waste_company_name,
        notes=payload.notes,
        version=1,
    )
    db.add(disposal)

    # 6. Atualização de status da amostra e da contraprova
    sample.status = SampleStatus.DESCARTADO
    if retention:
        retention.status = RetentionStatus.DISPOSED
        retention.version += 1

    # 7. Trilha de Auditoria ALCOA+
    await audit_service.append(
        db,
        action=AuditAction.UPDATE,
        entity_type=AuditEntity.SAMPLE_DISPOSAL.value,
        entity_id=disposal.id,
        actor=actor,
        new_value={
            "manifest_number": manifest_number,
            "sample_accession": sample.accession_number,
            "method": payload.disposal_method.value,
            "primary_signer": actor.full_name,
            "witness_signer": witness_user.full_name,
            "primary_signature_id": str(primary_sig.id),
            "witness_signature_id": str(witness_sig.id),
        },
        reason=f"Lavratura do Termo de Descarte {manifest_number} com dupla assinatura eletrônica",
        context=context,
        signature_id=primary_sig.id,
    )

    await db.commit()
    await db.refresh(disposal)
    return disposal


async def list_disposals(
    db: AsyncSession, *, sample_id: UUID | None = None
) -> Sequence[SampleDisposalRecord]:
    """Lista registros e manifestos de descarte."""
    stmt = (
        select(SampleDisposalRecord)
        .options(
            selectinload(SampleDisposalRecord.sample),
            selectinload(SampleDisposalRecord.disposed_by),
            selectinload(SampleDisposalRecord.witness),
            selectinload(SampleDisposalRecord.primary_signature),
            selectinload(SampleDisposalRecord.witness_signature),
        )
        .order_by(SampleDisposalRecord.disposed_at.desc())
    )
    if sample_id is not None:
        stmt = stmt.where(SampleDisposalRecord.sample_id == sample_id)
    result = await db.scalars(stmt)
    return result.all()


# ---------------------------------------------------------------------------
# Dashboard Consolidado de Custódia e Descarte
# ---------------------------------------------------------------------------


async def get_storage_summary(db: AsyncSession) -> StorageDashboardSummary:
    """Agrega contadores operacionais e de conformidade para o dashboard."""
    total_loc = await db.scalar(select(func.count(StorageLocation.id))) or 0
    active_loc = (
        await db.scalar(
            select(func.count(StorageLocation.id)).where(StorageLocation.is_active.is_(True))
        )
        or 0
    )
    total_ret = await db.scalar(select(func.count(SampleRetention.id))) or 0
    active_ret = (
        await db.scalar(
            select(func.count(SampleRetention.id)).where(
                SampleRetention.status.in_([RetentionStatus.ACTIVE, RetentionStatus.EXTENDED])
            )
        )
        or 0
    )
    expired_ret = (
        await db.scalar(
            select(func.count(SampleRetention.id)).where(
                SampleRetention.status.in_([RetentionStatus.ACTIVE, RetentionStatus.EXTENDED]),
                SampleRetention.retain_until < date.today(),
            )
        )
        or 0
    )
    total_disp = await db.scalar(select(func.count(SampleDisposalRecord.id))) or 0

    return StorageDashboardSummary(
        total_locations=int(total_loc),
        active_locations=int(active_loc),
        total_retentions=int(total_ret),
        active_retentions=int(active_ret),
        expired_retentions=int(expired_ret),
        total_disposals=int(total_disp),
    )
