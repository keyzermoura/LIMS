"""Horizonte 2: Motor de Investigação de Desvios Analíticos OOS e OOT (ISO 17025 §7.10 / FDA Guidance).

Revision ID: 0016_fase7_oos_investigations
Revises: 0015_fase7_reagentes_padroes
Create Date: 2026-11-17
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0016_fase7_oos_investigations"
down_revision: str | None = "0015_fase7_reagentes_padroes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DEVIATION_TYPE = postgresql.ENUM(
    "OOS",
    "OOT",
    name="deviation_type",
    create_type=False,
)
OOS_INVESTIGATION_STATUS = postgresql.ENUM(
    "PHASE_I_PENDING",
    "PHASE_I_COMPLETED",
    "PHASE_II_REQUIRED",
    "CONFIRMED_LAB_ERROR",
    "CONFIRMED_PRODUCT_FAILURE",
    "CLOSED",
    name="oos_investigation_status",
    create_type=False,
)
OOS_ROOT_CAUSE_CATEGORY = postgresql.ENUM(
    "EQUIPMENT_MALFUNCTION",
    "REAGENT_CONTAMINATION",
    "OPERATOR_ERROR",
    "CALCULATION_ERROR",
    "ENVIRONMENTAL_FLUCTUATION",
    "SAMPLE_ANOMALY",
    "METHOD_LIMITATION",
    "OTHER",
    name="oos_root_cause_category",
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
                CREATE TYPE deviation_type AS ENUM ('OOS', 'OOT');
            EXCEPTION WHEN duplicate_object THEN null;
            END $$;
        """)
        op.execute("""
            DO $$ BEGIN
                CREATE TYPE oos_investigation_status AS ENUM (
                    'PHASE_I_PENDING', 'PHASE_I_COMPLETED', 'PHASE_II_REQUIRED',
                    'CONFIRMED_LAB_ERROR', 'CONFIRMED_PRODUCT_FAILURE', 'CLOSED'
                );
            EXCEPTION WHEN duplicate_object THEN null;
            END $$;
        """)
        op.execute("""
            DO $$ BEGIN
                CREATE TYPE oos_root_cause_category AS ENUM (
                    'EQUIPMENT_MALFUNCTION', 'REAGENT_CONTAMINATION', 'OPERATOR_ERROR',
                    'CALCULATION_ERROR', 'ENVIRONMENTAL_FLUCTUATION', 'SAMPLE_ANOMALY',
                    'METHOD_LIMITATION', 'OTHER'
                );
            EXCEPTION WHEN duplicate_object THEN null;
            END $$;
        """)

    op.create_table(
        "oos_investigations",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("investigation_number", sa.String(32), nullable=False),
        sa.Column("lab_test_id", uuid_type, nullable=False),
        sa.Column("execution_id", uuid_type, nullable=True),
        sa.Column("deviation_type", DEVIATION_TYPE if is_pg else sa.String(16), nullable=False),
        sa.Column("status", OOS_INVESTIGATION_STATUS if is_pg else sa.String(32), nullable=False),
        sa.Column("initial_result", sa.Float(), nullable=True),
        sa.Column("initial_result_text", sa.Text(), nullable=True),
        sa.Column("specification_min", sa.Float(), nullable=True),
        sa.Column("specification_max", sa.Float(), nullable=True),
        sa.Column("specification_text", sa.String(255), nullable=True),
        sa.Column("detected_by_id", uuid_type, nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("phase_1_checklist", json_type, nullable=False, server_default="{}"),
        sa.Column("phase_1_conclusion", sa.Text(), nullable=True),
        sa.Column("phase_1_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("phase_1_responsible_id", uuid_type, nullable=True),
        sa.Column("phase_2_required", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("phase_2_plan", sa.Text(), nullable=True),
        sa.Column("phase_2_retest_results", json_type, nullable=False, server_default="[]"),
        sa.Column("root_cause_category", OOS_ROOT_CAUSE_CATEGORY if is_pg else sa.String(32), nullable=True),
        sa.Column("root_cause_description", sa.Text(), nullable=True),
        sa.Column("capa_action_id", uuid_type, nullable=True),
        sa.Column("final_disposition", sa.Text(), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_by_id", uuid_type, nullable=True),
        sa.Column("metadata", json_type, nullable=False, server_default="{}"),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["lab_test_id"], ["lab_tests.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["execution_id"], ["test_executions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["detected_by_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["phase_1_responsible_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["closed_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["capa_action_id"], ["capa_actions.id"], ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_oos_investigations_investigation_number"), "oos_investigations", ["investigation_number"], unique=True)
    op.create_index(op.f("ix_oos_investigations_lab_test_id"), "oos_investigations", ["lab_test_id"], unique=False)
    op.create_index(op.f("ix_oos_investigations_execution_id"), "oos_investigations", ["execution_id"], unique=False)
    op.create_index(op.f("ix_oos_investigations_deviation_type"), "oos_investigations", ["deviation_type"], unique=False)
    op.create_index(op.f("ix_oos_investigations_status"), "oos_investigations", ["status"], unique=False)
    op.create_index(op.f("ix_oos_investigations_root_cause_category"), "oos_investigations", ["root_cause_category"], unique=False)
    op.create_index(op.f("ix_oos_investigations_capa_action_id"), "oos_investigations", ["capa_action_id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"

    op.drop_table("oos_investigations")

    if is_pg:
        op.execute("DROP TYPE IF EXISTS oos_root_cause_category CASCADE;")
        op.execute("DROP TYPE IF EXISTS oos_investigation_status CASCADE;")
        op.execute("DROP TYPE IF EXISTS deviation_type CASCADE;")
