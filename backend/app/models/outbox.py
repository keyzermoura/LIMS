"""Modelo de Outbox Transacional para Garantia de Entrega At-Least-Once (H3.2).

Conforme ESPECIFICACAO_CAMADA_INTEGRACAO_LIMS.md §4 e ALCOA+.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, PortableJSON, UUIDPrimaryKeyMixin, utcnow


class IntegrationOutbox(UUIDPrimaryKeyMixin, Base):
    """Fila transacional imutável de eventos de negócio persistidos atomicamente."""

    __tablename__ = "integration_outbox"

    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    aggregate_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    aggregate_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(
        PortableJSON, nullable=False, default=dict, server_default="{}"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        server_default=func.now(),
        index=True,
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    attempts: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    next_attempt_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        server_default=func.now(),
        index=True,
    )
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    dead_lettered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<IntegrationOutbox {self.id} [{self.event_type}] agg={self.aggregate_type}:{self.aggregate_id}>"
