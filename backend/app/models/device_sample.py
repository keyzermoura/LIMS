"""Amostra de dispositivo médico apreendida/coletada no mercado."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import (
    Base,
    JsonMetadataMixin,
    OptimisticLockMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    utcnow,
)
from app.models.enums import SampleStatus
from app.models.types import sample_status_type


class DeviceSample(
    UUIDPrimaryKeyMixin, TimestampMixin, OptimisticLockMixin, JsonMetadataMixin, Base
):
    __tablename__ = "device_samples"
    __table_args__ = (
        UniqueConstraint(
            "serial_number",
            "lot_number",
            "manufacturer",
            name="uq_device_sample_identity",
        ),
    )

    accession_number: Mapped[str] = mapped_column(
        String(32), unique=True, nullable=False, index=True
    )
    serial_number: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    lot_number: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    manufacturer: Mapped[str] = mapped_column(String(160), nullable=False)
    commercial_name: Mapped[str] = mapped_column(String(200), nullable=False)
    model: Mapped[str | None] = mapped_column(String(120))
    registration_number: Mapped[str | None] = mapped_column(
        String(64), comment="Registro ANVISA (ex.: 80012345678)"
    )
    description: Mapped[str | None] = mapped_column(Text)

    solicitation_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("solicitations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    origin_custody_object_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("custody_objects.id", ondelete="SET NULL"), nullable=True, index=True
    )

    status: Mapped[SampleStatus] = mapped_column(
        sample_status_type,
        nullable=False,
        default=SampleStatus.RECEBIDO,
        index=True,
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    received_by_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    current_custodian_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    current_location: Mapped[str | None] = mapped_column(String(160))

    # Relação many-to-one carregada via JOIN — evita lazy load em async.
    current_custodian = relationship(
        "User", foreign_keys=[current_custodian_id], lazy="selectin"
    )
    received_by = relationship(
        "User", foreign_keys=[received_by_id], lazy="selectin"
    )

    @property
    def qr_identifier(self) -> str:
        return self.accession_number

    def __repr__(self) -> str:  # pragma: no cover
        return f"<DeviceSample {self.accession_number} {self.status.value}>"
