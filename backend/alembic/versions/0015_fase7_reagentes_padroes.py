"""Horizonte 2: Gestão de Reagentes, Padrões Analíticos (CRMs) e Bloqueio de Insumos Vencidos (ISO 17025 §6.4).

Revision ID: 0015_fase7_reagentes_padroes
Revises: 0014_fase6_mfa_totp
Create Date: 2026-11-17
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0015_fase7_reagentes_padroes"
down_revision: str | None = "0014_fase6_mfa_totp"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

REAGENT_TYPE = postgresql.ENUM(
    "REAGENT",
    "PRIMARY_STANDARD_CRM",
    "SECONDARY_STANDARD",
    "SOLVENT",
    "INDICATOR",
    name="reagent_type",
    create_type=False,
)
REAGENT_GRADE = postgresql.ENUM(
    "PA",
    "HPLC",
    "USP",
    "ANALYTICAL",
    name="reagent_grade",
    create_type=False,
)
REAGENT_BATCH_STATUS = postgresql.ENUM(
    "AVAILABLE",
    "IN_USE",
    "EXPIRED",
    "DEPLETED",
    "QUARANTINE",
    name="reagent_batch_status",
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
                CREATE TYPE reagent_type AS ENUM ('REAGENT', 'PRIMARY_STANDARD_CRM', 'SECONDARY_STANDARD', 'SOLVENT', 'INDICATOR');
            EXCEPTION WHEN duplicate_object THEN null;
            END $$;
        """)
        op.execute("""
            DO $$ BEGIN
                CREATE TYPE reagent_grade AS ENUM ('PA', 'HPLC', 'USP', 'ANALYTICAL');
            EXCEPTION WHEN duplicate_object THEN null;
            END $$;
        """)
        op.execute("""
            DO $$ BEGIN
                CREATE TYPE reagent_batch_status AS ENUM ('AVAILABLE', 'IN_USE', 'EXPIRED', 'DEPLETED', 'QUARANTINE');
            EXCEPTION WHEN duplicate_object THEN null;
            END $$;
        """)

    # 1. Tabela reagents
    op.create_table(
        "reagents",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("chemical_formula", sa.String(64), nullable=True),
        sa.Column("cas_number", sa.String(32), nullable=True),
        sa.Column("reagent_type", REAGENT_TYPE if is_pg else sa.String(32), nullable=False),
        sa.Column("grade", REAGENT_GRADE if is_pg else sa.String(32), nullable=False),
        sa.Column("storage_temperature_min", sa.Float(), nullable=True),
        sa.Column("storage_temperature_max", sa.Float(), nullable=True),
        sa.Column("hazard_classification", sa.String(120), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("metadata", json_type, nullable=False, server_default="{}"),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index(op.f("ix_reagents_code"), "reagents", ["code"], unique=True)
    op.create_index(op.f("ix_reagents_name"), "reagents", ["name"], unique=False)
    op.create_index(op.f("ix_reagents_cas_number"), "reagents", ["cas_number"], unique=False)
    op.create_index(op.f("ix_reagents_reagent_type"), "reagents", ["reagent_type"], unique=False)

    # 2. Tabela reagent_batches
    op.create_table(
        "reagent_batches",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("reagent_id", uuid_type, nullable=False),
        sa.Column("lot_number", sa.String(64), nullable=False),
        sa.Column("manufacturer", sa.String(120), nullable=False),
        sa.Column("catalog_number", sa.String(64), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expiration_date", sa.Date(), nullable=False),
        sa.Column("initial_quantity", sa.Float(), nullable=False),
        sa.Column("current_quantity", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(16), nullable=False),
        sa.Column("certificate_number", sa.String(64), nullable=True),
        sa.Column("uncertainty_value", sa.Float(), nullable=True),
        sa.Column("k_factor", sa.Float(), nullable=True),
        sa.Column("status", REAGENT_BATCH_STATUS if is_pg else sa.String(32), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["reagent_id"], ["reagents.id"], ondelete="RESTRICT"),
    )
    op.create_index(op.f("ix_reagent_batches_reagent_id"), "reagent_batches", ["reagent_id"], unique=False)
    op.create_index(op.f("ix_reagent_batches_lot_number"), "reagent_batches", ["lot_number"], unique=False)
    op.create_index(op.f("ix_reagent_batches_expiration_date"), "reagent_batches", ["expiration_date"], unique=False)
    op.create_index(op.f("ix_reagent_batches_status"), "reagent_batches", ["status"], unique=False)

    # 3. Tabela test_execution_reagent_usages
    op.create_table(
        "test_execution_reagent_usages",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("execution_id", uuid_type, nullable=False),
        sa.Column("batch_id", uuid_type, nullable=False),
        sa.Column("quantity_used", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(16), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("recorded_by_id", uuid_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["execution_id"], ["test_executions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["batch_id"], ["reagent_batches.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["recorded_by_id"], ["users.id"], ondelete="RESTRICT"),
    )
    op.create_index(op.f("ix_test_execution_reagent_usages_execution_id"), "test_execution_reagent_usages", ["execution_id"], unique=False)
    op.create_index(op.f("ix_test_execution_reagent_usages_batch_id"), "test_execution_reagent_usages", ["batch_id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"

    op.drop_table("test_execution_reagent_usages")
    op.drop_table("reagent_batches")
    op.drop_table("reagents")

    if is_pg:
        op.execute("DROP TYPE IF EXISTS reagent_batch_status CASCADE;")
        op.execute("DROP TYPE IF EXISTS reagent_grade CASCADE;")
        op.execute("DROP TYPE IF EXISTS reagent_type CASCADE;")
