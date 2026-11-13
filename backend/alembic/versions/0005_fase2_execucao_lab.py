"""Modelos da Fase 2: Catálogo de Métodos, Equipamentos Metrológicos e Execuções (M2.1).

Revision ID: 0005_fase2_execucao_lab
Revises: 0004_fase1_solic_receb
Create Date: 2026-11-12
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005_fase2_execucao_lab"
down_revision: str | None = "0004_fase1_solic_receb"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

EQUIPMENT_CALIBRATION_STATUS = postgresql.ENUM(
    "CALIBRADO",
    "VENCIDO",
    "EM_MANUTENCAO",
    "NAO_APLICAVEL",
    name="equipment_calibration_status",
    create_type=False,
)

EXECUTION_STATUS = postgresql.ENUM(
    "EM_ANDAMENTO",
    "CONCLUIDA",
    "INTERROMPIDA",
    "CANCELADA",
    name="execution_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"

    # Enums no PostgreSQL
    if is_pg:
        op.execute(
            "DO $$ BEGIN "
            "CREATE TYPE equipment_calibration_status AS ENUM ('CALIBRADO', 'VENCIDO', 'EM_MANUTENCAO', 'NAO_APLICAVEL'); "
            "EXCEPTION WHEN duplicate_object THEN null; "
            "END $$;"
        )
        op.execute(
            "DO $$ BEGIN "
            "CREATE TYPE execution_status AS ENUM ('EM_ANDAMENTO', 'CONCLUIDA', 'INTERROMPIDA', 'CANCELADA'); "
            "EXCEPTION WHEN duplicate_object THEN null; "
            "END $$;"
        )

    json_type = postgresql.JSONB(astext_type=sa.Text()) if is_pg else sa.JSON()

    # 1. Tabela test_methods (Catálogo de Métodos Padronizados)
    op.create_table(
        "test_methods",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("standard", sa.String(length=120), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("parameters_schema", json_type, server_default="{}", nullable=False),
        sa.Column("default_unit", sa.String(length=32), nullable=False),
        sa.Column("default_lower_limit", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("default_upper_limit", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("default_acceptance_criteria", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("metadata", json_type, server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_test_methods")),
    )
    op.create_index(op.f("ix_test_methods_code"), "test_methods", ["code"], unique=True)
    op.create_index(op.f("ix_test_methods_standard"), "test_methods", ["standard"], unique=False)
    op.create_index(op.f("ix_test_methods_category"), "test_methods", ["category"], unique=False)

    # 2. Tabela laboratory_equipment (Controle Metrológico de Equipamentos)
    op.create_table(
        "laboratory_equipment",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("equipment_type", sa.String(length=100), nullable=True),
        sa.Column("manufacturer", sa.String(length=160), nullable=True),
        sa.Column("model", sa.String(length=120), nullable=True),
        sa.Column("serial_number", sa.String(length=120), nullable=True),
        sa.Column("location", sa.String(length=160), nullable=True),
        sa.Column(
            "calibration_status",
            EQUIPMENT_CALIBRATION_STATUS if is_pg else sa.String(32),
            nullable=False,
        ),
        sa.Column("last_calibration_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("calibration_due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("certificate_number", sa.String(length=120), nullable=True),
        sa.Column("calibration_agency", sa.String(length=200), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("metadata", json_type, server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_laboratory_equipment")),
    )
    op.create_index(op.f("ix_laboratory_equipment_code"), "laboratory_equipment", ["code"], unique=True)
    op.create_index(op.f("ix_laboratory_equipment_equipment_type"), "laboratory_equipment", ["equipment_type"], unique=False)
    op.create_index(op.f("ix_laboratory_equipment_serial_number"), "laboratory_equipment", ["serial_number"], unique=False)
    op.create_index(op.f("ix_laboratory_equipment_calibration_status"), "laboratory_equipment", ["calibration_status"], unique=False)
    op.create_index(op.f("ix_laboratory_equipment_calibration_due_date"), "laboratory_equipment", ["calibration_due_date"], unique=False)
    op.create_index(
        "ix_equipment_status_due",
        "laboratory_equipment",
        ["calibration_status", "calibration_due_date"],
        unique=False,
    )

    # 3. Adição de colunas em lab_tests (aditivo e retrocompatível)
    op.add_column("lab_tests", sa.Column("method_id", sa.UUID(), nullable=True))
    op.add_column("lab_tests", sa.Column("equipment_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        op.f("fk_lab_tests_method_id_test_methods"),
        "lab_tests",
        "test_methods",
        ["method_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        op.f("fk_lab_tests_equipment_id_laboratory_equipment"),
        "lab_tests",
        "laboratory_equipment",
        ["equipment_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(op.f("ix_lab_tests_method_id"), "lab_tests", ["method_id"], unique=False)
    op.create_index(op.f("ix_lab_tests_equipment_id"), "lab_tests", ["equipment_id"], unique=False)

    # 4. Tabela test_executions (Execuções e Tentativas de Bancada ALCOA+)
    test_outcome_col = (
        postgresql.ENUM("APROVADO", "REPROVADO", "INCONCLUSIVO", name="test_outcome", create_type=False)
        if is_pg
        else sa.String(32)
    )

    op.create_table(
        "test_executions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("lab_test_id", sa.UUID(), nullable=False),
        sa.Column("execution_number", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            EXECUTION_STATUS if is_pg else sa.String(32),
            nullable=False,
        ),
        sa.Column("equipment_id", sa.UUID(), nullable=True),
        sa.Column("executed_by_id", sa.UUID(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("temperature_celsius", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("humidity_percent", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("pressure_hpa", sa.Numeric(precision=7, scale=2), nullable=True),
        sa.Column("raw_data", json_type, server_default="{}", nullable=False),
        sa.Column("result_value", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("result_text", sa.String(length=500), nullable=True),
        sa.Column("outcome", test_outcome_col, nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("interruption_reason", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("metadata", json_type, server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["lab_test_id"],
            ["lab_tests.id"],
            name=op.f("fk_test_executions_lab_test_id_lab_tests"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["equipment_id"],
            ["laboratory_equipment.id"],
            name=op.f("fk_test_executions_equipment_id_laboratory_equipment"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["executed_by_id"],
            ["users.id"],
            name=op.f("fk_test_executions_executed_by_id_users"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_test_executions")),
        sa.UniqueConstraint("lab_test_id", "execution_number", name="uq_test_execution_number"),
    )
    op.create_index(op.f("ix_test_executions_lab_test_id"), "test_executions", ["lab_test_id"], unique=False)
    op.create_index(op.f("ix_test_executions_status"), "test_executions", ["status"], unique=False)
    op.create_index(op.f("ix_test_executions_equipment_id"), "test_executions", ["equipment_id"], unique=False)
    op.create_index(op.f("ix_test_executions_executed_by_id"), "test_executions", ["executed_by_id"], unique=False)
    op.create_index("ix_executions_test_status", "test_executions", ["lab_test_id", "status"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"

    op.drop_table("test_executions")
    op.drop_constraint(op.f("fk_lab_tests_equipment_id_laboratory_equipment"), "lab_tests", type_="foreignkey")
    op.drop_constraint(op.f("fk_lab_tests_method_id_test_methods"), "lab_tests", type_="foreignkey")
    op.drop_index(op.f("ix_lab_tests_equipment_id"), table_name="lab_tests")
    op.drop_index(op.f("ix_lab_tests_method_id"), table_name="lab_tests")
    op.drop_column("lab_tests", "equipment_id")
    op.drop_column("lab_tests", "method_id")
    op.drop_table("laboratory_equipment")
    op.drop_table("test_methods")

    if is_pg:
        op.execute("DROP TYPE IF EXISTS execution_status;")
        op.execute("DROP TYPE IF EXISTS equipment_calibration_status;")
