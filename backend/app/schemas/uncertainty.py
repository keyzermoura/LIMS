"""Schemas Pydantic para Incerteza de Medição GUM e Regras de Decisão ILAC-G8 (Sprint 4.2)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import (
    ConformityStatus,
    DecisionRuleType,
    TestOutcome,
    UncertaintyDistribution,
    UncertaintySourceType,
)


class UncertaintyComponentIn(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    symbol: str | None = Field(default=None, max_length=32)
    source_type: UncertaintySourceType = UncertaintySourceType.TYPE_B
    distribution: UncertaintyDistribution = UncertaintyDistribution.RECTANGULAR
    half_width: Decimal = Field(ge=Decimal("0"))
    divisor: Decimal | None = Field(default=None, gt=Decimal("0"))
    sensitivity_coefficient: Decimal = Field(default=Decimal("1.0"), gt=Decimal("0"))
    degrees_of_freedom: int | None = Field(default=None, ge=1)


class UncertaintyComponentOut(BaseModel):
    name: str
    symbol: str | None = None
    source_type: UncertaintySourceType
    distribution: UncertaintyDistribution
    half_width: Decimal
    divisor: Decimal
    sensitivity_coefficient: Decimal
    degrees_of_freedom: int | None = None
    standard_uncertainty: Decimal
    combined_contribution: Decimal
    weight_percent: Decimal


class UncertaintySimulateIn(BaseModel):
    unit: str = Field(default="UN", min_length=1, max_length=32)
    measured_value: Decimal | None = None
    repeatability_readings: list[Decimal] = Field(default_factory=list)
    lower_limit: Decimal | None = None
    upper_limit: Decimal | None = None
    components: list[UncertaintyComponentIn] = Field(default_factory=list)
    coverage_factor: Decimal | None = Field(default=None, gt=Decimal("0"))
    confidence_level: Decimal = Field(default=Decimal("95.45"), gt=Decimal("0"), lt=Decimal("100"))
    guard_band_multiplier: Decimal = Field(default=Decimal("1.000"), ge=Decimal("0"))
    decision_rule: DecisionRuleType = DecisionRuleType.GUARD_BAND_CONSERVATIVE

    @model_validator(mode="after")
    def _validate_limits(self) -> UncertaintySimulateIn:
        if (
            self.lower_limit is not None
            and self.upper_limit is not None
            and self.lower_limit > self.upper_limit
        ):
            raise ValueError("Limite inferior não pode ser maior que o limite superior.")
        return self


class UncertaintyBudgetCreateIn(UncertaintySimulateIn):
    method_id: UUID | None = None
    lab_test_id: UUID | None = None
    execution_id: UUID | None = None
    equipment_id: UUID | None = None
    notes: str | None = Field(default=None, max_length=2000)


class UncertaintyCalculationOut(BaseModel):
    unit: str
    measured_value: Decimal
    lower_limit: Decimal | None = None
    upper_limit: Decimal | None = None
    lower_acceptance_limit: Decimal | None = None
    upper_acceptance_limit: Decimal | None = None
    repeatability_mean: Decimal | None = None
    repeatability_std_dev: Decimal | None = None
    repeatability_count: int = 0
    components: list[UncertaintyComponentOut]
    combined_uncertainty: Decimal
    effective_df: Decimal | None = None
    coverage_factor: Decimal
    confidence_level: Decimal
    expanded_uncertainty: Decimal
    guard_band_multiplier: Decimal
    guard_band_width: Decimal
    decision_rule: DecisionRuleType
    conformity_status: ConformityStatus
    recommended_outcome: TestOutcome
    conformity_statement: str
    formatted_result: str


class UncertaintyBudgetOut(UncertaintyCalculationOut):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    method_id: UUID | None = None
    lab_test_id: UUID | None = None
    execution_id: UUID | None = None
    equipment_id: UUID | None = None
    repeatability_readings: list[Decimal] = Field(default_factory=list)
    calculated_by_id: UUID
    calculated_by_name: str | None = None
    method_code: str | None = None
    test_name: str | None = None
    equipment_code: str | None = None
    signature_id: UUID | None = None
    notes: str | None = None
    version: int
    created_at: datetime
