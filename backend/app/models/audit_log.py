"""Trilha de auditoria append-only com encadeamento de hashes.

Cada registro contém `payload` (o conteúdo exato hasheado), `prev_hash`
e `hash`:

    hash_n = SHA-256( seq_n || ":" || prev_hash || ":" || canonical_json(payload) )

Além do hash, gravamos um HMAC-SHA256 com chave mantida fora do banco
(KMS/secret manager). Um administrador do banco consegue recalcular a
cadeia, mas não o HMAC — detectando adulteração mesmo com acesso DDL.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.enums import AuditAction
from app.models.types import audit_action_type


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_entity", "entity_type", "entity_id"),
        Index("ix_audit_actor_time", "actor_id", "occurred_at"),
        Index("ix_audit_occurred_at", "occurred_at"),
    )

    # INTEGER no SQLite (testes) garante autoincremento de rowid; no
    # PostgreSQL permanece BIGINT/BIGSERIAL.
    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    sequence: Mapped[int] = mapped_column(
        BigInteger, nullable=False, unique=True, index=True
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    actor_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    actor_username: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_role: Mapped[str | None] = mapped_column(String(40))

    action: Mapped[AuditAction] = mapped_column(
        audit_action_type,
        nullable=False,
        index=True,
    )
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    old_value: Mapped[dict[str, Any] | None] = mapped_column()
    new_value: Mapped[dict[str, Any] | None] = mapped_column()
    reason: Mapped[str | None] = mapped_column(Text)
    # Snapshot canônico completo hasheado — permite reverificação exata.
    payload: Mapped[dict[str, Any]] = mapped_column(nullable=False)

    ip_address: Mapped[str | None] = mapped_column(String(64))
    user_agent: Mapped[str | None] = mapped_column(String(512))
    request_id: Mapped[str | None] = mapped_column(String(64))
    signature_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("electronic_signatures.id", ondelete="RESTRICT")
    )

    prev_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    hmac: Mapped[str] = mapped_column(String(64), nullable=False)


__all__ = ["AuditLog"]
