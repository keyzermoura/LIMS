"""Modelo de Chaves de Idempotência para APIs de Integração.

Conforme ESPECIFICACAO_CAMADA_INTEGRACAO_LIMS.md §3 e RFC 7231 §4.2.2.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, PortableJSON, utcnow


class IdempotencyKey(Base):
    """Registro de idempotência para chamadas de integração e uploads de instrumentos."""

    __tablename__ = "idempotency_keys"

    client_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    response_status: Mapped[int] = mapped_column(Integer, nullable=False)
    response_body: Mapped[dict[str, Any] | list[Any]] = mapped_column(
        PortableJSON, nullable=False, default=dict, server_default="{}"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    created_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<IdempotencyKey {self.client_id}:{self.key} status={self.response_status}>"
