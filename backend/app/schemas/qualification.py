"""Schemas Pydantic para Qualificação de Analistas e Treinamento (Sprint 4.1)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import QualificationStatus


class TrainingRecordCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    provider: str | None = Field(None, max_length=200)
    completed_at: datetime | None = None
    hours: Decimal = Field(default=Decimal("1.00"), ge=Decimal("0.25"), le=Decimal("1000.00"))
    certificate_code: str | None = Field(None, max_length=100)
    notes: str | None = None


class TrainingRecordOut(BaseModel):
    id: UUID
    user_id: UUID
    qualification_id: UUID | None = None
    title: str
    provider: str | None = None
    completed_at: datetime
    hours: Decimal
    certificate_code: str | None = None
    notes: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class AnalystQualificationGrantIn(BaseModel):
    user_id: UUID
    method_id: UUID
    status: QualificationStatus = QualificationStatus.QUALIFICADO
    expires_at: datetime | None = None
    scope: str | None = Field(None, max_length=200)
    notes: str | None = None
    trainings: list[TrainingRecordCreate] = Field(default_factory=list)


class AnalystQualificationRevokeIn(BaseModel):
    status: QualificationStatus = Field(
        ...,
        description="Novo status (SUSPENSO ou EXPIRADO)",
    )
    reason: str = Field(..., min_length=10, description="Justificativa da revogação ou suspensão")


class AnalystQualificationOut(BaseModel):
    id: UUID
    user_id: UUID
    method_id: UUID
    status: QualificationStatus
    granted_at: datetime
    expires_at: datetime | None = None
    authorized_by_id: UUID
    signature_id: UUID | None = None
    scope: str | None = None
    notes: str | None = None
    is_active: bool
    version: int
    created_at: datetime
    user_name: str | None = None
    method_code: str | None = None
    method_name: str | None = None
    trainings: list[TrainingRecordOut] = Field(default_factory=list)

    class Config:
        from_attributes = True


class QualificationCheckOut(BaseModel):
    is_qualified: bool
    status: QualificationStatus | None = None
    user_id: UUID
    method_id: UUID
    user_name: str
    method_code: str
    reason: str | None = None
