"""Horizonte 2: Cadeia Física de Armazenamento, Retenção de Contraprova e Descarte (H2.3 & H2.4).

Revision ID: 0017_fase7_armazena_descarte
Revises: 0016_fase7_oos_investigations
Create Date: 2026-11-17
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0017_fase7_armazena_descarte"
down_revision: str | None = "0016_fase7_oos_investigations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

STORAGE_LOCATION_TYPE = postgresql.ENUM(
    "ULTRA_FREEZER",
    "COLD_CHAMBER",
    "REFRIGERATOR",
    "CONTROLLED_ROOM",
    "DESICCATOR",
    "HAZARDOUS_CABINET",
    name="storage_location_type",
    create_type=False,
)
RETENTION_TYPE = postgresql.ENUM(
    "CONTRAPROVA_PERICIAL",
    "TESTEMUNHA_QUALIDADE",
    "RETENCAO_REGULATORIA",
    name="retention_type",
    create_type=False,
)
RETENTION_STATUS = postgresql.ENUM(
    "ACTIVE",
    "EXTENDED",
    "EXPIRED",
    "DISPOSED",
    name="retention_status",
    create_type=False,
)
DISPOSAL_METHOD = postgresql.ENUM(
    "INCINERACAO",
    "AUTOCLAVAGEM",
    "DESCARTE_QUIMICO_ESPECIALIZADO",
    "DEVOLUCAO_ORGAO_REGULADOR",
    "RECICLAGEM_CONTROLADA",
    name="disposal_method",
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
                CREATE TYPE storage_location_type AS ENUM (
                    'ULTRA_FREEZER', 'COLD_CHAMBER', 'REFRIGERATOR',
                    'CONTROLLED_ROOM', 'DESICCATOR', 'HAZARDOUS_CABINET'
                );
            EXCEPTION WHEN duplicate_object THEN null;
            END $$;
        """)
        op.execute("""
            DO $$ BEGIN
                CREATE TYPE retention_type AS ENUM (
                    'CONTRAPROVA_PERICIAL', 'TESTEMUNHA_QUALIDADE', 'RETENCAO_REGULATORIA'
                );
            EXCEPTION WHEN duplicate_object THEN null;
            END $$;
        """)
        op.execute("""
            DO $$ BEGIN
                CREATE TYPE retention_status AS ENUM (
                    'ACTIVE', 'EXTENDED', 'EXPIRED', 'DISPOSED'
                );
            EXCEPTION WHEN duplicate_object THEN null;
            END $$;
        """)
        op.execute("""
            DO $$ BEGIN
                CREATE TYPE disposal_method AS ENUM (
                    'INCINERACAO', 'AUTOCLAVAGEM', 'DESCARTE_QUIMICO_ESPECIALIZADO',
                    'DEVOLUCAO_ORGAO_REGULADOR', 'RECICLAGEM_CONTROLADA'
                );
            EXCEPTION WHEN duplicate_object THEN null;
            END $$;
        """)
        op.execute("""
            DO $$ BEGIN
                ALTER TYPE signature_meaning ADD VALUE IF NOT EXISTS 'EXECUCAO_DESCARTE';
                ALTER TYPE signature_meaning ADD VALUE IF NOT EXISTS 'TESTEMUNHA_DESCARTE';
            EXCEPTION WHEN duplicate_object THEN null;
            END $$;
        """)

    # 1. Tabela storage_locations
    op.create_table(
        "storage_locations",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("location_type", STORAGE_LOCATION_TYPE if is_pg else sa.String(32), nullable=False),
        sa.Column("room", sa.String(64), nullable=False),
        sa.Column("temperature_target_celsius", sa.Float(), nullable=False),
        sa.Column("temperature_min_celsius", sa.Float(), nullable=False),
        sa.Column("temperature_max_celsius", sa.Float(), nullable=False),
        sa.Column("humidity_max_percent", sa.Float(), nullable=True),
        sa.Column("capacity_units", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("metadata", json_type, nullable=False, server_default="{}"),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index(op.f("ix_storage_locations_code"), "storage_locations", ["code"], unique=True)
    op.create_index(op.f("ix_storage_locations_location_type"), "storage_locations", ["location_type"], unique=False)

    # 2. Tabela sample_storage_movements
    op.create_table(
        "sample_storage_movements",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("sample_id", uuid_type, nullable=False),
        sa.Column("from_location_id", uuid_type, nullable=True),
        sa.Column("to_location_id", uuid_type, nullable=False),
        sa.Column("moved_by_id", uuid_type, nullable=False),
        sa.Column("moved_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("reason", sa.String(255), nullable=False),
        sa.Column("temperature_at_movement", sa.Float(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["sample_id"], ["device_samples.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["from_location_id"], ["storage_locations.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["to_location_id"], ["storage_locations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["moved_by_id"], ["users.id"], ondelete="RESTRICT"),
    )
    op.create_index(op.f("ix_sample_storage_movements_sample_id"), "sample_storage_movements", ["sample_id"], unique=False)
    op.create_index(op.f("ix_sample_storage_movements_from_location_id"), "sample_storage_movements", ["from_location_id"], unique=False)
    op.create_index(op.f("ix_sample_storage_movements_to_location_id"), "sample_storage_movements", ["to_location_id"], unique=False)

    # 3. Tabela sample_retentions (Contraprova pericial)
    op.create_table(
        "sample_retentions",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("sample_id", uuid_type, nullable=False),
        sa.Column("storage_location_id", uuid_type, nullable=False),
        sa.Column("retention_type", RETENTION_TYPE if is_pg else sa.String(32), nullable=False),
        sa.Column("retained_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("retain_until", sa.Date(), nullable=False),
        sa.Column("quantity_retained", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(16), nullable=False),
        sa.Column("seal_number", sa.String(64), nullable=False),
        sa.Column("status", RETENTION_STATUS if is_pg else sa.String(32), nullable=False),
        sa.Column("responsible_id", uuid_type, nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["sample_id"], ["device_samples.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["storage_location_id"], ["storage_locations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["responsible_id"], ["users.id"], ondelete="RESTRICT"),
    )
    op.create_index(op.f("ix_sample_retentions_sample_id"), "sample_retentions", ["sample_id"], unique=True)
    op.create_index(op.f("ix_sample_retentions_storage_location_id"), "sample_retentions", ["storage_location_id"], unique=False)
    op.create_index(op.f("ix_sample_retentions_retention_type"), "sample_retentions", ["retention_type"], unique=False)
    op.create_index(op.f("ix_sample_retentions_seal_number"), "sample_retentions", ["seal_number"], unique=False)
    op.create_index(op.f("ix_sample_retentions_status"), "sample_retentions", ["status"], unique=False)
    op.create_index(op.f("ix_sample_retentions_retain_until"), "sample_retentions", ["retain_until"], unique=False)

    # 4. Tabela sample_disposal_records (Descarte com Dupla Assinatura)
    op.create_table(
        "sample_disposal_records",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("sample_id", uuid_type, nullable=False),
        sa.Column("retention_id", uuid_type, nullable=True),
        sa.Column("disposal_manifest_number", sa.String(64), nullable=False),
        sa.Column("disposal_method", DISPOSAL_METHOD if is_pg else sa.String(32), nullable=False),
        sa.Column("disposed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("disposed_by_id", uuid_type, nullable=False),
        sa.Column("witness_id", uuid_type, nullable=False),
        sa.Column("primary_signature_id", uuid_type, nullable=False),
        sa.Column("witness_signature_id", uuid_type, nullable=False),
        sa.Column("environmental_license_number", sa.String(64), nullable=True),
        sa.Column("waste_company_name", sa.String(120), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["sample_id"], ["device_samples.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["retention_id"], ["sample_retentions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["disposed_by_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["witness_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["primary_signature_id"], ["electronic_signatures.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["witness_signature_id"], ["electronic_signatures.id"], ondelete="RESTRICT"),
    )
    op.create_index(op.f("ix_sample_disposal_records_sample_id"), "sample_disposal_records", ["sample_id"], unique=False)
    op.create_index(op.f("ix_sample_disposal_records_retention_id"), "sample_disposal_records", ["retention_id"], unique=False)
    op.create_index(op.f("ix_sample_disposal_records_disposal_manifest_number"), "sample_disposal_records", ["disposal_manifest_number"], unique=True)
    op.create_index(op.f("ix_sample_disposal_records_disposal_method"), "sample_disposal_records", ["disposal_method"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"

    op.drop_table("sample_disposal_records")
    op.drop_table("sample_retentions")
    op.drop_table("sample_storage_movements")
    op.drop_table("storage_locations")

    if is_pg:
        op.execute("DROP TYPE IF EXISTS disposal_method CASCADE;")
        op.execute("DROP TYPE IF EXISTS retention_status CASCADE;")
        op.execute("DROP TYPE IF EXISTS retention_type CASCADE;")
        op.execute("DROP TYPE IF EXISTS storage_location_type CASCADE;")
