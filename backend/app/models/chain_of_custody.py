"""Cadeia de custódia — registro imutável de cada transferência de guarda."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, desc
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, utcnow


class ChainOfCustody(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Evento append-only: nunca é atualizado nem removido.

    `from_custodian_id` é nulo apenas no evento de recebimento inicial.
    O evento é assinado eletronicamente por quem entrega a guarda.
    """

    __tablename__ = "chain_of_custody"
    __table_args__ = (
        Index(
            "ix_custody_sample_time",
            "device_sample_id",
            desc("transferred_at"),
        ),
    )

    device_sample_id: Mapped[UUID] = mapped_column(
        ForeignKey("device_samples.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    from_custodian_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    to_custodian_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    transferred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, index=True
    )
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    location_from: Mapped[str | None] = mapped_column(String(160))
    location_to: Mapped[str] = mapped_column(String(160), nullable=False)
    seal_number: Mapped[str | None] = mapped_column(String(80))
    signature_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("electronic_signatures.id", ondelete="RESTRICT")
    )
    notes: Mapped[str | None] = mapped_column(Text)

    to_custodian = relationship(
        "User", foreign_keys=[to_custodian_id], lazy="selectin"
    )
    from_custodian = relationship(
        "User", foreign_keys=[from_custodian_id], lazy="selectin"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ChainOfCustody sample={self.device_sample_id} at={self.transferred_at}>"
