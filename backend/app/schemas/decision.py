"""Schemas Pydantic para Decisões de Recebimento e Revisão da Coordenação (Fase 1 / M1.2)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import CoordinationReviewStatus, ReceiptDecisionEnum
from app.schemas.common import UserBrief


class ReceiptDecisionCreate(BaseModel):
    decision: ReceiptDecisionEnum
    justification: str = Field(min_length=5, max_length=2000)
    custody_object_id: UUID | None = None


class DecisionBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    decision: ReceiptDecisionEnum
    justification: str
    decided_by: UserBrief | None = None
    created_at: datetime


class CoordinationReviewAction(BaseModel):
    status: CoordinationReviewStatus = CoordinationReviewStatus.APROVADO
    review_notes: str = Field(min_length=5, max_length=2000)


class CoordinationReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    decision_id: UUID
    status: CoordinationReviewStatus
    decision: DecisionBrief | None = None
    reviewed_by_id: UUID | None = None
    reviewed_by: UserBrief | None = None
    reviewed_at: datetime | None = None
    review_notes: str | None = None
    created_at: datetime
    updated_at: datetime


class ReceiptDecisionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    receipt_item_id: UUID
    custody_object_id: UUID | None = None
    decision: ReceiptDecisionEnum
    justification: str
    decided_by_id: UUID
    decided_by: UserBrief | None = None
    requires_coordination_review: bool
    coordination_review: CoordinationReviewOut | None = None
    version: int
    created_at: datetime
    updated_at: datetime
