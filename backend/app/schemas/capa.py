"""Schemas de CAPA (Gestão de Não Conformidades e Ações Corretivas - ISO/IEC 17025 §8.7)."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import (
    CapaActionType,
    CapaEffectivenessStatus,
    CapaItemStatus,
    CapaSourceType,
    CapaStatus,
)
from app.schemas.common import UserBrief


class IshikawaCauses(BaseModel):
    """Categorias dos 6Ms do Diagrama de Causa e Efeito (Ishikawa)."""

    metodo: list[str] = Field(default_factory=list)
    maquina: list[str] = Field(default_factory=list)
    material: list[str] = Field(default_factory=list)
    mao_de_obra: list[str] = Field(default_factory=list)
    meio_ambiente: list[str] = Field(default_factory=list)
    medicao: list[str] = Field(default_factory=list)


class FiveWhysItem(BaseModel):
    """Item guiado da metodologia dos 5 Porquês."""

    why_number: int = Field(ge=1, le=5)
    question: str = Field(min_length=3, max_length=500)
    answer: str = Field(min_length=3, max_length=1000)


class CapaActionItemCreate(BaseModel):
    """Criação de item do plano de ação CAPA."""

    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=5, max_length=4000)
    action_type: CapaActionType
    assigned_to_id: UUID
    due_date: date


class CapaActionItemUpdate(BaseModel):
    """Atualização e conclusão de item de ação."""

    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, min_length=5, max_length=4000)
    action_type: CapaActionType | None = None
    assigned_to_id: UUID | None = None
    due_date: date | None = None
    status: CapaItemStatus | None = None
    completion_evidence: str | None = Field(default=None, max_length=4000)


class CapaActionItemOut(BaseModel):
    """Representação serializada do item de ação CAPA."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    capa_id: UUID
    title: str
    description: str
    action_type: CapaActionType
    assigned_to: UserBrief
    due_date: date
    status: CapaItemStatus
    completed_at: datetime | None = None
    completion_evidence: str | None = None
    created_at: datetime
    updated_at: datetime


class CapaEffectivenessEvaluationIn(BaseModel):
    """Registro de verificação de eficácia temporal (ISO 17025 §8.7.3)."""

    effectiveness_status: CapaEffectivenessStatus
    recurrence_detected: bool = False
    justification: str = Field(min_length=10, max_length=4000)


class CapaCreate(BaseModel):
    id: UUID
    device_sample_id: UUID | None = None
    lab_test_id: UUID | None = None
    source_type: CapaSourceType = CapaSourceType.OUTRO
    title: str = Field(min_length=5, max_length=200)
    containment_action: str | None = Field(default=None, max_length=4000)
    ishikawa_causes: dict[str, list[str]] | None = None
    five_whys: list[dict[str, Any]] | None = None
    root_cause: str = Field(min_length=10, max_length=4000)
    action_plan: str = Field(min_length=10, max_length=4000)
    owner_id: UUID
    due_date: date
    target_effectiveness_date: date | None = None
    action_items: list[CapaActionItemCreate] | None = None

    @model_validator(mode="after")
    def _requires_origin(self) -> CapaCreate:
        if self.device_sample_id is None and self.lab_test_id is None:
            raise ValueError("Informe a amostra ou o ensaio de origem.")
        return self


class CapaUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=5, max_length=200)
    source_type: CapaSourceType | None = None
    containment_action: str | None = Field(default=None, max_length=4000)
    ishikawa_causes: dict[str, list[str]] | None = None
    five_whys: list[dict[str, Any]] | None = None
    root_cause: str | None = Field(default=None, min_length=10, max_length=4000)
    action_plan: str | None = Field(default=None, min_length=10, max_length=4000)
    owner_id: UUID | None = None
    status: CapaStatus | None = None
    due_date: date | None = None
    target_effectiveness_date: date | None = None
    effectiveness_check: str | None = Field(default=None, min_length=10, max_length=4000)
    effectiveness_status: CapaEffectivenessStatus | None = None
    recurrence_detected: bool | None = None
    version: int = Field(ge=1)

    @model_validator(mode="after")
    def _at_least_one(self) -> CapaUpdate:
        if not any(
            value is not None
            for value in (
                self.title,
                self.source_type,
                self.containment_action,
                self.ishikawa_causes,
                self.five_whys,
                self.root_cause,
                self.action_plan,
                self.owner_id,
                self.status,
                self.due_date,
                self.target_effectiveness_date,
                self.effectiveness_check,
                self.effectiveness_status,
                self.recurrence_detected,
            )
        ):
            raise ValueError("Nenhum campo para atualizar.")
        return self


class CapaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    device_sample_id: UUID | None
    lab_test_id: UUID | None
    source_type: CapaSourceType
    title: str
    containment_action: str | None = None
    ishikawa_causes: dict[str, list[str]] | None = None
    five_whys: list[dict[str, Any]] | None = None
    root_cause: str
    action_plan: str
    owner: UserBrief
    status: CapaStatus
    due_date: date
    opened_at: datetime
    closed_at: datetime | None
    auto_opened: bool
    created_by_id: UUID
    effectiveness_check: str | None = None
    target_effectiveness_date: date | None = None
    effectiveness_status: CapaEffectivenessStatus
    effectiveness_evaluator: UserBrief | None = None
    effectiveness_evaluated_at: datetime | None = None
    recurrence_detected: bool = False
    effective: bool | None = None
    action_items: list[CapaActionItemOut] = []
    version: int
    created_at: datetime
    updated_at: datetime


class CapaCreateResponse(BaseModel):
    capa: CapaOut
    audit_log_id: int
    signature_id: UUID
