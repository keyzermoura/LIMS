"""Horizonte 1: Versionamento e Emendas Regulamentares de Laudos Oficiais (ISO/IEC 17025 §7.8.8).

Revision ID: 0013_fase6_laudos_emendas
Revises: 0012_fase5_webhooks
Create Date: 2026-11-16
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0013_fase6_laudos_emendas"
down_revision: str | None = "0012_fase5_webhooks"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"
    uuid_type = postgresql.UUID(as_uuid=True) if is_pg else sa.Uuid()

    # 1. Adicionar colunas de versionamento e emenda em official_reports
    op.add_column(
        "official_reports",
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "official_reports",
        sa.Column("root_report_id", uuid_type, nullable=True),
    )
    op.add_column(
        "official_reports",
        sa.Column("supersedes_id", uuid_type, nullable=True),
    )
    op.add_column(
        "official_reports",
        sa.Column("is_latest", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.add_column(
        "official_reports",
        sa.Column("amendment_reason", sa.Text(), nullable=True),
    )

    # 2. Criar Foreign Keys e Índices
    op.create_foreign_key(
        "fk_official_reports_root_report_id_official_reports",
        "official_reports",
        "official_reports",
        ["root_report_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_official_reports_supersedes_id_official_reports",
        "official_reports",
        "official_reports",
        ["supersedes_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        "ix_official_reports_root_report_id",
        "official_reports",
        ["root_report_id"],
        unique=False,
    )
    op.create_index(
        "ix_official_reports_supersedes_id",
        "official_reports",
        ["supersedes_id"],
        unique=False,
    )
    op.create_index(
        "ix_official_reports_is_latest",
        "official_reports",
        ["is_latest"],
        unique=False,
    )

    # 3. Atualizar trigger no PostgreSQL para proteger campos de versionamento
    if is_pg:
        op.execute("""
CREATE OR REPLACE FUNCTION lims_official_reports_guard() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'Laudos oficiais nao podem ser excluidos (21 CFR Part 11)'
            USING ERRCODE = 'insufficient_privilege';
    END IF;

    IF OLD.pdf_data IS NOT NULL AND NEW.pdf_data IS DISTINCT FROM OLD.pdf_data THEN
        RAISE EXCEPTION 'PDF do laudo e write-once'
            USING ERRCODE = 'insufficient_privilege';
    END IF;

    IF OLD.report_number IS DISTINCT FROM NEW.report_number
       OR OLD.solicitation_id IS DISTINCT FROM NEW.solicitation_id
       OR OLD.device_sample_id IS DISTINCT FROM NEW.device_sample_id
       OR OLD.title IS DISTINCT FROM NEW.title
       OR OLD.conclusion IS DISTINCT FROM NEW.conclusion
       OR OLD.summary IS DISTINCT FROM NEW.summary
       OR OLD.sha256_hash IS DISTINCT FROM NEW.sha256_hash
       OR OLD.issued_by_id IS DISTINCT FROM NEW.issued_by_id
       OR OLD.issued_at IS DISTINCT FROM NEW.issued_at
       OR OLD.signature_id IS DISTINCT FROM NEW.signature_id
       OR OLD.auth_token IS DISTINCT FROM NEW.auth_token
       OR OLD.version IS DISTINCT FROM NEW.version
       OR OLD.root_report_id IS DISTINCT FROM NEW.root_report_id
       OR OLD.supersedes_id IS DISTINCT FROM NEW.supersedes_id
       OR OLD.amendment_reason IS DISTINCT FROM NEW.amendment_reason THEN
        RAISE EXCEPTION 'Campos de laudo oficial sao imutaveis (21 CFR Part 11)'
            USING ERRCODE = 'insufficient_privilege';
    END IF;

    IF OLD.is_latest = false AND NEW.is_latest = true THEN
        RAISE EXCEPTION 'Laudo superado nao pode ser reativado como vigente'
            USING ERRCODE = 'insufficient_privilege';
    END IF;

    RETURN NEW;
END;
$$;
""")


def downgrade() -> None:
    op.drop_index("ix_official_reports_is_latest", table_name="official_reports")
    op.drop_index("ix_official_reports_supersedes_id", table_name="official_reports")
    op.drop_index("ix_official_reports_root_report_id", table_name="official_reports")
    op.drop_constraint(
        "fk_official_reports_supersedes_id_official_reports",
        table_name="official_reports",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_official_reports_root_report_id_official_reports",
        table_name="official_reports",
        type_="foreignkey",
    )
    op.drop_column("official_reports", "amendment_reason")
    op.drop_column("official_reports", "is_latest")
    op.drop_column("official_reports", "supersedes_id")
    op.drop_column("official_reports", "root_report_id")
    op.drop_column("official_reports", "version")
