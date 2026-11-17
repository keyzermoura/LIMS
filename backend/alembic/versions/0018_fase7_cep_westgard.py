"""Horizonte 2: Controle Estatístico de Processo (CEP / Westgard) (H2.5).

Revision ID: 0018_fase7_cep_westgard
Revises: 0017_fase7_armazena_descarte
Create Date: 2026-11-17
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0018_fase7_cep_westgard"
down_revision: str | None = "0017_fase7_armazena_descarte"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

QC_STATUS = postgresql.ENUM(
    "CONFORMING",
    "WARNING",
    "REJECTED",
    name="qc_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"
    uuid_type = postgresql.UUID(as_uuid=True) if is_pg else sa.Uuid()
    json_type = postgresql.JSONB(astext_type=sa.Text()) if is_pg else sa.JSON()

    if is_pg:
        op.execute("""
            DO $$ BEGIN
                CREATE TYPE qc_status AS ENUM (
                    'CONFORMING', 'WARNING', 'REJECTED'
                );
            EXCEPTION WHEN duplicate_object THEN null;
            END $$;
        """)

    op.create_table(
        "qc_runs",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("method_id", uuid_type, nullable=False),
        sa.Column("equipment_id", uuid_type, nullable=True),
        sa.Column("reagent_batch_id", uuid_type, nullable=True),
        sa.Column("operator_id", uuid_type, nullable=False),
        sa.Column("run_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("target_mean", sa.Float(), nullable=False),
        sa.Column("target_sd", sa.Float(), nullable=False),
        sa.Column("measured_value", sa.Float(), nullable=False),
        sa.Column("z_score", sa.Float(), nullable=False),
        sa.Column("status", QC_STATUS if is_pg else sa.String(32), nullable=False, server_default="CONFORMING"),
        sa.Column("violation_rules", json_type, nullable=False, server_default="[]"),
        sa.Column("is_active_violation", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("corrective_notes", sa.Text(), nullable=True),
        sa.Column("metadata", json_type, nullable=False, server_default="{}"),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["method_id"], ["test_methods.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["equipment_id"], ["laboratory_equipment.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["reagent_batch_id"], ["reagent_batches.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["operator_id"], ["users.id"], ondelete="RESTRICT"),
    )
    op.create_index(op.f("ix_qc_runs_code"), "qc_runs", ["code"], unique=True)
    op.create_index(op.f("ix_qc_runs_method_id"), "qc_runs", ["method_id"], unique=False)
    op.create_index(op.f("ix_qc_runs_equipment_id"), "qc_runs", ["equipment_id"], unique=False)
    op.create_index(op.f("ix_qc_runs_reagent_batch_id"), "qc_runs", ["reagent_batch_id"], unique=False)
    op.create_index(op.f("ix_qc_runs_operator_id"), "qc_runs", ["operator_id"], unique=False)
    op.create_index(op.f("ix_qc_runs_status"), "qc_runs", ["status"], unique=False)
    op.create_index(op.f("ix_qc_runs_is_active_violation"), "qc_runs", ["is_active_violation"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"

    op.drop_table("qc_runs")
    if is_pg:
        op.execute("DROP TYPE IF EXISTS qc_status CASCADE;")
