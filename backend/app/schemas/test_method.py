"""Schemas para Catálogo de Métodos de Ensaio."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TestMethodBase(BaseModel):
    code: str = Field(min_length=2, max_length=64, description="Código único do método, ex: MET-ELETRO-01")
    name: str = Field(min_length=2, max_length=200, description="Nome oficial do método")
    standard: str = Field(min_length=2, max_length=120, description="Norma técnica (ex: ABNT NBR IEC 60601-1)")
    version: int = Field(default=1, ge=1)
    category: str | None = Field(default=None, max_length=100, description="Categoria técnica")
    description: str | None = Field(default=None, max_length=2000)
    parameters_schema: dict[str, Any] = Field(default_factory=dict)
    default_unit: str = Field(default="UN", max_length=32)
    default_lower_limit: Decimal | None = None
    default_upper_limit: Decimal | None = None
    default_acceptance_criteria: str | None = Field(default=None, max_length=2000)
    is_active: bool = True

    @model_validator(mode="after")
    def _validate_limits(self) -> TestMethodBase:
        if (
            self.default_lower_limit is not None
            and self.default_upper_limit is not None
            and self.default_lower_limit > self.default_upper_limit
        ):
            raise ValueError("Limite inferior padrão não pode ser maior que o superior.")
        return self


class TestMethodCreate(TestMethodBase):
    pass


class TestMethodUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    standard: str | None = Field(default=None, min_length=2, max_length=120)
    category: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = None
    parameters_schema: dict[str, Any] | None = None
    default_unit: str | None = None
    default_lower_limit: Decimal | None = None
    default_upper_limit: Decimal | None = None
    default_acceptance_criteria: str | None = None
    is_active: bool | None = None


class TestMethodOut(TestMethodBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
