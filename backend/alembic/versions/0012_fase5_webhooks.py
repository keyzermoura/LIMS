"""Modelos da Fase 5: Webhooks e Mensageria Segura de Integração (Sprint 5.4).

Revision ID: 0012_fase5_webhooks
Revises: 0011_fase5_guards_integridade
Create Date: 2026-11-16
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0012_fase5_webhooks"
down_revision: str | None = "0011_fase5_guards_integridade"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"
    uuid_type = postgresql.UUID(as_uuid=True) if is_pg else sa.Uuid()
    json_type = postgresql.JSONB(astext_type=sa.Text()) if is_pg else sa.JSON()

    # 1. Tabela webhook_subscriptions
    op.create_table(
        "webhook_subscriptions",
        sa.Column("id", uuid_type, primary_key=True, nullable=False),
        sa.Column("url", sa.String(500), nullable=False),
        sa.Column("secret", sa.String(255), nullable=False),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("events", json_type, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_by_id", uuid_type, nullable=False),
        sa.Column("metadata", json_type, server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(
            ["created_by_id"],
            ["users.id"],
            name="fk_webhook_subscriptions_created_by_id_users",
            ondelete="RESTRICT",
        ),
    )
    op.create_index(
        "ix_webhook_subscriptions_created_by_id",
        "webhook_subscriptions",
        ["created_by_id"],
        unique=False,
    )

    # 2. Tabela webhook_deliveries
    op.create_table(
        "webhook_deliveries",
        sa.Column("id", uuid_type, primary_key=True, nullable=False),
        sa.Column("subscription_id", uuid_type, nullable=False),
        sa.Column("event", sa.String(64), nullable=False),
        sa.Column("payload", json_type, nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("response_body", sa.Text(), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(
            ["subscription_id"],
            ["webhook_subscriptions.id"],
            name="fk_webhook_deliveries_subscription_id_webhook_subscriptions",
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "ix_webhook_deliveries_subscription_id",
        "webhook_deliveries",
        ["subscription_id"],
        unique=False,
    )
    op.create_index(
        "ix_webhook_deliveries_event",
        "webhook_deliveries",
        ["event"],
        unique=False,
    )
    op.create_index(
        "ix_webhook_deliveries_status",
        "webhook_deliveries",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_webhook_deliveries_status", table_name="webhook_deliveries")
    op.drop_index("ix_webhook_deliveries_event", table_name="webhook_deliveries")
    op.drop_index("ix_webhook_deliveries_subscription_id", table_name="webhook_deliveries")
    op.drop_table("webhook_deliveries")

    op.drop_index("ix_webhook_subscriptions_created_by_id", table_name="webhook_subscriptions")
    op.drop_table("webhook_subscriptions")
