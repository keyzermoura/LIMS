"""Modelos de Competência Técnica, Qualificação de Analistas e Treinamento (Fase 4 / M4.1).

Implementa os requisitos da ISO/IEC 17025:2017 (§6.2 - Pessoal):
O laboratório deve garantir a competência de todo o pessoal que realiza atividades
laboratoriais, autorizar formalmente cada analista por método de ensaio específico
e manter registros atualizados de treinamentos, supervisões e avaliações de eficácia.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import (
    Base,
    JsonMetadataMixin,
    OptimisticLockMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    utcnow,
)
from app.models.enums import QualificationStatus
from app.models.types import qualification_status_type

if TYPE_CHECKING:
    from app.models.electronic_signature import ElectronicSignature
    from app.models.test_method import TestMethod
    from app.models.user import User


class AnalystQualification(
    UUIDPrimaryKeyMixin, TimestampMixin, OptimisticLockMixin, JsonMetadataMixin, Base
):
    """Habilitação formal de um analista para execução de determinado método analítico."""

    __tablename__ = "analyst_qualifications"
    __table_args__ = (
        UniqueConstraint("user_id", "method_id", name="uq_analyst_qualifications_user_method"),
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    method_id: Mapped[UUID] = mapped_column(
        ForeignKey("test_methods.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[QualificationStatus] = mapped_column(
        qualification_status_type,
        nullable=False,
        default=QualificationStatus.QUALIFICADO,
        index=True,
    )
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), index=True
    )
    authorized_by_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    signature_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("electronic_signatures.id", ondelete="RESTRICT")
    )
    scope: Mapped[str | None] = mapped_column(String(200))
    notes: Mapped[str | None] = mapped_column(Text)

    # Relacionamentos
    user: Mapped[User] = relationship(
        "User", foreign_keys=[user_id], lazy="selectin"
    )
    method: Mapped[TestMethod] = relationship(
        "TestMethod", foreign_keys=[method_id], lazy="selectin"
    )
    authorized_by: Mapped[User] = relationship(
        "User", foreign_keys=[authorized_by_id], lazy="selectin"
    )
    signature: Mapped[ElectronicSignature | None] = relationship(
        "ElectronicSignature", foreign_keys=[signature_id], lazy="selectin"
    )
    trainings: Mapped[list[TrainingRecord]] = relationship(
        "TrainingRecord", back_populates="qualification", cascade="all, delete-orphan", lazy="selectin"
    )

    @property
    def is_active(self) -> bool:
        if self.status != QualificationStatus.QUALIFICADO:
            return False
        return not (self.expires_at and self.expires_at < utcnow())

    def __repr__(self) -> str:
        return f"<AnalystQualification user={self.user_id} method={self.method_id} status={self.status.value}>"


class TrainingRecord(
    UUIDPrimaryKeyMixin, TimestampMixin, OptimisticLockMixin, JsonMetadataMixin, Base
):
    """Registro de treinamento técnico, horas práticas de bancada e comprovações de competência."""

    __tablename__ = "training_records"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    qualification_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("analyst_qualifications.id", ondelete="SET NULL"), index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    provider: Mapped[str | None] = mapped_column(String(200))
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    hours: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False, default=Decimal("0.00"))
    certificate_code: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(Text)

    # Relacionamentos
    user: Mapped[User] = relationship(
        "User", foreign_keys=[user_id], lazy="selectin"
    )
    qualification: Mapped[AnalystQualification | None] = relationship(
        "AnalystQualification", back_populates="trainings", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<TrainingRecord user={self.user_id} title='{self.title}'>"
