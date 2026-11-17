"""Schemas Pydantic para Reagentes, Padrões Analíticos e Controle de Insumos (Sprint 7.1)."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ReagentBatchStatus, ReagentGrade, ReagentType


class ReagentBase(BaseModel):
    code: str = Field(min_length=2, max_length=32, description="Código único do insumo (ex: REA-001)")
    name: str = Field(min_length=2, max_length=160, description="Nome químico ou comercial do reagente")
    chemical_formula: str | None = Field(default=None, max_length=64)
    cas_number: str | None = Field(default=None, max_length=32, description="Número CAS")
    reagent_type: ReagentType
    grade: ReagentGrade = ReagentGrade.PA
    storage_temperature_min: float | None = None
    storage_temperature_max: float | None = None
    hazard_classification: str | None = Field(default=None, max_length=120)


class ReagentCreate(ReagentBase):
    pass


class ReagentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    chemical_formula: str | None = None
    cas_number: str | None = None
    grade: ReagentGrade | None = None
    storage_temperature_min: float | None = None
    storage_temperature_max: float | None = None
    hazard_classification: str | None = None
    is_active: bool | None = None


class ReagentOut(ReagentBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ReagentBatchCreate(BaseModel):
    lot_number: str = Field(min_length=1, max_length=64)
    manufacturer: str = Field(min_length=1, max_length=120)
    catalog_number: str | None = Field(default=None, max_length=64)
    expiration_date: date
    initial_quantity: float = Field(gt=0, description="Quantidade inicial recebida")
    unit: str = Field(default="g", min_length=1, max_length=16)
    certificate_number: str | None = Field(default=None, max_length=64, description="Número do certificado CRM")
    uncertainty_value: float | None = Field(default=None, ge=0, description="Incerteza U do padrão")
    k_factor: float | None = Field(default=2.0, ge=1.0)
    notes: str | None = None


class ReagentBatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    reagent_id: UUID
    lot_number: str
    manufacturer: str
    catalog_number: str | None
    received_at: datetime
    opened_at: datetime | None
    expiration_date: date
    initial_quantity: float
    current_quantity: float
    unit: str
    certificate_number: str | None
    uncertainty_value: float | None
    k_factor: float | None
    status: ReagentBatchStatus
    is_expired: bool
    is_usable: bool
    notes: str | None


class ExecutionReagentUsageCreate(BaseModel):
    batch_id: UUID
    quantity_used: float = Field(gt=0, description="Quantidade de reagente/padrão consumida")
    unit: str = Field(min_length=1, max_length=16)


class ExecutionReagentUsageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    execution_id: UUID
    batch_id: UUID
    quantity_used: float
    unit: str
    consumed_at: datetime
    recorded_by_id: UUID
