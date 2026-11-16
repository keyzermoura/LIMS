"""Item de Ação CAPA (Contenção Imediata, Ação Corretiva ou Ação Preventiva - ISO 17025 §8.7)."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Date, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import CapaActionType, CapaItemStatus
from app.models.types import capa_action_type, capa_item_status


class CapaActionItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "capa_action_items"

    capa_id: Mapped[UUID] = mapped_column(
        ForeignKey("capa_actions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    action_type: Mapped[CapaActionType] = mapped_column(
        capa_action_type, nullable=False, index=True
    )
    assigned_to_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[CapaItemStatus] = mapped_column(
        capa_item_status,
        nullable=False,
        default=CapaItemStatus.PENDENTE,
        server_default="PENDENTE",
        index=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completion_evidence: Mapped[str | None] = mapped_column(Text)

    capa = relationship("CapaAction", back_populates="action_items")
    assigned_to = relationship("User", foreign_keys=[assigned_to_id], lazy="selectin")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<CapaActionItem {self.id} {self.action_type.value} {self.status.value}>"
