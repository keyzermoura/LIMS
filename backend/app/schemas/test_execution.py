"""Schemas para Execuções de Bancada e Tentativas de Ensaio."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ExecutionStatus, TestOutcome
from app.schemas.common import UserBrief


class TestExecutionStart(BaseModel):
    equipment_id: UUID | None = None
    temperature_celsius: Decimal | None = None
    humidity_percent: Decimal | None = None
    pressure_hpa: Decimal | None = None
    notes: str | None = Field(default=None, max_length=2000)


class TestExecutionRecordData(BaseModel):
    temperature_celsius: Decimal | None = None
    humidity_percent: Decimal | None = None
    pressure_hpa: Decimal | None = None
    raw_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Leituras brutas obtidas do equipamento/instrumento",
    )
    result_value: Decimal | None = None
    result_text: str | None = Field(default=None, max_length=500)
    notes: str | None = None


class TestExecutionInterrupt(BaseModel):
    reason: str = Field(min_length=5, max_length=1000, description="Motivo técnico da interrupção do ensaio")


class TestExecutionComplete(BaseModel):
    raw_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Leituras brutas finais consolidadas da execução",
    )
    result_value: Decimal | None = None
    result_text: str | None = Field(default=None, max_length=500)
    outcome: TestOutcome = Field(description="Resultado obtido nesta execução (APROVADO, REPROVADO, INCONCLUSIVO)")
    temperature_celsius: Decimal | None = None
    humidity_percent: Decimal | None = None
    pressure_hpa: Decimal | None = None
    notes: str | None = None


class TestExecutionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    lab_test_id: UUID
    execution_number: int
    attempt_label: str
    status: ExecutionStatus
    equipment_id: UUID | None = None
    executed_by_id: UUID | None = None
    executed_by: UserBrief | None = None
    started_at: datetime
    finished_at: datetime | None = None
    temperature_celsius: Decimal | None = None
    humidity_percent: Decimal | None = None
    pressure_hpa: Decimal | None = None
    raw_data: dict[str, Any]
    result_value: Decimal | None = None
    result_text: str | None = None
    outcome: TestOutcome | None = None
    interruption_reason: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
