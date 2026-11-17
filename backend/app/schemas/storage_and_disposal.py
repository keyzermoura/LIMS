"""Schemas Pydantic para Cadeia Física de Armazenamento, Retenção e Descarte (H2.3 & H2.4)."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    DisposalMethod,
    RetentionStatus,
    RetentionType,
    StorageLocationType,
)


class UserBriefOut(BaseModel):
    id: UUID
    full_name: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class DeviceSampleBriefOut(BaseModel):
    id: UUID
    accession_number: str
    commercial_name: str
    manufacturer: str
    lot_number: str | None = None
    serial_number: str | None = None
    status: str

    model_config = ConfigDict(from_attributes=True)


class StorageLocationCreate(BaseModel):
    code: str = Field(..., max_length=32, description="Código único do local (ex: FRZ-80-01)")
    name: str = Field(..., max_length=120, description="Nome amigável (ex: Ultra Freezer 01 - Biologia)")
    location_type: StorageLocationType
    room: str = Field(..., max_length=64, description="Sala/Setor físico")
    temperature_target_celsius: float
    temperature_min_celsius: float
    temperature_max_celsius: float
    humidity_max_percent: float | None = None
    capacity_units: int = Field(100, ge=1, description="Capacidade máxima de unidades/amostras")
    metadata: dict[str, Any] = Field(default_factory=dict)


class StorageLocationUpdate(BaseModel):
    name: str | None = None
    room: str | None = None
    temperature_target_celsius: float | None = None
    temperature_min_celsius: float | None = None
    temperature_max_celsius: float | None = None
    humidity_max_percent: float | None = None
    capacity_units: int | None = None
    is_active: bool | None = None
    metadata: dict[str, Any] | None = None


class StorageLocationOut(BaseModel):
    id: UUID
    code: str
    name: str
    location_type: StorageLocationType
    room: str
    temperature_target_celsius: float
    temperature_min_celsius: float
    temperature_max_celsius: float
    humidity_max_percent: float | None = None
    capacity_units: int
    current_occupancy: int = 0
    is_active: bool
    metadata: dict[str, Any] = Field(default_factory=dict, validation_alias="attributes")
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class SampleStorageMovementCreate(BaseModel):
    sample_id: UUID
    to_location_id: UUID
    reason: str = Field(..., min_length=3, max_length=255, description="Motivo da movimentação de custódia")
    temperature_at_movement: float | None = Field(None, description="Temperatura conferida no ato da movimentação")
    notes: str | None = None


class SampleStorageMovementOut(BaseModel):
    id: UUID
    sample_id: UUID
    from_location_id: UUID | None = None
    to_location_id: UUID
    moved_by_id: UUID
    moved_at: datetime
    reason: str
    temperature_at_movement: float | None = None
    notes: str | None = None
    from_location: StorageLocationOut | None = None
    to_location: StorageLocationOut | None = None
    moved_by: UserBriefOut | None = None
    sample: DeviceSampleBriefOut | None = None

    model_config = ConfigDict(from_attributes=True)


class SampleRetentionCreate(BaseModel):
    sample_id: UUID
    storage_location_id: UUID
    retention_type: RetentionType = RetentionType.CONTRAPROVA_PERICIAL
    retain_until: date = Field(..., description="Data limite legal de retenção da contraprova")
    quantity_retained: float = Field(..., gt=0, description="Quantidade física retida")
    unit: str = Field("un", max_length=16)
    seal_number: str = Field(..., min_length=3, max_length=64, description="Número do lacre inviolável")
    notes: str | None = None


class SampleRetentionUpdate(BaseModel):
    retain_until: date | None = None
    seal_number: str | None = None
    status: RetentionStatus | None = None
    notes: str | None = None


class SampleRetentionOut(BaseModel):
    id: UUID
    sample_id: UUID
    storage_location_id: UUID
    retention_type: RetentionType
    retained_at: datetime
    retain_until: date
    quantity_retained: float
    unit: str
    seal_number: str
    status: RetentionStatus
    is_expired: bool
    responsible_id: UUID
    notes: str | None = None
    version: int
    created_at: datetime
    updated_at: datetime
    storage_location: StorageLocationOut | None = None
    responsible: UserBriefOut | None = None
    sample: DeviceSampleBriefOut | None = None

    model_config = ConfigDict(from_attributes=True)


class SampleDisposalCreate(BaseModel):
    sample_id: UUID
    disposal_method: DisposalMethod
    primary_esign_token: str = Field(..., description="Token de assinatura eletrônica do executor (21 CFR Part 11)")
    witness_id: UUID = Field(..., description="ID da testemunha/fiscal da qualidade")
    witness_esign_token: str = Field(..., description="Token de assinatura eletrônica da testemunha (21 CFR Part 11)")
    environmental_license_number: str | None = Field(None, description="Licença ambiental da empresa de destinação")
    waste_company_name: str | None = Field(None, description="Empresa especializada em incineração/destinação")
    notes: str | None = None
    force_legal_override: bool = Field(False, description="Autorização excepcional para contraprova não expirada")


class SampleDisposalOut(BaseModel):
    id: UUID
    sample_id: UUID
    retention_id: UUID | None = None
    disposal_manifest_number: str
    disposal_method: DisposalMethod
    disposed_at: datetime
    disposed_by_id: UUID
    witness_id: UUID
    primary_signature_id: UUID
    witness_signature_id: UUID
    environmental_license_number: str | None = None
    waste_company_name: str | None = None
    notes: str | None = None
    version: int
    created_at: datetime
    sample: DeviceSampleBriefOut | None = None
    disposed_by: UserBriefOut | None = None
    witness: UserBriefOut | None = None

    model_config = ConfigDict(from_attributes=True)


class StorageDashboardSummary(BaseModel):
    total_locations: int
    active_locations: int
    total_retentions: int
    active_retentions: int
    expired_retentions: int
    total_disposals: int
