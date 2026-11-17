"""Horizonte 3: Contas de Serviço M2M e Idempotência (Sprint 8.1 - H3.1).

Revision ID: 0019_fase8_servicos_idempotencia
Revises: 0018_fase7_cep_westgard
Create Date: 2026-11-17
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0019_fase8_servicos_idempotencia"
down_revision: str | None = "0018_fase7_cep_westgard"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"
    uuid_type = postgresql.UUID(as_uuid=True) if is_pg else sa.Uuid()
    json_type = postgresql.JSONB(astext_type=sa.Text()) if is_pg else sa.JSON()

    if is_pg:
        op.execute("""
            DO $$ BEGIN
                ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'SERVICE';
            EXCEPTION WHEN duplicate_object THEN null;
            END $$;
        """)

    # 1. Tabela service_clients
    op.create_table(
        "service_clients",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("client_id", sa.String(64), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("secret_hash", sa.String(128), nullable=False),
        sa.Column("secondary_secret_hash", sa.String(128), nullable=True),
        sa.Column("scopes", json_type, nullable=False, server_default="[]"),
        sa.Column("service_user_id", uuid_type, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_id", uuid_type, nullable=False),
        sa.Column("ip_allowlist", json_type, nullable=True),
        sa.Column("metadata", json_type, nullable=False, server_default="{}"),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["service_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="RESTRICT"),
    )
    op.create_index(op.f("ix_service_clients_client_id"), "service_clients", ["client_id"], unique=True)
    op.create_index(op.f("ix_service_clients_service_user_id"), "service_clients", ["service_user_id"], unique=False)
    op.create_index(op.f("ix_service_clients_is_active"), "service_clients", ["is_active"], unique=False)
    op.create_index(op.f("ix_service_clients_created_by_id"), "service_clients", ["created_by_id"], unique=False)

    # 2. Tabela idempotency_keys
    op.create_table(
        "idempotency_keys",
        sa.Column("client_id", sa.String(64), nullable=False),
        sa.Column("key", sa.String(128), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("response_status", sa.Integer(), nullable=False),
        sa.Column("response_body", json_type, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by_user_id", uuid_type, nullable=True),
        sa.PrimaryKeyConstraint("client_id", "key", name=op.f("pk_idempotency_keys")),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_idempotency_keys_expires_at"), "idempotency_keys", ["expires_at"], unique=False)
    op.create_index(op.f("ix_idempotency_keys_created_by_user_id"), "idempotency_keys", ["created_by_user_id"], unique=False)


def downgrade() -> None:
    op.drop_table("idempotency_keys")
    op.drop_table("service_clients")
