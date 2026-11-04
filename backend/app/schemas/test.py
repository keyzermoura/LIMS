"""Schemas de ensaios laboratoriais e resultados."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import TestOutcome, TestStatus
from app.schemas.common import UserBrief


class LabTestCreate(BaseModel):
    id: UUID
    device_sample_id: UUID
    name: str = Field(min_length=2, max_length=160)
    method: str | None = Field(default=None, max_length=200)
    parameters: dict[str, Any] = Field(default_factory=dict)
    unit: str = Field(min_length=1, max_length=32)
    lower_limit: Decimal | None = None
    upper_limit: Decimal | None = None
    acceptance_criteria: str | None = Field(default=None, max_length=2000)
    assigned_to_id: UUID | None = None

    @model_validator(mode="after")
    def _limits_order(self) -> LabTestCreate:
        if (
            self.lower_limit is not None
            and self.upper_limit is not None
            and self.lower_limit > self.upper_limit
        ):
            raise ValueError("Limite inferior não pode ser maior que o superior.")
        return self


class LabTestResultIn(BaseModel):
    result_value: Decimal | None = None
    result_text: str | None = Field(default=None, max_length=500)
    outcome: TestOutcome | None = None
    notes: str | None = Field(default=None, max_length=4000)
    amendment_reason: str | None = Field(default=None, min_length=10, max_length=1000)
    version: int = Field(ge=1)


class LabTestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    device_sample_id: UUID
    name: str
    method: str | None
    parameters: dict[str, Any]
    unit: str
    lower_limit: Decimal | None
    upper_limit: Decimal | None
    acceptance_criteria: str | None
    result_value: Decimal | None
    result_text: str | None
    outcome: TestOutcome | None = None
    notes: str | None
    status: TestStatus
    assigned_to_id: UUID | None
    tested_by: UserBrief | None = None
    tested_at: datetime | None
    signed_at: datetime | None
    signed_by: UserBrief | None = None
    signature_id: UUID | None
    result_version: int
    version: int
    created_at: datetime
    updated_at: datetime


class LabTestResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    version: int
    result_value: Decimal | None
    result_text: str | None
    unit: str
    outcome: TestOutcome
    notes: str | None
    is_amendment: bool
    amendment_reason: str | None
    signed_by: UserBrief
    signed_at: datetime
    signature_id: UUID


class TestAlert(BaseModel):
    code: str
    severity: str
    message: str
    capa_id: UUID | None = None
    capa_code: str | None = None
    capa_required: bool = False


class TestResultResponse(BaseModel):
    test: LabTestOut
    result_version: LabTestResultOut
    alert: TestAlert | None = None
    capa_id: UUID | None = None
    audit_log_id: int
    signature_id: UUID
    signature_manifest_hash: str


class LabTestCreateResponse(BaseModel):
    test: LabTestOut
    audit_log_id: int
    signature_id: UUID


class TestHistoryOut(BaseModel):
    test_id: UUID
    versions: list[LabTestResultOut]
