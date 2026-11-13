"""Schemas para Gestão de Equipamentos e Controle Metrológico."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import EquipmentCalibrationStatus


class EquipmentBase(BaseModel):
    code: str = Field(min_length=2, max_length=64, description="Código de identificação/tombamento")
    name: str = Field(min_length=2, max_length=200, description="Nome do equipamento")
    equipment_type: str | None = Field(default=None, max_length=100, description="Tipo de instrumento")
    manufacturer: str | None = Field(default=None, max_length=160)
    model: str | None = Field(default=None, max_length=120)
    serial_number: str | None = Field(default=None, max_length=120)
    location: str | None = Field(default=None, max_length=160)
    calibration_status: EquipmentCalibrationStatus = EquipmentCalibrationStatus.CALIBRADO
    last_calibration_at: datetime | None = None
    calibration_due_date: datetime | None = None
    certificate_number: str | None = Field(default=None, max_length=120)
    calibration_agency: str | None = Field(default=None, max_length=200)
    notes: str | None = None
    is_active: bool = True


class EquipmentCreate(EquipmentBase):
    pass


class EquipmentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    equipment_type: str | None = Field(default=None, max_length=100)
    manufacturer: str | None = None
    model: str | None = None
    serial_number: str | None = None
    location: str | None = None
    calibration_status: EquipmentCalibrationStatus | None = None
    last_calibration_at: datetime | None = None
    calibration_due_date: datetime | None = None
    certificate_number: str | None = None
    calibration_agency: str | None = None
    notes: str | None = None
    is_active: bool | None = None


class EquipmentCalibrationUpdate(BaseModel):
    last_calibration_at: datetime
    calibration_due_date: datetime
    certificate_number: str = Field(min_length=1, max_length=120)
    calibration_agency: str = Field(min_length=1, max_length=200)
    calibration_status: EquipmentCalibrationStatus = EquipmentCalibrationStatus.CALIBRADO
    notes: str | None = None


class EquipmentOut(EquipmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    is_calibration_valid: bool = True
    created_at: datetime
    updated_at: datetime
