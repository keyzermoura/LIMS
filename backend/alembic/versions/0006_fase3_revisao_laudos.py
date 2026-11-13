"""Modelos da Fase 3: Revisão por Pares, Laudos Oficiais e Evidências (M3.1 / M3.2 / M3.3).

Revision ID: 0006_fase3_revisao_laudos
Revises: 0005_fase2_execucao_lab
Create Date: 2026-11-13
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006_fase3_revisao_laudos"
down_revision: str | None = "0005_fase2_execucao_lab"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

COORDINATION_REVIEW_STATUS = postgresql.ENUM(
    "PENDENTE",
    "APROVADO",
    "DEVOLVIDO",
    "REJEITADO",
    name="coordination_review_status",
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

    json_type = postgresql.JSONB(astext_type=sa.Text()) if is_pg else sa.JSON()
    review_status_type = COORDINATION_REVIEW_STATUS if is_pg else sa.String(32)
    test_outcome_type = TEST_OUTCOME if is_pg else sa.String(32)

    # 1. Adicionar review_status em lab_tests (retrocompatível com default PENDENTE)
    op.add_column(
        "lab_tests",
        sa.Column(
            "review_status",
            review_status_type,
            server_default="PENDENTE",
            nullable=False,
        ),
    )
    op.alter_column("lab_tests", "review_status", server_default=None)
    op.create_index(
        op.f("ix_lab_tests_review_status"),
        "lab_tests",
        ["review_status"],
        unique=False,
    )

    # 2. Tabela test_reviews (Revisão Técnica Colegiada por Pares - Sprint 3.1)
    op.create_table(
        "test_reviews",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("lab_test_id", sa.UUID(), nullable=False),
        sa.Column("review_number", sa.Integer(), nullable=False),
        sa.Column("status", review_status_type, nullable=False),
        sa.Column("reviewed_by_id", sa.UUID(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("justification", sa.Text(), nullable=True),
        sa.Column("signature_id", sa.UUID(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("metadata", json_type, server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["lab_test_id"],
            ["lab_tests.id"],
            name=op.f("fk_test_reviews_lab_test_id_lab_tests"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by_id"],
            ["users.id"],
            name=op.f("fk_test_reviews_reviewed_by_id_users"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["signature_id"],
            ["electronic_signatures.id"],
            name=op.f("fk_test_reviews_signature_id_electronic_signatures"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_test_reviews")),
        sa.UniqueConstraint("lab_test_id", "review_number", name="uq_test_review_number"),
    )
    op.create_index(op.f("ix_test_reviews_lab_test_id"), "test_reviews", ["lab_test_id"], unique=False)
    op.create_index(op.f("ix_test_reviews_status"), "test_reviews", ["status"], unique=False)
    op.create_index(op.f("ix_test_reviews_reviewed_by_id"), "test_reviews", ["reviewed_by_id"], unique=False)
    op.create_index("ix_test_reviews_test_status", "test_reviews", ["lab_test_id", "status"], unique=False)

    # 3. Tabela official_reports (Laudos Periciais Oficiais com Hash e QR Code - Sprint 3.2)
    op.create_table(
        "official_reports",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("report_number", sa.String(length=64), nullable=False),
        sa.Column("solicitation_id", sa.UUID(), nullable=True),
        sa.Column("device_sample_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("conclusion", test_outcome_type, nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("sha256_hash", sa.String(length=64), nullable=False),
        sa.Column("pdf_data", sa.LargeBinary(), nullable=True),
        sa.Column("issued_by_id", sa.UUID(), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("signature_id", sa.UUID(), nullable=False),
        sa.Column("auth_token", sa.String(length=64), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("metadata", json_type, server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["solicitation_id"],
            ["solicitations.id"],
            name=op.f("fk_official_reports_solicitation_id_solicitations"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["device_sample_id"],
            ["device_samples.id"],
            name=op.f("fk_official_reports_device_sample_id_device_samples"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["issued_by_id"],
            ["users.id"],
            name=op.f("fk_official_reports_issued_by_id_users"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["signature_id"],
            ["electronic_signatures.id"],
            name=op.f("fk_official_reports_signature_id_electronic_signatures"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_official_reports")),
    )
    op.create_index(op.f("ix_official_reports_report_number"), "official_reports", ["report_number"], unique=True)
    op.create_index(op.f("ix_official_reports_auth_token"), "official_reports", ["auth_token"], unique=True)
    op.create_index(op.f("ix_official_reports_solicitation_id"), "official_reports", ["solicitation_id"], unique=False)
    op.create_index(op.f("ix_official_reports_device_sample_id"), "official_reports", ["device_sample_id"], unique=False)
    op.create_index(op.f("ix_official_reports_conclusion"), "official_reports", ["conclusion"], unique=False)

    # 4. Tabela test_attachments (Evidências de Bancada e Dados Brutos - Sprint 3.3)
    op.create_table(
        "test_attachments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("lab_test_id", sa.UUID(), nullable=False),
        sa.Column("execution_id", sa.UUID(), nullable=True),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("sha256_hash", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("file_data", sa.LargeBinary(), nullable=False),
        sa.Column("uploaded_by_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["lab_test_id"],
            ["lab_tests.id"],
            name=op.f("fk_test_attachments_lab_test_id_lab_tests"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["execution_id"],
            ["test_executions.id"],
            name=op.f("fk_test_attachments_execution_id_test_executions"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["uploaded_by_id"],
            ["users.id"],
            name=op.f("fk_test_attachments_uploaded_by_id_users"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_test_attachments")),
    )
    op.create_index(op.f("ix_test_attachments_lab_test_id"), "test_attachments", ["lab_test_id"], unique=False)
    op.create_index(op.f("ix_test_attachments_execution_id"), "test_attachments", ["execution_id"], unique=False)
    op.create_index(op.f("ix_test_attachments_sha256_hash"), "test_attachments", ["sha256_hash"], unique=False)


def downgrade() -> None:
    op.drop_table("test_attachments")
    op.drop_table("official_reports")
    op.drop_table("test_reviews")
    op.drop_index(op.f("ix_lab_tests_review_status"), table_name="lab_tests")
    op.drop_column("lab_tests", "review_status")
