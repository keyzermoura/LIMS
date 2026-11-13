"""Ensaios de bancada e versões assinadas de resultados.

`LabTest` mantém o estado corrente (consulta rápida). Cada gravação
definitiva gera um `LabTestResult` imutável — o histórico nunca é
sobrescrito, o que preserva o dado bruto original (ALCOA+).
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import (
    Base,
    JsonMetadataMixin,
    OptimisticLockMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    utcnow,
)
from app.models.enums import CoordinationReviewStatus, TestOutcome, TestStatus
from app.models.types import (
    coordination_review_status_type,
    test_outcome_type,
    test_status_type,
)

if TYPE_CHECKING:
    from app.models.device_sample import DeviceSample
    from app.models.equipment import LaboratoryEquipment
    from app.models.test_attachment import TestAttachment
    from app.models.test_execution import TestExecution
    from app.models.test_method import TestMethod
    from app.models.test_review import TestReview
    from app.models.user import User


class LabTest(
    UUIDPrimaryKeyMixin, TimestampMixin, OptimisticLockMixin, JsonMetadataMixin, Base
):
    __tablename__ = "lab_tests"
    __table_args__ = (
        Index("ix_tests_sample_status", "device_sample_id", "status"),
    )

    device_sample_id: Mapped[UUID] = mapped_column(
        ForeignKey("device_samples.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    method: Mapped[str | None] = mapped_column(String(200))
    method_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("test_methods.id", ondelete="SET NULL"), index=True
    )
    equipment_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("laboratory_equipment.id", ondelete="SET NULL"), index=True
    )
    parameters: Mapped[dict[str, Any]] = mapped_column(
        nullable=False, default=dict, server_default="{}"
    )
    unit: Mapped[str] = mapped_column(String(32), nullable=False)
    lower_limit: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    upper_limit: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    acceptance_criteria: Mapped[str | None] = mapped_column(Text)

    result_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    result_text: Mapped[str | None] = mapped_column(String(500))
    outcome: Mapped[TestOutcome | None] = mapped_column(
        test_outcome_type, index=True
    )
    notes: Mapped[str | None] = mapped_column(Text)

    status: Mapped[TestStatus] = mapped_column(
        test_status_type,
        nullable=False,
        default=TestStatus.PENDENTE,
        index=True,
    )
    review_status: Mapped[CoordinationReviewStatus] = mapped_column(
        coordination_review_status_type,
        nullable=False,
        default=CoordinationReviewStatus.PENDENTE,
        index=True,
    )
    assigned_to_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT")
    )
    tested_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT")
    )
    tested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    signed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    signed_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT")
    )
    signature_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("electronic_signatures.id", ondelete="RESTRICT")
    )
    result_version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    sample: Mapped[DeviceSample] = relationship(
        "DeviceSample", foreign_keys=[device_sample_id], lazy="selectin"
    )
    tested_by: Mapped[User | None] = relationship(
        "User", foreign_keys=[tested_by_id], lazy="selectin"
    )
    signed_by: Mapped[User | None] = relationship(
        "User", foreign_keys=[signed_by_id], lazy="selectin"
    )
    test_method: Mapped[TestMethod | None] = relationship(
        "TestMethod", back_populates="lab_tests", lazy="selectin"
    )
    equipment: Mapped[LaboratoryEquipment | None] = relationship(
        "LaboratoryEquipment", lazy="selectin"
    )
    executions: Mapped[list[TestExecution]] = relationship(
        "TestExecution",
        back_populates="lab_test",
        cascade="all, delete-orphan",
        order_by="TestExecution.execution_number",
        lazy="selectin",
    )
    reviews: Mapped[list[TestReview]] = relationship(
        "TestReview",
        back_populates="lab_test",
        cascade="all, delete-orphan",
        order_by="TestReview.review_number",
        lazy="selectin",
    )
    attachments: Mapped[list[TestAttachment]] = relationship(
        "TestAttachment",
        back_populates="lab_test",
        cascade="all, delete-orphan",
        order_by="TestAttachment.created_at",
        lazy="selectin",
    )
    @property
    def is_signed(self) -> bool:
        return self.signed_at is not None

    def __repr__(self) -> str:  # pragma: no cover
        return f"<LabTest {self.name} {self.status.value}>"


class LabTestResult(UUIDPrimaryKeyMixin, Base):
    """Versão imutável de um resultado assinado.

    Bloqueada por trigger no PostgreSQL para UPDATE/DELETE.
    """

    __tablename__ = "lab_test_results"
    __table_args__ = (
        UniqueConstraint("lab_test_id", "version", name="uq_lab_test_result_version"),
    )

    lab_test_id: Mapped[UUID] = mapped_column(
        ForeignKey("lab_tests.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    result_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    result_text: Mapped[str | None] = mapped_column(String(500))
    unit: Mapped[str] = mapped_column(String(32), nullable=False)
    outcome: Mapped[TestOutcome] = mapped_column(
        test_outcome_type, nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text)
    is_amendment: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    amendment_reason: Mapped[str | None] = mapped_column(Text)
    signed_by_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    signed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    signature_id: Mapped[UUID] = mapped_column(
        ForeignKey("electronic_signatures.id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )

    signed_by = relationship("User", lazy="selectin")
