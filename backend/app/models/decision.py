"""Modelos de Decisão de Recebimento e Validação da Coordenação (M0.3 / D06, D10).

Decisão por item/objeto com histórico append-only e segregação de funções.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import (
    Base,
    OptimisticLockMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from app.models.enums import CoordinationReviewStatus, ReceiptDecisionEnum
from app.models.types import coordination_review_status_type, receipt_decision_type

if TYPE_CHECKING:
    from app.models.receipt import CustodyObject, ReceiptItem
    from app.models.user import User


class ReceiptDecision(UUIDPrimaryKeyMixin, TimestampMixin, OptimisticLockMixin, Base):
    """Decisão formalizada pelo conferente sobre item ou objeto de custódia."""

    __tablename__ = "receipt_decisions"

    receipt_item_id: Mapped[UUID] = mapped_column(
        ForeignKey("receipt_items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    custody_object_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("custody_objects.id", ondelete="SET NULL"), index=True
    )
    decision: Mapped[ReceiptDecisionEnum] = mapped_column(
        receipt_decision_type, nullable=False
    )
    justification: Mapped[str] = mapped_column(Text, nullable=False)
    decided_by_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    requires_coordination_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relacionamentos
    receipt_item: Mapped[ReceiptItem] = relationship("ReceiptItem", back_populates="decisions")
    custody_object: Mapped[CustodyObject | None] = relationship("CustodyObject", lazy="selectin")
    decided_by: Mapped[User] = relationship("User", foreign_keys=[decided_by_id], lazy="selectin")
    coordination_review: Mapped[CoordinationReview | None] = relationship(
        "CoordinationReview", back_populates="decision", uselist=False, lazy="selectin"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ReceiptDecision {self.decision.value} (Item {self.receipt_item_id})>"


class CoordinationReview(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Revisão independente da coordenação para exceções, ressalvas e recusas."""

    __tablename__ = "coordination_reviews"

    decision_id: Mapped[UUID] = mapped_column(
        ForeignKey("receipt_decisions.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    status: Mapped[CoordinationReviewStatus] = mapped_column(
        coordination_review_status_type,
        nullable=False,
        default=CoordinationReviewStatus.PENDENTE,
        index=True,
    )
    reviewed_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT")
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    review_notes: Mapped[str | None] = mapped_column(Text)

    # Relacionamentos
    decision: Mapped[ReceiptDecision] = relationship("ReceiptDecision", back_populates="coordination_review")
    reviewed_by: Mapped[User | None] = relationship("User", foreign_keys=[reviewed_by_id], lazy="selectin")
