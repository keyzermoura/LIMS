"""Modelos de Solicitação e Itens Declarados (M0.3).

Representa a demanda cadastrada antes da chegada física do material.
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
)
from app.models.enums import SolicitationStatus
from app.models.types import solicitation_status_type

if TYPE_CHECKING:
    from app.models.receipt import Receipt
    from app.models.user import User


class Solicitation(
    UUIDPrimaryKeyMixin, TimestampMixin, OptimisticLockMixin, JsonMetadataMixin, Base
):
    """Demanda institucional de fiscalização ou ensaio laboratorial."""

    __tablename__ = "solicitations"

    solicitation_number: Mapped[str] = mapped_column(
        String(32), unique=True, nullable=False, index=True
    )
    requester_name: Mapped[str] = mapped_column(String(160), nullable=False)
    requester_email: Mapped[str | None] = mapped_column(String(255))
    requester_document: Mapped[str | None] = mapped_column(String(64))
    requester_organization: Mapped[str | None] = mapped_column(String(200))

    created_by_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    purpose: Mapped[str | None] = mapped_column(Text)
    request_type: Mapped[str] = mapped_column(String(64), nullable=False, default="FISCALIZACAO")
    priority: Mapped[str] = mapped_column(String(32), nullable=False, default="NORMAL")

    status: Mapped[SolicitationStatus] = mapped_column(
        solicitation_status_type,
        nullable=False,
        default=SolicitationStatus.RASCUNHO,
        index=True,
    )
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relacionamentos
    created_by: Mapped[User] = relationship("User", foreign_keys=[created_by_id], lazy="selectin")
    items: Mapped[list[SolicitationItem]] = relationship(
        "SolicitationItem", back_populates="solicitation", cascade="all, delete-orphan", lazy="selectin"
    )
    receipt: Mapped[Receipt | None] = relationship(
        "Receipt", back_populates="solicitation", uselist=False, lazy="selectin"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Solicitation {self.solicitation_number} {self.status.value}>"


class SolicitationItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Item/dispositivo declarado no âmbito de uma solicitação."""

    __tablename__ = "solicitation_items"

    solicitation_id: Mapped[UUID] = mapped_column(
        ForeignKey("solicitations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    item_number: Mapped[int] = mapped_column(nullable=False, default=1)
    product_name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str | None] = mapped_column(String(100))
    manufacturer: Mapped[str | None] = mapped_column(String(160))
    model: Mapped[str | None] = mapped_column(String(120))
    serial_number: Mapped[str | None] = mapped_column(String(120))
    lot_number: Mapped[str | None] = mapped_column(String(120))
    declared_quantity: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(32), nullable=False, default="UN")
    notes: Mapped[str | None] = mapped_column(Text)

    # Relacionamentos
    solicitation: Mapped[Solicitation] = relationship("Solicitation", back_populates="items")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<SolicitationItem {self.item_number}: {self.product_name} ({self.declared_quantity} {self.unit_of_measure})>"
