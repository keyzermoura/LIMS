"""Modelos de Orçamento de Incerteza de Medição GUM e Regras de Decisão ILAC-G8 (Sprint 4.2).

Implementa os requisitos da ISO/IEC 17025:2017 (§7.6 - Avaliação da Incerteza de Medição
e §7.8.6 - Relato de Declarações de Conformidade), JCGM 100:2008 (GUM) e ILAC-G8:09/2019.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import (
    Base,
    JsonMetadataMixin,
    OptimisticLockMixin,
    PortableJSON,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from app.models.enums import ConformityStatus, DecisionRuleType, TestOutcome
from app.models.types import (
    conformity_status_type,
    decision_rule_type,
    test_outcome_type,
)

if TYPE_CHECKING:
    from app.models.electronic_signature import ElectronicSignature
    from app.models.equipment import LaboratoryEquipment
    from app.models.lab_test import LabTest
    from app.models.test_execution import TestExecution
    from app.models.test_method import TestMethod
    from app.models.user import User


class UncertaintyBudget(
    UUIDPrimaryKeyMixin, TimestampMixin, OptimisticLockMixin, JsonMetadataMixin, Base
):
    """Orçamento de incerteza metrológica GUM e avaliação de conformidade com faixa de guarda."""

    __tablename__ = "uncertainty_budgets"

    method_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("test_methods.id", ondelete="SET NULL"), index=True
    )
    lab_test_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("lab_tests.id", ondelete="CASCADE"), index=True
    )
    execution_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("test_executions.id", ondelete="SET NULL"), index=True
    )
    equipment_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("laboratory_equipment.id", ondelete="SET NULL"), index=True
    )

    unit: Mapped[str] = mapped_column(String(32), nullable=False, default="UN")
    measured_value: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    lower_limit: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    upper_limit: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))

    repeatability_readings: Mapped[list[Any]] = mapped_column(
        PortableJSON, nullable=False, default=list, server_default="[]"
    )
    components: Mapped[list[dict[str, Any]]] = mapped_column(
        PortableJSON, nullable=False, default=list, server_default="[]"
    )

    combined_uncertainty: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    effective_df: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    coverage_factor: Mapped[Decimal] = mapped_column(
        Numeric(6, 3), nullable=False, default=Decimal("2.000")
    )
    confidence_level: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("95.45")
    )
    expanded_uncertainty: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)

    guard_band_multiplier: Mapped[Decimal] = mapped_column(
        Numeric(6, 3), nullable=False, default=Decimal("1.000")
    )
    guard_band_width: Mapped[Decimal] = mapped_column(
        Numeric(18, 6), nullable=False, default=Decimal("0.000000")
    )
    decision_rule: Mapped[DecisionRuleType] = mapped_column(
        decision_rule_type,
        nullable=False,
        default=DecisionRuleType.GUARD_BAND_CONSERVATIVE,
    )
    conformity_status: Mapped[ConformityStatus] = mapped_column(
        conformity_status_type, nullable=False, index=True
    )
    recommended_outcome: Mapped[TestOutcome] = mapped_column(test_outcome_type, nullable=False)
    conformity_statement: Mapped[str] = mapped_column(Text, nullable=False)

    calculated_by_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    signature_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("electronic_signatures.id", ondelete="RESTRICT")
    )
    notes: Mapped[str | None] = mapped_column(Text)

    # Relacionamentos
    method: Mapped[TestMethod | None] = relationship(
        "TestMethod", foreign_keys=[method_id], lazy="selectin"
    )
    lab_test: Mapped[LabTest | None] = relationship(
        "LabTest", foreign_keys=[lab_test_id], lazy="selectin"
    )
    execution: Mapped[TestExecution | None] = relationship(
        "TestExecution", foreign_keys=[execution_id], lazy="selectin"
    )
    equipment: Mapped[LaboratoryEquipment | None] = relationship(
        "LaboratoryEquipment", foreign_keys=[equipment_id], lazy="selectin"
    )
    calculated_by: Mapped[User] = relationship(
        "User", foreign_keys=[calculated_by_id], lazy="selectin"
    )
    signature: Mapped[ElectronicSignature | None] = relationship(
        "ElectronicSignature", foreign_keys=[signature_id], lazy="selectin"
    )

    def __repr__(self) -> str:
        return (
            f"<UncertaintyBudget value={self.measured_value} "
            f"U={self.expanded_uncertainty} {self.unit} status={self.conformity_status.value}>"
        )
