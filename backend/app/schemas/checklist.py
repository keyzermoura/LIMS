"""Schemas Pydantic para Checklist e Critérios de Conferência (Fase 1 / M1.2)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ChecklistResult, CriterionClass
from app.schemas.common import UserBrief


class ChecklistCriterionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    template_id: UUID
    code: str
    description: str
    criterion_class: CriterionClass
    is_mandatory: bool
    order: int
    created_at: datetime
    updated_at: datetime


class ChecklistTemplateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    category: str | None = None
    version: int
    is_active: bool
    criteria: list[ChecklistCriterionOut] = []
    created_at: datetime
    updated_at: datetime


class ChecklistAnswerCreate(BaseModel):
    criterion_id: UUID
    result: ChecklistResult = ChecklistResult.CONFORME
    justification: str | None = Field(default=None, max_length=2000)


class ChecklistEvaluationSubmit(BaseModel):
    template_id: UUID | None = None
    answers: list[ChecklistAnswerCreate] = Field(min_length=1)


class ChecklistAnswerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    receipt_item_id: UUID
    criterion_id: UUID
    criterion: ChecklistCriterionOut | None = None
    result: ChecklistResult
    justification: str | None = None
    evaluated_by_id: UUID
    evaluated_by: UserBrief | None = None
    created_at: datetime
    updated_at: datetime
