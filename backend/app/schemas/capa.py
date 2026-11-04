"""Schemas de CAPA."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import CapaStatus
from app.schemas.common import UserBrief


class CapaCreate(BaseModel):
    id: UUID
    device_sample_id: UUID | None = None
    lab_test_id: UUID | None = None
    title: str = Field(min_length=5, max_length=200)
    root_cause: str = Field(min_length=10, max_length=4000)
    action_plan: str = Field(min_length=10, max_length=4000)
    owner_id: UUID
    due_date: date

    @model_validator(mode="after")
    def _requires_origin(self) -> CapaCreate:
        if self.device_sample_id is None and self.lab_test_id is None:
            raise ValueError("Informe a amostra ou o ensaio de origem.")
        return self


class CapaUpdate(BaseModel):
    root_cause: str | None = Field(default=None, min_length=10, max_length=4000)
    action_plan: str | None = Field(default=None, min_length=10, max_length=4000)
    owner_id: UUID | None = None
    status: CapaStatus | None = None
    due_date: date | None = None
    effectiveness_check: str | None = Field(default=None, min_length=10, max_length=4000)
    version: int = Field(ge=1)

    @model_validator(mode="after")
    def _at_least_one(self) -> CapaUpdate:
        if not any(
            value is not None
            for value in (
                self.root_cause,
                self.action_plan,
                self.owner_id,
                self.status,
                self.due_date,
                self.effectiveness_check,
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
    title: str
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
    effective: bool | None = None
    version: int
    created_at: datetime
    updated_at: datetime


class CapaCreateResponse(BaseModel):
    capa: CapaOut
    audit_log_id: int
    signature_id: UUID
