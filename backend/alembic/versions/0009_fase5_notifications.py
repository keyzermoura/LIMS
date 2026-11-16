"""Modelos da Fase 5: Notificações e Alertas em Tempo Real (Sprint 5.2).

Revision ID: 0009_fase5_notifications
Revises: 0008_fase4_capa
Create Date: 2026-11-16
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0009_fase5_notifications"
down_revision: str | None = "0008_fase4_capa"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

USER_ROLE = postgresql.ENUM(
    "ADMIN",
    "FISCAL",
    "TECNICO",
    "CUSTODIANTE",
    "AUDITOR",
    name="user_role",
    create_type=False,
)

NOTIFICATION_SEVERITY = postgresql.ENUM(
    "INFO",
    "WARNING",
    "CRITICAL",
    name="notification_severity",
    create_type=False,
)

NOTIFICATION_CATEGORY = postgresql.ENUM(
    "CALIBRATION",
    "COMPETENCE",
    "CAPA",
    "TAT",
    "SAMPLE_ISSUE",
    "SYSTEM",
    name="notification_category",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"

    if is_pg:
        op.execute(
            "DO $$ BEGIN "
            "CREATE TYPE notification_severity AS ENUM ('INFO', 'WARNING', 'CRITICAL'); "
            "EXCEPTION WHEN duplicate_object THEN null; "
            "END $$;"
        )
        op.execute(
            "DO $$ BEGIN "
            "CREATE TYPE notification_category AS ENUM ("
            "'CALIBRATION', 'COMPETENCE', 'CAPA', 'TAT', 'SAMPLE_ISSUE', 'SYSTEM'); "
            "EXCEPTION WHEN duplicate_object THEN null; "
            "END $$;"
        )

    json_type = postgresql.JSONB(astext_type=sa.Text()) if is_pg else sa.JSON()
    role_col = USER_ROLE if is_pg else sa.String(32)
    severity_col = NOTIFICATION_SEVERITY if is_pg else sa.String(32)
    category_col = NOTIFICATION_CATEGORY if is_pg else sa.String(32)

    op.create_table(
        "notifications",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("target_role", role_col, nullable=True),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("severity", severity_col, nullable=False, server_default="INFO"),
        sa.Column("category", category_col, nullable=False, server_default="SYSTEM"),
        sa.Column("link_url", sa.String(length=255), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", json_type, server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_notifications_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_notifications")),
    )
    op.create_index(op.f("ix_notifications_user_id"), "notifications", ["user_id"], unique=False)
    op.create_index(op.f("ix_notifications_target_role"), "notifications", ["target_role"], unique=False)
    op.create_index(op.f("ix_notifications_severity"), "notifications", ["severity"], unique=False)
    op.create_index(op.f("ix_notifications_category"), "notifications", ["category"], unique=False)
    op.create_index(op.f("ix_notifications_is_read"), "notifications", ["is_read"], unique=False)
    op.create_index("ix_notifications_user_unread", "notifications", ["user_id", "is_read"], unique=False)
    op.create_index("ix_notifications_role_unread", "notifications", ["target_role", "is_read"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_notifications_role_unread", table_name="notifications")
    op.drop_index("ix_notifications_user_unread", table_name="notifications")
    op.drop_index(op.f("ix_notifications_is_read"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_category"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_severity"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_target_role"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_user_id"), table_name="notifications")
    op.drop_table("notifications")

    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP TYPE IF EXISTS notification_category CASCADE")
        op.execute("DROP TYPE IF EXISTS notification_severity CASCADE")
