"""Modelos de Reagentes, Padrões Analíticos (CRMs) e Consumo em Bancada (Fase 7 / H2.1).

Atende aos requisitos da ISO/IEC 17025:2017 (§6.4 e §6.5):
- Rastreabilidade metrológica de Materiais de Referência Certificados (MRC/CRM).
- Controle de lote, abertura, validade e incerteza do padrão.
- Rastreabilidade de consumo associada às execuções de ensaio (ALCOA+).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import (
    Base,
    JsonMetadataMixin,
    OptimisticLockMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    utcnow,
)
from app.models.enums import ReagentBatchStatus, ReagentGrade, ReagentType
from app.models.types import (
    reagent_batch_status_enum,
    reagent_grade_enum,
    reagent_type_enum,
)

if TYPE_CHECKING:
    from app.models.test_execution import TestExecution
    from app.models.user import User


class Reagent(
    UUIDPrimaryKeyMixin, TimestampMixin, OptimisticLockMixin, JsonMetadataMixin, Base
):
    """Catálogo mestre de reagentes químicos, padrões analíticos e consumíveis."""

    __tablename__ = "reagents"

    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    chemical_formula: Mapped[str | None] = mapped_column(String(64), nullable=True)
    cas_number: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    reagent_type: Mapped[ReagentType] = mapped_column(
        reagent_type_enum, nullable=False, index=True
    )
    grade: Mapped[ReagentGrade] = mapped_column(
        reagent_grade_enum, nullable=False, default=ReagentGrade.PA
    )
    storage_temperature_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    storage_temperature_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    hazard_classification: Mapped[str | None] = mapped_column(String(120), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )

    batches: Mapped[list[ReagentBatch]] = relationship(
        "ReagentBatch", back_populates="reagent", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Reagent {self.code}: {self.name} ({self.reagent_type.value})>"


class ReagentBatch(UUIDPrimaryKeyMixin, TimestampMixin, OptimisticLockMixin, Base):
    """Lote individual físico de um reagente ou padrão de referência com prazo de validade."""

    __tablename__ = "reagent_batches"

    reagent_id: Mapped[UUID] = mapped_column(
        ForeignKey("reagents.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    lot_number: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    manufacturer: Mapped[str] = mapped_column(String(120), nullable=False)
    catalog_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now()
    )
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expiration_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    initial_quantity: Mapped[float] = mapped_column(Float, nullable=False)
    current_quantity: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(16), nullable=False, default="g")

    # Metrologia e Rastreabilidade CRM (ISO 17025 §6.5)
    certificate_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    uncertainty_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    k_factor: Mapped[float | None] = mapped_column(Float, nullable=True, default=2.0)

    status: Mapped[ReagentBatchStatus] = mapped_column(
        reagent_batch_status_enum,
        nullable=False,
        default=ReagentBatchStatus.AVAILABLE,
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    reagent: Mapped[Reagent] = relationship("Reagent", back_populates="batches", lazy="selectin")

    @property
    def is_expired(self) -> bool:
        return date.today() > self.expiration_date

    @property
    def is_usable(self) -> bool:
        return (
            self.status in (ReagentBatchStatus.AVAILABLE, ReagentBatchStatus.IN_USE)
            and not self.is_expired
            and self.current_quantity > 0
        )

    def __repr__(self) -> str:
        return f"<ReagentBatch {self.lot_number}: exp={self.expiration_date} status={self.status.value}>"


class TestExecutionReagentUsage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Registro de insumo analítico consumido durante a execução de um ensaio de bancada."""

    __tablename__ = "test_execution_reagent_usages"

    execution_id: Mapped[UUID] = mapped_column(
        ForeignKey("test_executions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    batch_id: Mapped[UUID] = mapped_column(
        ForeignKey("reagent_batches.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    quantity_used: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(16), nullable=False)
    consumed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now()
    )
    recorded_by_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )

    batch: Mapped[ReagentBatch] = relationship("ReagentBatch", lazy="selectin")
    recorded_by: Mapped[User] = relationship("User", lazy="selectin")
    execution: Mapped[TestExecution] = relationship("TestExecution", lazy="selectin")

    def __repr__(self) -> str:
        return f"<ReagentUsage exec={self.execution_id} batch={self.batch_id} qtd={self.quantity_used}{self.unit}>"
