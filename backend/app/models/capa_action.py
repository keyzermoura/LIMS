"""CAPA — Ação Corretiva e Preventiva."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    String,
    Text,
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
from app.models.enums import CapaStatus
from app.models.types import capa_status_type


class CapaAction(
    UUIDPrimaryKeyMixin, TimestampMixin, OptimisticLockMixin, JsonMetadataMixin, Base
):
    __tablename__ = "capa_actions"
    __table_args__ = (
        CheckConstraint(
            "device_sample_id IS NOT NULL OR lab_test_id IS NOT NULL",
            name="capa_requires_origin",
        ),
    )

    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    device_sample_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("device_samples.id", ondelete="RESTRICT"), index=True
    )
    lab_test_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("lab_tests.id", ondelete="RESTRICT"), index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    root_cause: Mapped[str] = mapped_column(Text, nullable=False)
    action_plan: Mapped[str] = mapped_column(Text, nullable=False)
    owner_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[CapaStatus] = mapped_column(
        capa_status_type,
        nullable=False,
        default=CapaStatus.ABERTA,
        index=True,
    )
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    auto_opened: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    created_by_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    closed_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT")
    )
    signature_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("electronic_signatures.id", ondelete="RESTRICT")
    )
    effectiveness_check: Mapped[str | None] = mapped_column(Text)

    owner = relationship("User", foreign_keys=[owner_id], lazy="selectin")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<CapaAction {self.code} {self.status.value}>"
