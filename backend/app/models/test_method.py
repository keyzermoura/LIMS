"""Catálogo de métodos analíticos e normas técnicas (Fase 2 / M2.1).

Define métodos de ensaio controlados (ex.: ABNT NBR IEC 60601-1), versão,
parâmetros padronizados e limites de aceitação.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import (
    Base,
    JsonMetadataMixin,
    OptimisticLockMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)

if TYPE_CHECKING:
    from app.models.lab_test import LabTest


class TestMethod(
    UUIDPrimaryKeyMixin, TimestampMixin, OptimisticLockMixin, JsonMetadataMixin, Base
):
    __tablename__ = "test_methods"

    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    standard: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    category: Mapped[str | None] = mapped_column(String(100), index=True)
    description: Mapped[str | None] = mapped_column(Text)

    parameters_schema: Mapped[dict[str, Any]] = mapped_column(
        nullable=False, default=dict, server_default="{}"
    )
    default_unit: Mapped[str] = mapped_column(String(32), nullable=False, default="UN")
    default_lower_limit: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    default_upper_limit: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    default_acceptance_criteria: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    # Relacionamento com os ensaios planejados que usam este método
    lab_tests: Mapped[list[LabTest]] = relationship("LabTest", back_populates="test_method")

    def __repr__(self) -> str:
        return f"<TestMethod {self.code} v{self.version}: {self.name}>"
