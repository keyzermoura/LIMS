"""Usuários e sessões de refresh rotativas."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    utcnow,
)
from app.models.enums import UserRole
from app.models.types import user_role_type


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(160), nullable=False)
    registration_number: Mapped[str | None] = mapped_column(String(64))  # conselho/CRM/CRF
    role: Mapped[UserRole] = mapped_column(
        user_role_type,
        nullable=False,
        default=UserRole.TECNICO,
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    failed_login_attempts: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    password_changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    # Contador monotônico embutido nos JWTs (`pwdv`). Incrementar invalida
    # imediatamente todos os access tokens já emitidos para o usuário.
    token_version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    mfa_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    @property
    def password_version(self) -> int:
        """Versão usada nos claims do JWT para invalidar sessões antigas.

        Um contador inteiro evita colisões de timestamp quando a senha é
        trocada (ou uma sessão é revogada) duas vezes no mesmo segundo.
        """
        return self.token_version

    @property
    def is_locked(self) -> bool:
        locked_until = self.locked_until
        if locked_until is None:
            return False
        if locked_until.tzinfo is None:

            locked_until = locked_until.replace(tzinfo=UTC)
        return locked_until > utcnow()

    def __repr__(self) -> str:  # pragma: no cover - debug
        return f"<User {self.username} ({self.role.value})>"


class RefreshToken(UUIDPrimaryKeyMixin, Base):
    """Refresh tokens são de uso único e rotacionados a cada refresh."""

    __tablename__ = "refresh_tokens"

    jti: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_reason: Mapped[str | None] = mapped_column(String(120))
    replaced_by_jti: Mapped[str | None] = mapped_column(String(64))
    ip_address: Mapped[str | None] = mapped_column(String(64))
    user_agent: Mapped[str | None] = mapped_column(String(512))

    @property
    def is_active(self) -> bool:
        return self.revoked_at is None and self.expires_at > utcnow()
