"""Schemas Pydantic para Investigação de Desvios Analíticos OOS e OOT (Sprint 7.2)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    DeviationType,
    OOSInvestigationStatus,
    OOSRootCauseCategory,
)


class UserBriefOut(BaseModel):
    id: UUID
    full_name: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class LabTestBriefOut(BaseModel):
    id: UUID
    name: str
    code: str | None = None
    unit: str | None = None
    device_sample_id: UUID

    model_config = ConfigDict(from_attributes=True)


class OOSInvestigationCreate(BaseModel):
    lab_test_id: UUID
    execution_id: UUID | None = None
    deviation_type: DeviationType = DeviationType.OOS
    initial_result: float | None = None
    initial_result_text: str | None = None
    specification_min: float | None = None
    specification_max: float | None = None
    specification_text: str | None = None


class OOSPhase1Update(BaseModel):
    calculation_verified: bool = Field(
        ..., description="Cálculos matemáticos e diluições auditados"
    )
    instrument_verified: bool = Field(
        ..., description="Calibração e baseline do instrumento conferidos"
    )
    reagent_verified: bool = Field(
        ..., description="Validade, pureza e certificados de lote de reagentes/CRMs checados"
    )
    analyst_interviewed: bool = Field(
        ..., description="Entrevista técnica com o analista executante"
    )
    sample_integrity_verified: bool = Field(
        ..., description="Aspecto físico e homogeneidade da amostra verificados"
    )
    checklist_notes: str | None = None
    phase_1_conclusion: str = Field(..., min_length=10, description="Parecer da Fase I")
    phase_2_required: bool = Field(
        False, description="Necessidade de avanço para investigação Fase II"
    )


class RetestResultItem(BaseModel):
    retest_number: int
    analyst_name: str
    result_value: float | None = None
    result_text: str | None = None
    retest_date: str
    outcome: str
    notes: str | None = None


class OOSPhase2Update(BaseModel):
    phase_2_plan: str = Field(..., min_length=10, description="Plano de re-ensaio e amostragem")
    retest_results: list[RetestResultItem] = Field(default_factory=list)
    root_cause_category: OOSRootCauseCategory
    root_cause_description: str = Field(
        ..., min_length=10, description="Descrição detalhada da causa raiz"
    )
    confirmed_status: OOSInvestigationStatus = Field(
        ...,
        description="Classificação final: CONFIRMED_LAB_ERROR ou CONFIRMED_PRODUCT_FAILURE",
    )
    capa_action_id: UUID | None = None
    auto_create_capa: bool = Field(
        False, description="Gera automaticamente uma ação corretiva no CAPA"
    )


class OOSCloseRequest(BaseModel):
    final_disposition: str = Field(
        ..., min_length=10, description="Disposição final e justificativa de encerramento"
    )


class OOSInvestigationOut(BaseModel):
    id: UUID
    investigation_number: str
    lab_test_id: UUID
    execution_id: UUID | None = None
    deviation_type: DeviationType
    status: OOSInvestigationStatus
    initial_result: float | None = None
    initial_result_text: str | None = None
    specification_min: float | None = None
    specification_max: float | None = None
    specification_text: str | None = None
    detected_by_id: UUID
    detected_at: datetime
    phase_1_checklist: dict[str, Any]
    phase_1_conclusion: str | None = None
    phase_1_completed_at: datetime | None = None
    phase_1_responsible_id: UUID | None = None
    phase_2_required: bool
    phase_2_plan: str | None = None
    phase_2_retest_results: list[Any]
    root_cause_category: OOSRootCauseCategory | None = None
    root_cause_description: str | None = None
    capa_action_id: UUID | None = None
    final_disposition: str | None = None
    closed_at: datetime | None = None
    closed_by_id: UUID | None = None
    version: int
    created_at: datetime
    updated_at: datetime

    detected_by: UserBriefOut | None = None
    phase_1_responsible: UserBriefOut | None = None
    closed_by: UserBriefOut | None = None
    lab_test: LabTestBriefOut | None = None

    model_config = ConfigDict(from_attributes=True)
