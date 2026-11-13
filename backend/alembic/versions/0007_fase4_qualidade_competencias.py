"""Modelos da Fase 4: Qualificação de Analistas e Registros de Treinamento (Sprint 4.1).

Revision ID: 0007_fase4_qualidade_competencias
Revises: 0006_fase3_revisao_laudos
Create Date: 2026-11-13
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007_fase4_qualidade_competencias"
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


def upgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"

    # Criação do Enum nativo no PostgreSQL
    if is_pg:
        op.execute(
            "DO $$ BEGIN "
            "CREATE TYPE qualification_status AS ENUM ('QUALIFICADO', 'EM_SUPERVISAO', 'SUSPENSO', 'EXPIRADO'); "
            "EXCEPTION WHEN duplicate_object THEN null; "
            "END $$;"
        )

    json_type = postgresql.JSONB(astext_type=sa.Text()) if is_pg else sa.JSON()
    status_type = QUALIFICATION_STATUS if is_pg else sa.String(32)

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


def downgrade() -> None:
    op.drop_table("training_records")
    op.drop_table("analyst_qualifications")
    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP TYPE IF EXISTS qualification_status CASCADE")
