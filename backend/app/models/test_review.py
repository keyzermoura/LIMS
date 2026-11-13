"""Modelos de Revisão Técnica por Pares de Ensaios Laboratoriais (Fase 3 / M3.1).

Implementa a segregação de funções requerida pela ISO/IEC 17025 e 21 CFR Part 11:
Todo ensaio concluído pelo analista é submetido à revisão colegiada independente
antes de ser liberado para homologação e emissão do laudo pericial final.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import (
    Base,
    JsonMetadataMixin,
    OptimisticLockMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    utcnow,
)
from app.models.enums import CoordinationReviewStatus
from app.models.types import coordination_review_status_type

if TYPE_CHECKING:
    from app.models.electronic_signature import ElectronicSignature
    from app.models.lab_test import LabTest
    from app.models.user import User


class TestReview(
    UUIDPrimaryKeyMixin, TimestampMixin, OptimisticLockMixin, JsonMetadataMixin, Base
):
    """Parecer e revisão técnica independente da coordenação sobre ensaio analítico."""

    __tablename__ = "test_reviews"
    __table_args__ = (
        UniqueConstraint("lab_test_id", "review_number", name="uq_test_review_number"),
        Index("ix_test_reviews_test_status", "lab_test_id", "status"),
    )

    lab_test_id: Mapped[UUID] = mapped_column(
        ForeignKey("lab_tests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    review_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[CoordinationReviewStatus] = mapped_column(
        coordination_review_status_type,
        nullable=False,
        index=True,
    )
    reviewed_by_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    notes: Mapped[str | None] = mapped_column(Text)
    justification: Mapped[str | None] = mapped_column(
        Text,
        comment="Justificativa técnica mandatória em caso de devolução ou reprovação (ALCOA+)",
    )
    signature_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("electronic_signatures.id", ondelete="RESTRICT"), nullable=True
    )

    # Relacionamentos
    lab_test: Mapped[LabTest] = relationship("LabTest", back_populates="reviews")
    reviewed_by: Mapped[User] = relationship(
        "User", foreign_keys=[reviewed_by_id], lazy="selectin"
    )
    signature: Mapped[ElectronicSignature | None] = relationship(
        "ElectronicSignature", foreign_keys=[signature_id], lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<TestReview #{self.review_number} on {self.lab_test_id}: {self.status.value}>"
