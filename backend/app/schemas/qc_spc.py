"""Schemas Pydantic para Controle Estatístico de Processo e Westgard (H2.5)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import QCStatus


class UserBriefOut(BaseModel):
    id: UUID
    full_name: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class TestMethodBriefOut(BaseModel):
    id: UUID
    code: str
    name: str
    category: str

    model_config = ConfigDict(from_attributes=True)


class QCRunCreate(BaseModel):
    method_id: UUID
    equipment_id: UUID | None = None
    reagent_batch_id: UUID | None = Field(None, description="Padrão Analítico (CRM) utilizado no controle")
    measured_value: float = Field(..., description="Valor medido na amostra de CQI")
    target_mean: float = Field(..., description="Média de referência esperada (nominal)")
    target_sd: float = Field(..., gt=0, description="Desvio padrão histórico ou aceitável")
    notes: str | None = None


class QCRunResolve(BaseModel):
    corrective_notes: str = Field(..., min_length=10, description="Justificativa técnica ou parecer da investigação OOS")


class QCRunOut(BaseModel):
    id: UUID
    code: str
    method_id: UUID
    equipment_id: UUID | None = None
    reagent_batch_id: UUID | None = None
    operator_id: UUID
    run_at: datetime
    target_mean: float
    target_sd: float
    measured_value: float
    z_score: float
    status: QCStatus
    violation_rules: list[str] = Field(default_factory=list)
    is_active_violation: bool
    corrective_notes: str | None = None
    version: int
    created_at: datetime
    updated_at: datetime

    method: TestMethodBriefOut | None = None
    operator: UserBriefOut | None = None

    model_config = ConfigDict(from_attributes=True)


class LeveyJenningsPoint(BaseModel):
    run_id: UUID
    code: str
    run_at: str
    measured_value: float
    z_score: float
    status: QCStatus
    violation_rules: list[str] = Field(default_factory=list)
    operator_name: str


class LeveyJenningsChartData(BaseModel):
    method_id: UUID
    method_name: str
    target_mean: float
    target_sd: float
    plus_1s: float
    minus_1s: float
    plus_2s: float
    minus_2s: float
    plus_3s: float
    minus_3s: float
    points: list[LeveyJenningsPoint] = Field(default_factory=list)
    total_runs: int
    active_rejections: int
    active_warnings: int
