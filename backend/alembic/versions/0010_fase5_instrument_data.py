"""Modelos da Fase 5: Conectores e Aquisição Direta de Instrumentos Analíticos (Sprint 5.3).

Revision ID: 0010_fase5_instrument_data
Revises: 0009_fase5_notifications
Create Date: 2026-11-16
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0010_fase5_instrument_data"
down_revision: str | None = "0009_fase5_notifications"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

INSTRUMENT_FILE_FORMAT = postgresql.ENUM(
    "BALANCA_ASCII",
    "UV_VIS_CSV",
    "CHROMATOGRAPHY_CSV",
    "GENERIC_JSON",
    name="instrument_file_format",
    create_type=False,
)

INSTRUMENT_IMPORT_STATUS = postgresql.ENUM(
    "IMPORTED",
    "MAPPED",
    "REJECTED",
    name="instrument_import_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"

    if is_pg:
        op.execute(
            "DO $$ BEGIN "
            "CREATE TYPE instrument_file_format AS ENUM ("
            "'BALANCA_ASCII', 'UV_VIS_CSV', 'CHROMATOGRAPHY_CSV', 'GENERIC_JSON'); "
            "EXCEPTION WHEN duplicate_object THEN null; "
            "END $$;"
        )
        op.execute(
            "DO $$ BEGIN "
            "CREATE TYPE instrument_import_status AS ENUM ('IMPORTED', 'MAPPED', 'REJECTED'); "
            "EXCEPTION WHEN duplicate_object THEN null; "
            "END $$;"
        )

    json_type = postgresql.JSONB(astext_type=sa.Text()) if is_pg else sa.JSON()
    format_col = INSTRUMENT_FILE_FORMAT if is_pg else sa.String(32)
    status_col = INSTRUMENT_IMPORT_STATUS if is_pg else sa.String(32)

    op.create_table(
        "instrument_data_imports",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("equipment_id", sa.UUID(), nullable=False),
        sa.Column("test_execution_id", sa.UUID(), nullable=True),
        sa.Column("imported_by_id", sa.UUID(), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_format", format_col, nullable=False),
        sa.Column("raw_file_hash_sha256", sa.String(length=64), nullable=False),
        sa.Column("raw_content", sa.Text(), nullable=False),
        sa.Column("parsed_data", json_type, server_default="{}", nullable=False),
        sa.Column("status", status_col, server_default="IMPORTED", nullable=False),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("mapped_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", json_type, server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(
            ["equipment_id"],
            ["laboratory_equipment.id"],
            name=op.f("fk_instrument_data_imports_equipment_id_laboratory_equipment"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["imported_by_id"],
            ["users.id"],
            name=op.f("fk_instrument_data_imports_imported_by_id_users"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["test_execution_id"],
            ["test_executions.id"],
            name=op.f("fk_instrument_data_imports_test_execution_id_test_executions"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_instrument_data_imports")),
    )
    op.create_index(op.f("ix_instrument_data_imports_equipment_id"), "instrument_data_imports", ["equipment_id"], unique=False)
    op.create_index(op.f("ix_instrument_data_imports_file_format"), "instrument_data_imports", ["file_format"], unique=False)
    op.create_index(op.f("ix_instrument_data_imports_imported_by_id"), "instrument_data_imports", ["imported_by_id"], unique=False)
    op.create_index(op.f("ix_instrument_data_imports_raw_file_hash_sha256"), "instrument_data_imports", ["raw_file_hash_sha256"], unique=False)
    op.create_index(op.f("ix_instrument_data_imports_status"), "instrument_data_imports", ["status"], unique=False)
    op.create_index(op.f("ix_instrument_data_imports_test_execution_id"), "instrument_data_imports", ["test_execution_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_instrument_data_imports_test_execution_id"), table_name="instrument_data_imports")
    op.drop_index(op.f("ix_instrument_data_imports_status"), table_name="instrument_data_imports")
    op.drop_index(op.f("ix_instrument_data_imports_raw_file_hash_sha256"), table_name="instrument_data_imports")
    op.drop_index(op.f("ix_instrument_data_imports_imported_by_id"), table_name="instrument_data_imports")
    op.drop_index(op.f("ix_instrument_data_imports_file_format"), table_name="instrument_data_imports")
    op.drop_index(op.f("ix_instrument_data_imports_equipment_id"), table_name="instrument_data_imports")
    op.drop_table("instrument_data_imports")

    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP TYPE IF EXISTS instrument_import_status CASCADE")
        op.execute("DROP TYPE IF EXISTS instrument_file_format CASCADE")
