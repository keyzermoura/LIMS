"""Horizonte 3: Outbox Transacional e Webhooks (Sprint 8.2 - H3.2).

Revision ID: 0020_fase8_outbox_webhooks
Revises: 0019_fase8_servicos_idempotencia
Create Date: 2026-11-17
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0020_fase8_outbox_webhooks"
down_revision: str | None = "0019_fase8_servicos_idempotencia"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"
    uuid_type = postgresql.UUID(as_uuid=True) if is_pg else sa.Uuid()
    json_type = postgresql.JSONB(astext_type=sa.Text()) if is_pg else sa.JSON()

    # 1. Tabela integration_outbox
    op.create_table(
        "integration_outbox",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("aggregate_type", sa.String(64), nullable=False),
        sa.Column("aggregate_id", sa.String(64), nullable=False),
        sa.Column("payload", json_type, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("dead_lettered_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(op.f("ix_integration_outbox_event_type"), "integration_outbox", ["event_type"], unique=False)
    op.create_index(op.f("ix_integration_outbox_aggregate_type"), "integration_outbox", ["aggregate_type"], unique=False)
    op.create_index(op.f("ix_integration_outbox_aggregate_id"), "integration_outbox", ["aggregate_id"], unique=False)
    op.create_index(op.f("ix_integration_outbox_created_at"), "integration_outbox", ["created_at"], unique=False)
    op.create_index(op.f("ix_integration_outbox_published_at"), "integration_outbox", ["published_at"], unique=False)
    op.create_index(op.f("ix_integration_outbox_next_attempt_at"), "integration_outbox", ["next_attempt_at"], unique=False)
    op.create_index(op.f("ix_integration_outbox_dead_lettered_at"), "integration_outbox", ["dead_lettered_at"], unique=False)


def downgrade() -> None:
    op.drop_table("integration_outbox")
