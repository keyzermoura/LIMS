"""Equipamentos laboratoriais e controle de situação metrológica (Fase 2 / M2.1).

Rastreia instrumentos, calibrações vigentes, certificados e validade,
permitindo o bloqueio de uso quando a calibração expirar (ALCOA+ / ISO 17025).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import (
    Base,
    JsonMetadataMixin,
    OptimisticLockMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    utcnow,
)
from app.models.enums import EquipmentCalibrationStatus
from app.models.types import equipment_calibration_status_type

if TYPE_CHECKING:
    from app.models.test_execution import TestExecution


class LaboratoryEquipment(
    UUIDPrimaryKeyMixin, TimestampMixin, OptimisticLockMixin, JsonMetadataMixin, Base
):
    __tablename__ = "laboratory_equipment"
    __table_args__ = (
        Index("ix_equipment_status_due", "calibration_status", "calibration_due_date"),
    )

    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    equipment_type: Mapped[str | None] = mapped_column(String(100), index=True)
    manufacturer: Mapped[str | None] = mapped_column(String(160))
    model: Mapped[str | None] = mapped_column(String(120))
    serial_number: Mapped[str | None] = mapped_column(String(120), index=True)
    location: Mapped[str | None] = mapped_column(String(160))

    calibration_status: Mapped[EquipmentCalibrationStatus] = mapped_column(
        equipment_calibration_status_type,
        nullable=False,
        default=EquipmentCalibrationStatus.CALIBRADO,
        server_default="CALIBRADO",
        index=True,
    )
    last_calibration_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    calibration_due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    certificate_number: Mapped[str | None] = mapped_column(String(120))
    calibration_agency: Mapped[str | None] = mapped_column(String(200))
    notes: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    executions: Mapped[list[TestExecution]] = relationship("TestExecution", back_populates="equipment")

    @property
    def is_calibration_valid(self) -> bool:
        """Verifica se a calibração metrológica está em vigor."""
        if self.calibration_status == EquipmentCalibrationStatus.NAO_APLICAVEL:
            return True
        if self.calibration_status != EquipmentCalibrationStatus.CALIBRADO:
            return False
        if self.calibration_due_date is None:
            return False
        due = self.calibration_due_date
        now = utcnow()
        if due.tzinfo is None:
            due = due.replace(tzinfo=UTC)
        return due >= now

    def __repr__(self) -> str:
        return f"<LaboratoryEquipment {self.code}: {self.name} ({self.calibration_status.value})>"
