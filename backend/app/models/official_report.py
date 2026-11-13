"""Modelos de Laudos Oficiais e Relatórios de Ensaio Consolidados (Fase 3 / M3.2).

Registra o documento pericial definitivo emitido pela SEFI, indexado com Hash SHA-256
e token de autenticidade (QR Code) para verificação pública da integridade (21 CFR Part 11).
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, LargeBinary, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import (
    Base,
    JsonMetadataMixin,
    OptimisticLockMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    utcnow,
)
from app.models.enums import TestOutcome
from app.models.types import test_outcome_type

if TYPE_CHECKING:
    from app.models.device_sample import DeviceSample
    from app.models.electronic_signature import ElectronicSignature
    from app.models.solicitation import Solicitation
    from app.models.user import User


class OfficialReport(
    UUIDPrimaryKeyMixin, TimestampMixin, OptimisticLockMixin, JsonMetadataMixin, Base
):
    """Documento pericial oficial emitido pelo laboratório após homologação colegiada."""

    __tablename__ = "official_reports"

    report_number: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    solicitation_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("solicitations.id", ondelete="SET NULL"), index=True
    )
    device_sample_id: Mapped[UUID] = mapped_column(
        ForeignKey("device_samples.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    conclusion: Mapped[TestOutcome] = mapped_column(
        test_outcome_type, nullable=False, index=True
    )
    summary: Mapped[str | None] = mapped_column(Text)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    pdf_data: Mapped[bytes | None] = mapped_column(LargeBinary)

    issued_by_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    signature_id: Mapped[UUID] = mapped_column(
        ForeignKey("electronic_signatures.id", ondelete="RESTRICT"), nullable=False
    )
    auth_token: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )

    # Relacionamentos
    solicitation: Mapped[Solicitation | None] = relationship("Solicitation", lazy="selectin")
    device_sample: Mapped[DeviceSample] = relationship("DeviceSample", lazy="selectin")
    issued_by: Mapped[User] = relationship(
        "User", foreign_keys=[issued_by_id], lazy="selectin"
    )
    signature: Mapped[ElectronicSignature] = relationship(
        "ElectronicSignature", foreign_keys=[signature_id], lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<OfficialReport {self.report_number}: {self.conclusion.value} ({self.sha256_hash[:8]})>"
