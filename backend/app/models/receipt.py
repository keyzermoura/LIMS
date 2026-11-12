"""Modelos de Recebimento, Itens e Objetos de Custódia (M0.3).

Garante a separação entre chegada física, conferência e criação da amostra operacional.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
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
    ConferenceStatus,
    CustodyEventType,
    CustodyObjectStatus,
    PresentationStatus,
    ReceiptDecisionEnum,
    ReceiptStatus,
)
from app.models.types import (
    conference_status_type,
    custody_event_type,
    custody_object_status_type,
    presentation_status_type,
    receipt_decision_type,
    receipt_status_type,
)

if TYPE_CHECKING:
    from app.models.checklist import ChecklistAnswer
    from app.models.decision import ReceiptDecision
    from app.models.device_sample import DeviceSample
    from app.models.solicitation import Solicitation, SolicitationItem
    from app.models.user import User


class Receipt(
    UUIDPrimaryKeyMixin, TimestampMixin, OptimisticLockMixin, JsonMetadataMixin, Base
):
    """Registro único de chegada física principal vinculada à solicitação."""

    __tablename__ = "receipts"

    solicitation_id: Mapped[UUID] = mapped_column(
        ForeignKey("solicitations.id", ondelete="RESTRICT"),
        unique=True,
        nullable=False,
        index=True,
    )
    receipt_number: Mapped[str] = mapped_column(
        String(32), unique=True, nullable=False, index=True
    )
    arrived_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    received_by_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    arrival_location: Mapped[str | None] = mapped_column(String(255))
    external_protocol: Mapped[str | None] = mapped_column(String(120), index=True)
    delivery_method: Mapped[str | None] = mapped_column(String(100))
    packaging_condition: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(Text)

    status: Mapped[ReceiptStatus] = mapped_column(
        receipt_status_type,
        nullable=False,
        default=ReceiptStatus.REGISTRADO,
        index=True,
    )

    # Relacionamentos
    solicitation: Mapped[Solicitation] = relationship("Solicitation", back_populates="receipt")
    received_by: Mapped[User] = relationship("User", foreign_keys=[received_by_id], lazy="selectin")
    items: Mapped[list[ReceiptItem]] = relationship(
        "ReceiptItem", back_populates="receipt", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Receipt {self.receipt_number} {self.status.value}>"


class ReceiptItem(UUIDPrimaryKeyMixin, TimestampMixin, OptimisticLockMixin, Base):
    """Situação de apresentação e conferência individual de um item declarado."""

    __tablename__ = "receipt_items"

    receipt_id: Mapped[UUID] = mapped_column(
        ForeignKey("receipts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    solicitation_item_id: Mapped[UUID] = mapped_column(
        ForeignKey("solicitation_items.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    presentation_status: Mapped[PresentationStatus] = mapped_column(
        presentation_status_type,
        nullable=False,
        default=PresentationStatus.PRESENTED,
    )
    presented_quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 4), nullable=False, default=Decimal(0)
    )
    conference_status: Mapped[ConferenceStatus] = mapped_column(
        conference_status_type,
        nullable=False,
        default=ConferenceStatus.PENDENTE,
    )
    decision: Mapped[ReceiptDecisionEnum | None] = mapped_column(receipt_decision_type)
    notes: Mapped[str | None] = mapped_column(Text)

    # Relacionamentos
    receipt: Mapped[Receipt] = relationship("Receipt", back_populates="items")
    solicitation_item: Mapped[SolicitationItem] = relationship("SolicitationItem", lazy="selectin")
    custody_objects: Mapped[list[CustodyObject]] = relationship(
        "CustodyObject", back_populates="receipt_item", cascade="all, delete-orphan", lazy="selectin"
    )
    checklist_answers: Mapped[list[ChecklistAnswer]] = relationship(
        "ChecklistAnswer", back_populates="receipt_item", cascade="all, delete-orphan", lazy="selectin"
    )
    decisions: Mapped[list[ReceiptDecision]] = relationship(
        "ReceiptDecision", back_populates="receipt_item", lazy="selectin"
    )


class CustodyObject(
    UUIDPrimaryKeyMixin, TimestampMixin, OptimisticLockMixin, JsonMetadataMixin, Base
):
    """Material sob custódia física desde a chegada (individual ou agrupamento homogêneo)."""

    __tablename__ = "custody_objects"

    receipt_item_id: Mapped[UUID] = mapped_column(
        ForeignKey("receipt_items.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    object_code: Mapped[str] = mapped_column(
        String(32), unique=True, nullable=False, index=True
    )
    grouping_description: Mapped[str | None] = mapped_column(String(500))
    represented_quantity: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    current_location: Mapped[str | None] = mapped_column(String(255))
    seal_number: Mapped[str | None] = mapped_column(String(120), index=True)

    status: Mapped[CustodyObjectStatus] = mapped_column(
        custody_object_status_type,
        nullable=False,
        default=CustodyObjectStatus.SOB_GUARDA,
        index=True,
    )
    current_custodian_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    linked_device_sample_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("device_samples.id", ondelete="SET NULL"), unique=True, index=True
    )

    # Relacionamentos
    receipt_item: Mapped[ReceiptItem] = relationship("ReceiptItem", back_populates="custody_objects")
    current_custodian: Mapped[User | None] = relationship("User", foreign_keys=[current_custodian_id], lazy="selectin")
    linked_device_sample: Mapped[DeviceSample | None] = relationship(
        "DeviceSample", foreign_keys=[linked_device_sample_id], lazy="selectin"
    )
    custody_events: Mapped[list[CustodyEvent]] = relationship(
        "CustodyEvent", back_populates="custody_object", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<CustodyObject {self.object_code} ({self.status.value})>"


class CustodyEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Evento append-only de custódia física vinculado ao ObjetoCustodia."""

    __tablename__ = "custody_events"

    custody_object_id: Mapped[UUID] = mapped_column(
        ForeignKey("custody_objects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[CustodyEventType] = mapped_column(
        custody_event_type, nullable=False, default=CustodyEventType.INGRESSO
    )
    effective_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    from_custodian_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    to_custodian_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    from_location: Mapped[str | None] = mapped_column(String(255))
    to_location: Mapped[str | None] = mapped_column(String(255))
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    registered_by_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )

    # Relacionamentos
    custody_object: Mapped[CustodyObject] = relationship("CustodyObject", back_populates="custody_events")
    from_custodian: Mapped[User | None] = relationship("User", foreign_keys=[from_custodian_id], lazy="selectin")
    to_custodian: Mapped[User | None] = relationship("User", foreign_keys=[to_custodian_id], lazy="selectin")
    registered_by: Mapped[User] = relationship("User", foreign_keys=[registered_by_id], lazy="selectin")
