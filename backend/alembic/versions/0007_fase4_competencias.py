"""Modelos da Fase 4: Qualificação de Analistas, Treinamento e Incerteza GUM (Sprints 4.1 e 4.2).

Revision ID: 0007_fase4_competencias
Revises: 0006_fase3_revisao_laudos
Create Date: 2026-11-13
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007_fase4_competencias"
down_revision: str | None = "0006_fase3_revisao_laudos"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

QUALIFICATION_STATUS = postgresql.ENUM(
    "QUALIFICADO",
    "EM_SUPERVISAO",
    "SUSPENSO",
    "EXPIRADO",
    name="qualification_status",
    create_type=False,
)

DECISION_RULE_TYPE = postgresql.ENUM(
    "SIMPLE_ACCEPTANCE",
    "GUARD_BAND_CONSERVATIVE",
    "GUARD_BAND_NON_BINARY",
    name="decision_rule_type",
    create_type=False,
)

CONFORMITY_STATUS = postgresql.ENUM(
    "CONFORME",
    "CONFORME_CONDICIONAL",
    "NAO_CONFORME_CONDICIONAL",
    "NAO_CONFORME",
    name="conformity_status",
    create_type=False,
)

TEST_OUTCOME = postgresql.ENUM(
    "APROVADO",
    "REPROVADO",
    "INCONCLUSIVO",
    name="test_outcome",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"

    # Criação dos Enums nativos no PostgreSQL
    if is_pg:
        op.execute(
            "DO $$ BEGIN "
            "CREATE TYPE qualification_status AS ENUM ('QUALIFICADO', 'EM_SUPERVISAO', 'SUSPENSO', 'EXPIRADO'); "
            "EXCEPTION WHEN duplicate_object THEN null; "
            "END $$;"
        )
        op.execute(
            "DO $$ BEGIN "
            "CREATE TYPE decision_rule_type AS ENUM ('SIMPLE_ACCEPTANCE', 'GUARD_BAND_CONSERVATIVE', 'GUARD_BAND_NON_BINARY'); "
            "EXCEPTION WHEN duplicate_object THEN null; "
            "END $$;"
        )
        op.execute(
            "DO $$ BEGIN "
            "CREATE TYPE conformity_status AS ENUM ('CONFORME', 'CONFORME_CONDICIONAL', 'NAO_CONFORME_CONDICIONAL', 'NAO_CONFORME'); "
            "EXCEPTION WHEN duplicate_object THEN null; "
            "END $$;"
        )

    json_type = postgresql.JSONB(astext_type=sa.Text()) if is_pg else sa.JSON()
    status_type = QUALIFICATION_STATUS if is_pg else sa.String(32)
    decision_type = DECISION_RULE_TYPE if is_pg else sa.String(32)
    conformity_type = CONFORMITY_STATUS if is_pg else sa.String(32)
    outcome_type = TEST_OUTCOME if is_pg else sa.String(32)

    # 1. Tabela analyst_qualifications (Matriz de Competência Analítica - ISO/IEC 17025 §6.2)
    op.create_table(
        "analyst_qualifications",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("method_id", sa.UUID(), nullable=False),
        sa.Column("status", status_type, nullable=False),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("authorized_by_id", sa.UUID(), nullable=False),
        sa.Column("signature_id", sa.UUID(), nullable=True),
        sa.Column("scope", sa.String(length=200), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("metadata", json_type, server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["authorized_by_id"],
            ["users.id"],
            name=op.f("fk_analyst_qualifications_authorized_by_id_users"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["method_id"],
            ["test_methods.id"],
            name=op.f("fk_analyst_qualifications_method_id_test_methods"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["signature_id"],
            ["electronic_signatures.id"],
            name=op.f("fk_analyst_qualifications_signature_id_electronic_signatures"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_analyst_qualifications_user_id_users"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_analyst_qualifications")),
        sa.UniqueConstraint("user_id", "method_id", name="uq_analyst_qualifications_user_method"),
    )
    op.create_index(op.f("ix_analyst_qualifications_user_id"), "analyst_qualifications", ["user_id"], unique=False)
    op.create_index(op.f("ix_analyst_qualifications_method_id"), "analyst_qualifications", ["method_id"], unique=False)
    op.create_index(op.f("ix_analyst_qualifications_status"), "analyst_qualifications", ["status"], unique=False)
    op.create_index(op.f("ix_analyst_qualifications_expires_at"), "analyst_qualifications", ["expires_at"], unique=False)

    # 2. Tabela training_records (Registros de Treinamento e Habilitação Prática)
    op.create_table(
        "training_records",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("qualification_id", sa.UUID(), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("provider", sa.String(length=200), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("hours", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("certificate_code", sa.String(length=100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("metadata", json_type, server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["qualification_id"],
            ["analyst_qualifications.id"],
            name=op.f("fk_training_records_qualification_id_analyst_qualifications"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_training_records_user_id_users"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_training_records")),
    )
    op.create_index(op.f("ix_training_records_user_id"), "training_records", ["user_id"], unique=False)
    op.create_index(op.f("ix_training_records_qualification_id"), "training_records", ["qualification_id"], unique=False)

    # 3. Tabela uncertainty_budgets (Motor de Incerteza GUM e Regras ILAC-G8 - Sprint 4.2)
    op.create_table(
        "uncertainty_budgets",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("method_id", sa.UUID(), nullable=True),
        sa.Column("lab_test_id", sa.UUID(), nullable=True),
        sa.Column("execution_id", sa.UUID(), nullable=True),
        sa.Column("equipment_id", sa.UUID(), nullable=True),
        sa.Column("unit", sa.String(length=32), nullable=False),
        sa.Column("measured_value", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("lower_limit", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("upper_limit", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("repeatability_readings", json_type, server_default="[]", nullable=False),
        sa.Column("components", json_type, server_default="[]", nullable=False),
        sa.Column("combined_uncertainty", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("effective_df", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("coverage_factor", sa.Numeric(precision=6, scale=3), nullable=False),
        sa.Column("confidence_level", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("expanded_uncertainty", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("guard_band_multiplier", sa.Numeric(precision=6, scale=3), nullable=False),
        sa.Column("guard_band_width", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("decision_rule", decision_type, nullable=False),
        sa.Column("conformity_status", conformity_type, nullable=False),
        sa.Column("recommended_outcome", outcome_type, nullable=False),
        sa.Column("conformity_statement", sa.Text(), nullable=False),
        sa.Column("calculated_by_id", sa.UUID(), nullable=False),
        sa.Column("signature_id", sa.UUID(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("metadata", json_type, server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["calculated_by_id"],
            ["users.id"],
            name=op.f("fk_uncertainty_budgets_calculated_by_id_users"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["equipment_id"],
            ["laboratory_equipment.id"],
            name=op.f("fk_uncertainty_budgets_equipment_id_laboratory_equipment"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["execution_id"],
            ["test_executions.id"],
            name=op.f("fk_uncertainty_budgets_execution_id_test_executions"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["lab_test_id"],
            ["lab_tests.id"],
            name=op.f("fk_uncertainty_budgets_lab_test_id_lab_tests"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["method_id"],
            ["test_methods.id"],
            name=op.f("fk_uncertainty_budgets_method_id_test_methods"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["signature_id"],
            ["electronic_signatures.id"],
            name=op.f("fk_uncertainty_budgets_signature_id_electronic_signatures"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_uncertainty_budgets")),
    )
    op.create_index(op.f("ix_uncertainty_budgets_method_id"), "uncertainty_budgets", ["method_id"], unique=False)
    op.create_index(op.f("ix_uncertainty_budgets_lab_test_id"), "uncertainty_budgets", ["lab_test_id"], unique=False)
    op.create_index(op.f("ix_uncertainty_budgets_execution_id"), "uncertainty_budgets", ["execution_id"], unique=False)
    op.create_index(op.f("ix_uncertainty_budgets_equipment_id"), "uncertainty_budgets", ["equipment_id"], unique=False)
    op.create_index(op.f("ix_uncertainty_budgets_conformity_status"), "uncertainty_budgets", ["conformity_status"], unique=False)


def downgrade() -> None:
    op.drop_table("uncertainty_budgets")
    op.drop_table("training_records")
    op.drop_table("analyst_qualifications")
    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP TYPE IF EXISTS conformity_status CASCADE")
        op.execute("DROP TYPE IF EXISTS decision_rule_type CASCADE")
        op.execute("DROP TYPE IF EXISTS qualification_status CASCADE")
