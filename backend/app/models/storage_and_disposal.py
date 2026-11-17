"""Modelos de Cadeia Física de Armazenamento, Retenção de Contraprova e Termo de Descarte (H2.3 & H2.4).

Implementa os requisitos:
- Rastreamento térmico e físico de locais de custódia (Freezer -80ºC, 2-8ºC, Sala 15-25ºC).
- Guarda de Contraprova Pericial inviolável com controle de lacre e data limite legal (ISO 17025 §7.4).
- Descarte Irreversível com Dupla Assinatura Eletrônica (21 CFR Part 11 e RDC 665/2022).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import (
    Base,
    JsonMetadataMixin,
    OptimisticLockMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    utcnow,
)
from app.models.enums import (
    DisposalMethod,
    RetentionStatus,
    RetentionType,
    StorageLocationType,
)
from app.models.types import (
    disposal_method_enum,
    retention_status_enum,
    retention_type_enum,
    storage_location_type_enum,
)

if TYPE_CHECKING:
    from app.models.device_sample import DeviceSample
    from app.models.electronic_signature import ElectronicSignature
    from app.models.user import User


class StorageLocation(
    UUIDPrimaryKeyMixin, TimestampMixin, OptimisticLockMixin, JsonMetadataMixin, Base
):
    """Local físico de custódia com controle térmico e ambiental."""

    __tablename__ = "storage_locations"

    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    location_type: Mapped[StorageLocationType] = mapped_column(
        storage_location_type_enum, nullable=False, index=True
    )
    room: Mapped[str] = mapped_column(String(64), nullable=False)
    temperature_target_celsius: Mapped[float] = mapped_column(Float, nullable=False)
    temperature_min_celsius: Mapped[float] = mapped_column(Float, nullable=False)
    temperature_max_celsius: Mapped[float] = mapped_column(Float, nullable=False)
    humidity_max_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    capacity_units: Mapped[int] = mapped_column(
        Integer, nullable=False, default=100, server_default="100"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )

    movements_to: Mapped[list[SampleStorageMovement]] = relationship(
        "SampleStorageMovement",
        back_populates="to_location",
        foreign_keys="SampleStorageMovement.to_location_id",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<StorageLocation {self.code}: {self.name} ({self.location_type.value})>"


class SampleStorageMovement(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Histórico de transferências físicas de custódia e movimentações de amostra."""

    __tablename__ = "sample_storage_movements"

    sample_id: Mapped[UUID] = mapped_column(
        ForeignKey("device_samples.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    from_location_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("storage_locations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    to_location_id: Mapped[UUID] = mapped_column(
        ForeignKey("storage_locations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    moved_by_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    moved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now()
    )
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    temperature_at_movement: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    sample: Mapped[DeviceSample] = relationship("DeviceSample", lazy="selectin")
    from_location: Mapped[StorageLocation | None] = relationship(
        "StorageLocation", foreign_keys=[from_location_id], lazy="selectin"
    )
    to_location: Mapped[StorageLocation] = relationship(
        "StorageLocation",
        foreign_keys=[to_location_id],
        back_populates="movements_to",
        lazy="selectin",
    )
    moved_by: Mapped[User] = relationship("User", foreign_keys=[moved_by_id], lazy="selectin")

    def __repr__(self) -> str:
        return f"<StorageMovement sample={self.sample_id} to={self.to_location_id}>"


class SampleRetention(UUIDPrimaryKeyMixin, TimestampMixin, OptimisticLockMixin, Base):
    """Guarda formal de contraprova pericial ou testemunha de lote (ISO 17025 §7.4)."""

    __tablename__ = "sample_retentions"

    sample_id: Mapped[UUID] = mapped_column(
        ForeignKey("device_samples.id", ondelete="RESTRICT"),
        unique=True,
        nullable=False,
        index=True,
    )
    storage_location_id: Mapped[UUID] = mapped_column(
        ForeignKey("storage_locations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    retention_type: Mapped[RetentionType] = mapped_column(
        retention_type_enum,
        nullable=False,
        default=RetentionType.CONTRAPROVA_PERICIAL,
        index=True,
    )
    retained_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now()
    )
    retain_until: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    quantity_retained: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(16), nullable=False, default="un")
    seal_number: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[RetentionStatus] = mapped_column(
        retention_status_enum,
        nullable=False,
        default=RetentionStatus.ACTIVE,
        index=True,
    )
    responsible_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    sample: Mapped[DeviceSample] = relationship("DeviceSample", lazy="selectin")
    storage_location: Mapped[StorageLocation] = relationship("StorageLocation", lazy="selectin")
    responsible: Mapped[User] = relationship("User", foreign_keys=[responsible_id], lazy="selectin")

    @property
    def is_expired(self) -> bool:
        return date.today() > self.retain_until

    def __repr__(self) -> str:
        return f"<SampleRetention seal={self.seal_number} until={self.retain_until} status={self.status.value}>"


class SampleDisposalRecord(UUIDPrimaryKeyMixin, TimestampMixin, OptimisticLockMixin, Base):
    """Termo de Descarte Irreversível com Dupla Assinatura Eletrônica (21 CFR Part 11)."""

    __tablename__ = "sample_disposal_records"

    sample_id: Mapped[UUID] = mapped_column(
        ForeignKey("device_samples.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    retention_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("sample_retentions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    disposal_manifest_number: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    disposal_method: Mapped[DisposalMethod] = mapped_column(
        disposal_method_enum, nullable=False, index=True
    )
    disposed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now()
    )
    disposed_by_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    witness_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    primary_signature_id: Mapped[UUID] = mapped_column(
        ForeignKey("electronic_signatures.id", ondelete="RESTRICT"), nullable=False
    )
    witness_signature_id: Mapped[UUID] = mapped_column(
        ForeignKey("electronic_signatures.id", ondelete="RESTRICT"), nullable=False
    )
    environmental_license_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    waste_company_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    sample: Mapped[DeviceSample] = relationship("DeviceSample", lazy="selectin")
    retention: Mapped[SampleRetention | None] = relationship("SampleRetention", lazy="selectin")
    disposed_by: Mapped[User] = relationship("User", foreign_keys=[disposed_by_id], lazy="selectin")
    witness: Mapped[User] = relationship("User", foreign_keys=[witness_id], lazy="selectin")
    primary_signature: Mapped[ElectronicSignature] = relationship(
        "ElectronicSignature", foreign_keys=[primary_signature_id], lazy="selectin"
    )
    witness_signature: Mapped[ElectronicSignature] = relationship(
        "ElectronicSignature", foreign_keys=[witness_signature_id], lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<SampleDisposal manifest={self.disposal_manifest_number} method={self.disposal_method.value}>"
