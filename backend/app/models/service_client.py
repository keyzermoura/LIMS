"""Modelo de Conta de Serviço (Machine-to-Machine / OAuth2 Client Credentials).

Conforme ESPECIFICACAO_CAMADA_INTEGRACAO_LIMS.md e ALCOA+.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import (
    Base,
    JsonMetadataMixin,
    OptimisticLockMixin,
    PortableJSON,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)

if TYPE_CHECKING:
    from app.models.user import User


class ServiceClient(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    OptimisticLockMixin,
    JsonMetadataMixin,
    Base,
):
    """Cliente de integração Máquina-a-Máquina (M2M) autenticado via Client Credentials."""

    __tablename__ = "service_clients"

    client_id: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    secret_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    secondary_secret_hash: Mapped[str | None] = mapped_column(
        String(128), nullable=True
    )
    scopes: Mapped[list[str]] = mapped_column(
        PortableJSON, nullable=False, default=list, server_default="[]"
    )
    service_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true", index=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_by_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    ip_allowlist: Mapped[list[str] | None] = mapped_column(
        PortableJSON, nullable=True
    )

    # Relacionamentos
    service_user: Mapped[User] = relationship(
        "User", foreign_keys=[service_user_id], lazy="selectin"
    )
    created_by: Mapped[User] = relationship(
        "User", foreign_keys=[created_by_id], lazy="selectin"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ServiceClient {self.client_id} [{self.name}] active={self.is_active}>"
