"""Schemas Pydantic para Revisão Técnica por Pares de Ensaios (Peer Review / ISO 17025)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import CoordinationReviewStatus
from app.schemas.common import UserBrief


class TestSubmitReviewIn(BaseModel):
    notes: str | None = Field(default=None, max_length=2000)


class TestReviewDecisionIn(BaseModel):
    status: CoordinationReviewStatus = CoordinationReviewStatus.APROVADO
    justification: str | None = Field(default=None, max_length=2000)
    notes: str | None = Field(default=None, max_length=2000)
    findings: dict[str, Any] = Field(default_factory=dict)


class TestReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    lab_test_id: UUID
    review_number: int
    reviewed_by_id: UUID
    reviewed_by: UserBrief | None = None
    status: CoordinationReviewStatus
    justification: str | None = None
    notes: str | None = None
    signature_id: UUID | None = None
    reviewed_at: datetime
    created_at: datetime
