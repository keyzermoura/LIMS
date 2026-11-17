"""Modelo de Notificações e Alertas em Tempo Real (Fase 5 / Sprint 5.2).

Permite comunicação proativa de desvios metrológicos, calibrações a vencer,
estouro de prazos 5W2H e gargalos de amostras (ISO/IEC 17025 §7.11/§8.7 e 21 CFR Part 11).
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, JsonMetadataMixin, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import NotificationCategory, NotificationSeverity, UserRole
from app.models.types import (
    notification_category_type,
    notification_severity_type,
    user_role_type,
)


class Notification(UUIDPrimaryKeyMixin, TimestampMixin, JsonMetadataMixin, Base):
    """Notificação ou alerta operacional emitido pelo sistema ou por eventos críticos."""

    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user_unread", "user_id", "is_read"),
        Index("ix_notifications_role_unread", "target_role", "is_read"),
    )

    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    target_role: Mapped[UserRole | None] = mapped_column(user_role_type, nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[NotificationSeverity] = mapped_column(
        notification_severity_type,
        nullable=False,
        default=NotificationSeverity.INFO,
        server_default="INFO",
        index=True,
    )
    category: Mapped[NotificationCategory] = mapped_column(
        notification_category_type,
        nullable=False,
        default=NotificationCategory.SYSTEM,
        server_default="SYSTEM",
        index=True,
    )
    link_url: Mapped[str | None] = mapped_column(String(255))
    is_read: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false", index=True
    )
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user = relationship("User", foreign_keys=[user_id], lazy="selectin")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Notification {self.id} {self.severity.value} {self.title}>"
