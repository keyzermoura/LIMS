"""Modelos de Assinatura e Entrega de Webhooks para Integrações Corporativas (Fase 5 / Sprint 5.4).

Conforme ESPECIFICACAO_CAMADA_INTEGRACAO_LIMS.md e ALCOA+.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import (
    Base,
    JsonMetadataMixin,
    PortableJSON,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)

if TYPE_CHECKING:
    from app.models.user import User


class WebhookSubscription(UUIDPrimaryKeyMixin, TimestampMixin, JsonMetadataMixin, Base):
    """Ponto de integração de saída (Webhook Endpoint) configurado para envio de eventos."""

    __tablename__ = "webhook_subscriptions"

    url: Mapped[str] = mapped_column(String(500), nullable=False)
    secret: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    events: Mapped[list[str]] = mapped_column(
        PortableJSON, nullable=False, default=list, server_default="[]"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", nullable=False
    )
    created_by_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    created_by: Mapped[User] = relationship("User", lazy="selectin")
    deliveries: Mapped[list[WebhookDelivery]] = relationship(
        "WebhookDelivery",
        back_populates="subscription",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class WebhookDelivery(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Histórico e registro transacional de tentativas de entrega de webhooks (Outbox Delivery)."""

    __tablename__ = "webhook_deliveries"

    subscription_id: Mapped[UUID] = mapped_column(
        ForeignKey("webhook_subscriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(PortableJSON, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="PENDING",
        server_default="PENDING",
        index=True,
    )  # PENDING, DELIVERED, FAILED
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempt_count: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    subscription: Mapped[WebhookSubscription] = relationship(
        "WebhookSubscription", back_populates="deliveries"
    )
