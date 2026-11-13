"""Serviço de Gestão de Equipamentos e Controle Metrológico (Fase 2 / M2.1)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.errors import ConflictError, NotFoundError, ValidationDomainError
from app.models.base import utcnow
from app.models.enums import AuditAction, AuditEntity, EquipmentCalibrationStatus
from app.models.equipment import LaboratoryEquipment
from app.models.user import User
from app.schemas.equipment import (
    EquipmentCalibrationUpdate,
    EquipmentCreate,
    EquipmentUpdate,
)
from app.services import audit_service


def _ensure_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


async def get_equipment(db: AsyncSession, equipment_id: UUID) -> LaboratoryEquipment:
    eq = await db.get(LaboratoryEquipment, equipment_id)
    if eq is None:
        raise NotFoundError("Equipamento não encontrado.")
    return eq


async def get_equipment_by_code(
    db: AsyncSession, code: str
) -> LaboratoryEquipment | None:
    return await db.scalar(
        select(LaboratoryEquipment).where(LaboratoryEquipment.code == code.strip())
    )


async def list_equipment(
    db: AsyncSession,
    *,
    calibration_status: EquipmentCalibrationStatus | None = None,
    active_only: bool = True,
) -> list[LaboratoryEquipment]:
    query = select(LaboratoryEquipment)
    if active_only:
        query = query.where(LaboratoryEquipment.is_active.is_(True))
    if calibration_status is not None:
        query = query.where(
            LaboratoryEquipment.calibration_status == calibration_status
        )
    query = query.order_by(LaboratoryEquipment.code.asc())
    result = await db.scalars(query)
    return list(result.all())


async def create_equipment(
    db: AsyncSession,
    *,
    payload: EquipmentCreate,
    actor: User,
    context: RequestContext | None = None,
) -> tuple[LaboratoryEquipment, int]:
    existing = await get_equipment_by_code(db, payload.code)
    if existing is not None:
        raise ConflictError(f"Já existe equipamento cadastrado com o código '{payload.code}'.")

    now = utcnow()
    status = payload.calibration_status
    due_utc = _ensure_utc(payload.calibration_due_date)
    if due_utc and due_utc < now:
        status = EquipmentCalibrationStatus.VENCIDO

    equipment = LaboratoryEquipment(
        code=payload.code.strip(),
        name=payload.name.strip(),
        equipment_type=payload.equipment_type.strip() if payload.equipment_type else None,
        manufacturer=payload.manufacturer.strip() if payload.manufacturer else None,
        model=payload.model.strip() if payload.model else None,
        serial_number=payload.serial_number.strip() if payload.serial_number else None,
        location=payload.location.strip() if payload.location else None,
        calibration_status=status,
        last_calibration_at=payload.last_calibration_at,
        calibration_due_date=payload.calibration_due_date,
        certificate_number=payload.certificate_number.strip() if payload.certificate_number else None,
        calibration_agency=payload.calibration_agency.strip() if payload.calibration_agency else None,
        notes=payload.notes,
        is_active=payload.is_active,
    )
    db.add(equipment)
    await db.flush()

    audit_entry = await audit_service.append(
        db,
        action=AuditAction.CREATE,
        entity_type=AuditEntity.LABORATORY_EQUIPMENT.value,
        entity_id=equipment.id,
        actor=actor,
        new_value=audit_service.snapshot(equipment),
        reason="Cadastro de equipamento/instrumento metrológico",
        context=context,
    )
    return equipment, audit_entry.sequence


async def update_equipment(
    db: AsyncSession,
    equipment_id: UUID,
    *,
    payload: EquipmentUpdate,
    actor: User,
    context: RequestContext | None = None,
) -> tuple[LaboratoryEquipment, int]:
    equipment = await get_equipment(db, equipment_id)
    old_value = audit_service.snapshot(equipment)

    if payload.name is not None:
        equipment.name = payload.name.strip()
    if payload.equipment_type is not None:
        equipment.equipment_type = payload.equipment_type.strip() if payload.equipment_type else None
    if payload.manufacturer is not None:
        equipment.manufacturer = payload.manufacturer.strip() if payload.manufacturer else None
    if payload.model is not None:
        equipment.model = payload.model.strip() if payload.model else None
    if payload.serial_number is not None:
        equipment.serial_number = payload.serial_number.strip() if payload.serial_number else None
    if payload.location is not None:
        equipment.location = payload.location.strip() if payload.location else None
    if payload.calibration_status is not None:
        equipment.calibration_status = payload.calibration_status
    if payload.last_calibration_at is not None:
        equipment.last_calibration_at = payload.last_calibration_at
    if payload.calibration_due_date is not None:
        equipment.calibration_due_date = payload.calibration_due_date
    if payload.certificate_number is not None:
        equipment.certificate_number = payload.certificate_number.strip() if payload.certificate_number else None
    if payload.calibration_agency is not None:
        equipment.calibration_agency = payload.calibration_agency.strip() if payload.calibration_agency else None
    if payload.notes is not None:
        equipment.notes = payload.notes
    if payload.is_active is not None:
        equipment.is_active = payload.is_active

    # Se a data de validade estiver vencida
    due_utc = _ensure_utc(equipment.calibration_due_date)
    if (
        due_utc
        and due_utc < utcnow()
        and equipment.calibration_status != EquipmentCalibrationStatus.NAO_APLICAVEL
    ):
        equipment.calibration_status = EquipmentCalibrationStatus.VENCIDO

    await db.flush()

    audit_entry = await audit_service.append(
        db,
        action=AuditAction.UPDATE,
        entity_type=AuditEntity.LABORATORY_EQUIPMENT.value,
        entity_id=equipment.id,
        actor=actor,
        old_value=old_value,
        new_value=audit_service.snapshot(equipment),
        reason="Atualização cadastral de equipamento",
        context=context,
    )
    return equipment, audit_entry.sequence


async def update_calibration(
    db: AsyncSession,
    equipment_id: UUID,
    *,
    payload: EquipmentCalibrationUpdate,
    actor: User,
    context: RequestContext | None = None,
) -> tuple[LaboratoryEquipment, int]:
    """Registra uma nova calibração periódica ou de manutenção para o instrumento."""
    equipment = await get_equipment(db, equipment_id)
    old_value = audit_service.snapshot(equipment)

    last_calib_utc = _ensure_utc(payload.last_calibration_at)
    due_utc = _ensure_utc(payload.calibration_due_date)
    if due_utc is not None and last_calib_utc is not None and due_utc <= last_calib_utc:
        raise ValidationDomainError(
            "A data de vencimento da calibração deve ser posterior à data de calibração."
        )

    now = utcnow()
    status = payload.calibration_status
    if due_utc and due_utc < now:
        status = EquipmentCalibrationStatus.VENCIDO

    equipment.last_calibration_at = payload.last_calibration_at
    equipment.calibration_due_date = payload.calibration_due_date
    equipment.certificate_number = payload.certificate_number.strip()
    equipment.calibration_agency = payload.calibration_agency.strip()
    equipment.calibration_status = status
    if payload.notes:
        note_entry = f"[{now.strftime('%Y-%m-%d %H:%M')}] Calibração: {payload.notes}"
        equipment.notes = f"{equipment.notes}\n{note_entry}" if equipment.notes else note_entry

    await db.flush()

    audit_entry = await audit_service.append(
        db,
        action=AuditAction.UPDATE,
        entity_type=AuditEntity.LABORATORY_EQUIPMENT.value,
        entity_id=equipment.id,
        actor=actor,
        old_value=old_value,
        new_value=audit_service.snapshot(equipment),
        reason="Atualização de calibração metrológica",
        context=context,
    )
    return equipment, audit_entry.sequence


def validate_equipment_for_use(equipment: LaboratoryEquipment) -> None:
    """Valida metrologicamente se um equipamento pode ser alocado para uma execução de ensaio."""
    if not equipment.is_active:
        raise ValidationDomainError(
            f"Equipamento '{equipment.code}' está inativo no sistema."
        )

    if equipment.calibration_status == EquipmentCalibrationStatus.EM_MANUTENCAO:
        raise ValidationDomainError(
            f"Equipamento '{equipment.code}' ({equipment.name}) está em MANUTENÇÃO e não pode ser utilizado."
        )

    if (
        equipment.calibration_status == EquipmentCalibrationStatus.VENCIDO
        or not equipment.is_calibration_valid
    ):
        due_str = (
            equipment.calibration_due_date.strftime("%d/%m/%Y")
            if equipment.calibration_due_date
            else "indeterminada"
        )
        raise ValidationDomainError(
            f"Bloqueio Metrológico: O equipamento '{equipment.code}' ({equipment.name}) "
            f"está com calibração VENCIDA (validade expirada em {due_str}). "
            "A realização de ensaios requer instrumento calibrado conforme ISO/IEC 17025."
        )
