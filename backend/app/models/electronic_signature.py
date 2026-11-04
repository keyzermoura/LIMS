"""Assinatura eletrônica — manifesto imutável (21 CFR Part 11 §11.50/§11.70).

Cada assinatura registra QUEM assinou (id + nome completo, snapshot),
QUANDO (timestamp UTC), O QUE foi assinado (entity/action/payload hash) e
POR QUÊ (significado + motivo declarado). O token é de uso único.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, utcnow
from app.models.enums import SignatureAction, SignatureMeaning
from app.models.types import signature_action_type, signature_meaning_type


class ElectronicSignature(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "electronic_signatures"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    # Snapshots: se o usuário trocar de nome/cargo, a assinatura histórica
    # continua exibindo exatamente o que foi apresentado no momento.
    username_snapshot: Mapped[str] = mapped_column(String(64), nullable=False)
    full_name_snapshot: Mapped[str] = mapped_column(String(160), nullable=False)
    role_snapshot: Mapped[str] = mapped_column(String(40), nullable=False)

    entity_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    action: Mapped[SignatureAction] = mapped_column(
        signature_action_type,
        nullable=False,
    )
    meaning: Mapped[SignatureMeaning] = mapped_column(
        signature_meaning_type,
        nullable=False,
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    method: Mapped[str] = mapped_column(
        String(32), nullable=False, default="PASSWORD"
    )

    # Hash do "manifesto" (quem/quando/o quê/por quê) e do registro assinado.
    manifest: Mapped[dict[str, Any]] = mapped_column(nullable=False)
    manifest_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    payload_hash: Mapped[str | None] = mapped_column(String(64))
    payload_snapshot: Mapped[dict[str, Any] | None] = mapped_column()

    ip_address: Mapped[str | None] = mapped_column(String(64))
    user_agent: Mapped[str | None] = mapped_column(String(512))
    request_id: Mapped[str | None] = mapped_column(String(64))

    token_jti: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    signed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    consumed_ip: Mapped[str | None] = mapped_column(String(64))
    consumed_user_agent: Mapped[str | None] = mapped_column(String(512))
    consumed_request_id: Mapped[str | None] = mapped_column(String(64))
