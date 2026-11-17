"""Modelos de Controle Estatístico de Processo (CEP / SPC) e Westgard (H2.5).

Implementa os requisitos de controle de qualidade analítico:
- ISO/IEC 17025:2017 §7.7 (Garantia da validade dos resultados)
- Regras múltiplas de Westgard (1_2s, 1_3s, 2_2s, R_4s, 4_1s, 10_x)
- Cartas de controle Levey-Jennings com limites de alerta (±2s) e ação (±3s)
- Intertravamento com liberação de laudos oficiais
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
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
from app.models.enums import QCStatus
from app.models.types import qc_status_enum

if TYPE_CHECKING:
    from app.models.equipment import LaboratoryEquipment
    from app.models.reagent import ReagentBatch
    from app.models.test_method import TestMethod
    from app.models.user import User


class QCRun(UUIDPrimaryKeyMixin, TimestampMixin, OptimisticLockMixin, JsonMetadataMixin, Base):
    """Corrida analítica de amostra de controle de qualidade interno (CQI / CRM)."""

    __tablename__ = "qc_runs"

    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    method_id: Mapped[UUID] = mapped_column(
        ForeignKey("test_methods.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    equipment_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("laboratory_equipment.id", ondelete="SET NULL"), nullable=True, index=True
    )
    reagent_batch_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("reagent_batches.id", ondelete="SET NULL"), nullable=True, index=True
    )
    operator_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    run_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now()
    )

    # Parâmetros Nominais do Ensaio / Padrão Analítico
    target_mean: Mapped[float] = mapped_column(Float, nullable=False)
    target_sd: Mapped[float] = mapped_column(Float, nullable=False)
    measured_value: Mapped[float] = mapped_column(Float, nullable=False)
    z_score: Mapped[float] = mapped_column(Float, nullable=False)

    # Avaliação Multiregra de Westgard
    status: Mapped[QCStatus] = mapped_column(
        qc_status_enum,
        nullable=False,
        default=QCStatus.CONFORMING,
        server_default=QCStatus.CONFORMING.value,
        index=True,
    )
    violation_rules: Mapped[list[str]] = mapped_column(
        PortableJSON, nullable=False, default=list, server_default="[]"
    )
    is_active_violation: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false", index=True
    )
    corrective_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relacionamentos
    method: Mapped[TestMethod] = relationship("TestMethod", lazy="selectin")
    equipment: Mapped[LaboratoryEquipment | None] = relationship(
        "LaboratoryEquipment", lazy="selectin"
    )
    reagent_batch: Mapped[ReagentBatch | None] = relationship("ReagentBatch", lazy="selectin")
    operator: Mapped[User] = relationship("User", foreign_keys=[operator_id], lazy="selectin")

    def __repr__(self) -> str:
        return f"<QCRun {self.code}: val={self.measured_value} z={self.z_score:.2f} status={self.status.value}>"
