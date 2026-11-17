"""Modelo de Investigação de Desvios Analíticos OOS e OOT (Fase 7 / H2.2).

Implementa os requisitos de conformidade:
- FDA Guidance for Industry: Investigating Out-of-Specification (OOS) Test Results.
- ISO/IEC 17025:2017 (§7.10 - Gestão de Trabalho Não Conforme).
- 21 CFR Part 11 (Rastreabilidade e integridade ALCOA+).
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import (
    Base,
    JsonMetadataMixin,
    OptimisticLockMixin,
    PortableJSON,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    utcnow,
)
from app.models.enums import (
    DeviationType,
    OOSInvestigationStatus,
    OOSRootCauseCategory,
)
from app.models.types import (
    deviation_type_enum,
    oos_investigation_status_enum,
    oos_root_cause_category_enum,
)

if TYPE_CHECKING:
    from app.models.capa_action import CapaAction
    from app.models.lab_test import LabTest
    from app.models.test_execution import TestExecution
    from app.models.user import User


class OOSInvestigation(
    UUIDPrimaryKeyMixin, TimestampMixin, OptimisticLockMixin, JsonMetadataMixin, Base
):
    """Registro formal de investigação de resultado fora de especificação ou de tendência."""

    __tablename__ = "oos_investigations"

    investigation_number: Mapped[str] = mapped_column(
        String(32), unique=True, nullable=False, index=True
    )
    lab_test_id: Mapped[UUID] = mapped_column(
        ForeignKey("lab_tests.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    execution_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("test_executions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    deviation_type: Mapped[DeviationType] = mapped_column(
        deviation_type_enum, nullable=False, default=DeviationType.OOS, index=True
    )
    status: Mapped[OOSInvestigationStatus] = mapped_column(
        oos_investigation_status_enum,
        nullable=False,
        default=OOSInvestigationStatus.PHASE_I_PENDING,
        index=True,
    )

    # Resultados e limites de especificação
    initial_result: Mapped[float | None] = mapped_column(Float, nullable=True)
    initial_result_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    specification_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    specification_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    specification_text: Mapped[str | None] = mapped_column(String(255), nullable=True)

    detected_by_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now()
    )

    # -----------------------------------------------------------------------
    # FASE I: Investigação Laboratorial Imediata (FDA / ISO 17025 §7.10)
    # -----------------------------------------------------------------------
    phase_1_checklist: Mapped[dict[str, Any]] = mapped_column(
        PortableJSON, nullable=False, default=dict, server_default="{}"
    )
    phase_1_conclusion: Mapped[str | None] = mapped_column(Text, nullable=True)
    phase_1_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    phase_1_responsible_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # -----------------------------------------------------------------------
    # FASE II: Investigação Sistêmica, Re-ensaio e Causa Raiz
    # -----------------------------------------------------------------------
    phase_2_required: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    phase_2_plan: Mapped[str | None] = mapped_column(Text, nullable=True)
    phase_2_retest_results: Mapped[list[Any]] = mapped_column(
        PortableJSON, nullable=False, default=list, server_default="[]"
    )
    root_cause_category: Mapped[OOSRootCauseCategory | None] = mapped_column(
        oos_root_cause_category_enum, nullable=True, index=True
    )
    root_cause_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    capa_action_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("capa_actions.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Conclusão e Encerramento
    final_disposition: Mapped[str | None] = mapped_column(Text, nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relacionamentos
    lab_test: Mapped[LabTest] = relationship("LabTest", lazy="selectin")
    execution: Mapped[TestExecution | None] = relationship("TestExecution", lazy="selectin")
    detected_by: Mapped[User] = relationship("User", foreign_keys=[detected_by_id], lazy="selectin")
    phase_1_responsible: Mapped[User | None] = relationship(
        "User", foreign_keys=[phase_1_responsible_id], lazy="selectin"
    )
    closed_by: Mapped[User | None] = relationship(
        "User", foreign_keys=[closed_by_id], lazy="selectin"
    )
    capa_action: Mapped[CapaAction | None] = relationship("CapaAction", lazy="selectin")

    @property
    def is_open(self) -> bool:
        return self.status != OOSInvestigationStatus.CLOSED

    def __repr__(self) -> str:
        return f"<OOSInvestigation {self.investigation_number} status={self.status.value}>"
