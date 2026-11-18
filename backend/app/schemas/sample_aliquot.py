"""Schemas Pydantic para gestão e rastreabilidade de sub-alíquotas de amostras (P4.2 / ISO 17025 §7.4)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SampleAliquotCreate(BaseModel):
    """Payload de criação / fracionamento de alíquota a partir da amostra-mãe."""

    aliquot_code: str = Field(
        ...,
        min_length=3,
        max_length=64,
        description="Código identificador único da alíquota (ex.: LIMS-2026-001-A1)",
    )
    volume_or_mass: float = Field(..., gt=0, description="Volume ou massa fracionada da alíquota")
    unit: str = Field(..., max_length=16, description="Unidade de medida (ex.: ml, mg, g)")
    storage_location: str | None = Field(None, max_length=120, description="Localização física ou freezer")
    notes: str | None = Field(None, max_length=500, description="Observações de fracionamento ou manuseio")


class SampleAliquotOut(BaseModel):
    """Representação serializada de uma sub-alíquota com rastreabilidade de custódia."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    device_sample_id: UUID
    aliquot_code: str
    volume_or_mass: float
    unit: str
    storage_location: str | None = None
    created_at: datetime
    created_by_id: UUID | None = None
    notes: str | None = None
