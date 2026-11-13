"""Schemas Pydantic para Emissão e Validação de Laudos Oficiais (Marco M3 / ISO 17025)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import TestOutcome
from app.schemas.common import UserBrief


class OfficialReportGenerateIn(BaseModel):
    device_sample_id: UUID
    test_ids: list[UUID] = Field(min_length=1)
    title: str = Field(default="Laudo Pericial Oficial", min_length=3, max_length=200)
    conclusion: TestOutcome = TestOutcome.APROVADO
    summary: str | None = Field(default=None, max_length=5000)
    observations: str | None = Field(default=None, max_length=2000)


class OfficialReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    report_number: str
    device_sample_id: UUID
    title: str
    conclusion: TestOutcome
    summary: str | None = None
    sha256_hash: str
    auth_token: str
    issued_by_id: UUID
    issued_by: UserBrief | None = None
    signature_id: UUID
    issued_at: datetime
    created_at: datetime


class OfficialReportDetailOut(OfficialReportOut):
    sample_acc_number: str | None = None
    sample_commercial_name: str | None = None
    sample_model: str | None = None
    sample_serial_number: str | None = None
    sample_lot_number: str | None = None
    tests_summary: list[dict[str, Any]] = Field(default_factory=list)


class OfficialReportPublicVerifyOut(BaseModel):
    is_valid: bool
    report_number: str
    sample_acc_number: str
    sample_commercial_name: str
    sample_serial_number: str | None = None
    sample_lot_number: str | None = None
    conclusion: TestOutcome
    sha256_hash: str
    issued_by_name: str
    issued_at: datetime
