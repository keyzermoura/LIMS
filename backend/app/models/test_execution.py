"""Execuções e tentativas de ensaio analítico de bancada (Fase 2 / M2.2).

Separa o planejamento do ensaio (`LabTest`) de cada tentativa real (`TestExecution`).
Repetições ou interrupções geram novas tentativas sem sobrescrever execuções anteriores,
preservando a rastreabilidade integral dos dados brutos e condições ambientais (ALCOA+).
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import (
    Base,
    JsonMetadataMixin,
    OptimisticLockMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    utcnow,
)
from app.models.enums import ExecutionStatus, TestOutcome
from app.models.types import execution_status_type, test_outcome_type

if TYPE_CHECKING:
    from app.models.equipment import LaboratoryEquipment
    from app.models.lab_test import LabTest
    from app.models.user import User


class TestExecution(
    UUIDPrimaryKeyMixin, TimestampMixin, OptimisticLockMixin, JsonMetadataMixin, Base
):
    __tablename__ = "test_executions"
    __table_args__ = (
        UniqueConstraint("lab_test_id", "execution_number", name="uq_test_execution_number"),
        Index("ix_executions_test_status", "lab_test_id", "status"),
    )

    lab_test_id: Mapped[UUID] = mapped_column(
        ForeignKey("lab_tests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    execution_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[ExecutionStatus] = mapped_column(
        execution_status_type,
        nullable=False,
        default=ExecutionStatus.EM_ANDAMENTO,
        index=True,
    )
    equipment_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("laboratory_equipment.id", ondelete="RESTRICT"), index=True
    )
    executed_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Condições ambientais na execução
    temperature_celsius: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    humidity_percent: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    pressure_hpa: Mapped[Decimal | None] = mapped_column(Numeric(7, 2))

    # Dados brutos das leituras (planilhas/curvas/amplitudes)
    raw_data: Mapped[dict[str, Any]] = mapped_column(
        nullable=False, default=dict, server_default="{}"
    )

    # Resultado apurado nesta tentativa
    result_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    result_text: Mapped[str | None] = mapped_column(String(500))
    outcome: Mapped[TestOutcome | None] = mapped_column(test_outcome_type)
    notes: Mapped[str | None] = mapped_column(Text)
    interruption_reason: Mapped[str | None] = mapped_column(Text)

    # Relacionamentos
    lab_test: Mapped[LabTest] = relationship("LabTest", back_populates="executions")
    equipment: Mapped[LaboratoryEquipment | None] = relationship(
        "LaboratoryEquipment", back_populates="executions", lazy="selectin"
    )
    executed_by: Mapped[User | None] = relationship("User", lazy="selectin")

    @property
    def attempt_label(self) -> str:
        return f"Tentativa #{self.execution_number}"

    def __repr__(self) -> str:
        return f"<TestExecution test={self.lab_test_id} run={self.execution_number} ({self.status.value})>"
