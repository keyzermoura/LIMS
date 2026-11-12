"""Modelos da Fase 1: SolicitaÃ§Ã£o, Recebimento, Objetos de CustÃ³dia e Checklist (M0.3).

Revision ID: 0004_fase1_solicitacao_recebimento
Revises: 0003_audit_export
Create Date: 2026-11-11
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_fase1_solic_receb"
down_revision: str | None = "0003_audit_export"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


RECEIPT_DECISION = postgresql.ENUM(
    "ACCEPTED", "PENDING", "REJECTED", name="receipt_decision", create_type=False
)


def upgrade() -> None:
    # Enum compartilhado por duas tabelas: criar uma única vez (PostgreSQL).
    if op.get_bind().dialect.name == "postgresql":
        op.execute(
            "DO $$ BEGIN "
            "CREATE TYPE receipt_decision AS ENUM ('ACCEPTED', 'PENDING', 'REJECTED'); "
            "EXCEPTION WHEN duplicate_object THEN null; "
            "END $$;"
        )
    # 1. Tabelas de Solicitação
    op.create_table(
        "solicitations",
        sa.Column("solicitation_number", sa.String(length=32), nullable=False),
        sa.Column("requester_name", sa.String(length=160), nullable=False),
        sa.Column("requester_email", sa.String(length=255), nullable=True),
        sa.Column("requester_document", sa.String(length=64), nullable=True),
        sa.Column("requester_organization", sa.String(length=200), nullable=True),
        sa.Column("created_by_id", sa.UUID(), nullable=False),
        sa.Column("purpose", sa.Text(), nullable=True),
        sa.Column("request_type", sa.String(length=64), nullable=False),
        sa.Column("priority", sa.String(length=32), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "RASCUNHO",
                "SUBMETIDA",
                "RECEBIMENTO_REGISTRADO",
                "EM_TRATAMENTO",
                "CONCLUIDA",
                "CANCELADA",
                name="solicitation_status",
            ),
            nullable=False,
        ),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], name=op.f("fk_solicitations_created_by_id_users"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_solicitations")),
    )
    op.create_index(op.f("ix_solicitations_created_by_id"), "solicitations", ["created_by_id"], unique=False)
    op.create_index(op.f("ix_solicitations_solicitation_number"), "solicitations", ["solicitation_number"], unique=True)
    op.create_index(op.f("ix_solicitations_status"), "solicitations", ["status"], unique=False)

    op.create_table(
        "solicitation_items",
        sa.Column("solicitation_id", sa.UUID(), nullable=False),
        sa.Column("item_number", sa.Integer(), nullable=False),
        sa.Column("product_name", sa.String(length=200), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("manufacturer", sa.String(length=160), nullable=True),
        sa.Column("model", sa.String(length=120), nullable=True),
        sa.Column("serial_number", sa.String(length=120), nullable=True),
        sa.Column("lot_number", sa.String(length=120), nullable=True),
        sa.Column("declared_quantity", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("unit_of_measure", sa.String(length=32), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["solicitation_id"], ["solicitations.id"], name=op.f("fk_solicitation_items_solicitation_id_solicitations"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_solicitation_items")),
    )
    op.create_index(op.f("ix_solicitation_items_solicitation_id"), "solicitation_items", ["solicitation_id"], unique=False)

    # 2. Tabelas de Recebimento
    op.create_table(
        "receipts",
        sa.Column("solicitation_id", sa.UUID(), nullable=False),
        sa.Column("receipt_number", sa.String(length=32), nullable=False),
        sa.Column("arrived_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("received_by_id", sa.UUID(), nullable=False),
        sa.Column("arrival_location", sa.String(length=255), nullable=True),
        sa.Column("external_protocol", sa.String(length=120), nullable=True),
        sa.Column("delivery_method", sa.String(length=100), nullable=True),
        sa.Column("packaging_condition", sa.String(length=100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "REGISTRADO",
                "EM_CONFERENCIA",
                "PENDENTE",
                "CONCLUIDO",
                "CANCELADO",
                name="receipt_status",
            ),
            nullable=False,
        ),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.ForeignKeyConstraint(["received_by_id"], ["users.id"], name=op.f("fk_receipts_received_by_id_users"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["solicitation_id"], ["solicitations.id"], name=op.f("fk_receipts_solicitation_id_solicitations"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_receipts")),
    )
    op.create_index(op.f("ix_receipts_external_protocol"), "receipts", ["external_protocol"], unique=False)
    op.create_index(op.f("ix_receipts_receipt_number"), "receipts", ["receipt_number"], unique=True)
    op.create_index(op.f("ix_receipts_received_by_id"), "receipts", ["received_by_id"], unique=False)
    op.create_index(op.f("ix_receipts_solicitation_id"), "receipts", ["solicitation_id"], unique=True)
    op.create_index(op.f("ix_receipts_status"), "receipts", ["status"], unique=False)

    op.create_table(
        "receipt_items",
        sa.Column("receipt_id", sa.UUID(), nullable=False),
        sa.Column("solicitation_item_id", sa.UUID(), nullable=False),
        sa.Column(
            "presentation_status",
            sa.Enum("PRESENTED", "NOT_PRESENTED", name="presentation_status"),
            nullable=False,
        ),
        sa.Column("presented_quantity", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column(
            "conference_status",
            sa.Enum("PENDENTE", "CONFORME", "COM_RESSALVA", "NAO_CONFORME", name="conference_status"),
            nullable=False,
        ),
        sa.Column(
            "decision",
            RECEIPT_DECISION,
            nullable=True,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["receipt_id"], ["receipts.id"], name=op.f("fk_receipt_items_receipt_id_receipts"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["solicitation_item_id"], ["solicitation_items.id"], name=op.f("fk_receipt_items_solicitation_item_id_solicitation_items"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_receipt_items")),
    )
    op.create_index(op.f("ix_receipt_items_receipt_id"), "receipt_items", ["receipt_id"], unique=False)
    op.create_index(op.f("ix_receipt_items_solicitation_item_id"), "receipt_items", ["solicitation_item_id"], unique=False)

    # 3. Tabelas de CustÃ³dia FÃ­sica PrÃ©-Amostra
    op.create_table(
        "custody_objects",
        sa.Column("receipt_item_id", sa.UUID(), nullable=False),
        sa.Column("object_code", sa.String(length=32), nullable=False),
        sa.Column("grouping_description", sa.String(length=500), nullable=True),
        sa.Column("represented_quantity", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("current_location", sa.String(length=255), nullable=True),
        sa.Column("seal_number", sa.String(length=120), nullable=True),
        sa.Column(
            "status",
            sa.Enum("SOB_GUARDA", "EM_CONFERENCIA", "ACEITO", "RECUSADO", "DEVOLVIDO", "DESCARTADO", name="custody_object_status"),
            nullable=False,
        ),
        sa.Column("current_custodian_id", sa.UUID(), nullable=True),
        sa.Column("linked_device_sample_id", sa.UUID(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.ForeignKeyConstraint(["current_custodian_id"], ["users.id"], name=op.f("fk_custody_objects_current_custodian_id_users"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["linked_device_sample_id"], ["device_samples.id"], name=op.f("fk_custody_objects_linked_device_sample_id_device_samples"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["receipt_item_id"], ["receipt_items.id"], name=op.f("fk_custody_objects_receipt_item_id_receipt_items"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_custody_objects")),
    )
    op.create_index(op.f("ix_custody_objects_current_custodian_id"), "custody_objects", ["current_custodian_id"], unique=False)
    op.create_index(op.f("ix_custody_objects_linked_device_sample_id"), "custody_objects", ["linked_device_sample_id"], unique=True)
    op.create_index(op.f("ix_custody_objects_object_code"), "custody_objects", ["object_code"], unique=True)
    op.create_index(op.f("ix_custody_objects_receipt_item_id"), "custody_objects", ["receipt_item_id"], unique=False)
    op.create_index(op.f("ix_custody_objects_seal_number"), "custody_objects", ["seal_number"], unique=False)
    op.create_index(op.f("ix_custody_objects_status"), "custody_objects", ["status"], unique=False)

    op.create_table(
        "custody_events",
        sa.Column("custody_object_id", sa.UUID(), nullable=False),
        sa.Column(
            "event_type",
            sa.Enum("INGRESSO", "TRANSFERENCIA", "MUDANCA_LOCAL", "SAIDA", "ENCERRAMENTO", name="custody_event_type"),
            nullable=False,
        ),
        sa.Column("effective_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("from_custodian_id", sa.UUID(), nullable=True),
        sa.Column("to_custodian_id", sa.UUID(), nullable=True),
        sa.Column("from_location", sa.String(length=255), nullable=True),
        sa.Column("to_location", sa.String(length=255), nullable=True),
        sa.Column("reason", sa.String(length=500), nullable=False),
        sa.Column("registered_by_id", sa.UUID(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["custody_object_id"], ["custody_objects.id"], name=op.f("fk_custody_events_custody_object_id_custody_objects"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["from_custodian_id"], ["users.id"], name=op.f("fk_custody_events_from_custodian_id_users"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["registered_by_id"], ["users.id"], name=op.f("fk_custody_events_registered_by_id_users"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["to_custodian_id"], ["users.id"], name=op.f("fk_custody_events_to_custodian_id_users"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_custody_events")),
    )
    op.create_index(op.f("ix_custody_events_custody_object_id"), "custody_events", ["custody_object_id"], unique=False)
    op.create_index(op.f("ix_custody_events_from_custodian_id"), "custody_events", ["from_custodian_id"], unique=False)
    op.create_index(op.f("ix_custody_events_to_custodian_id"), "custody_events", ["to_custodian_id"], unique=False)

    # 4. Tabelas de Checklist Versionado
    op.create_table(
        "checklist_templates",
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_checklist_templates")),
    )
    op.create_index(op.f("ix_checklist_templates_category"), "checklist_templates", ["category"], unique=False)
    op.create_index(op.f("ix_checklist_templates_code"), "checklist_templates", ["code"], unique=True)

    op.create_table(
        "checklist_criteria",
        sa.Column("template_id", sa.UUID(), nullable=False),
        sa.Column("code", sa.String(length=16), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "criterion_class",
            sa.Enum("ELIMINATORIO", "SANEAVEL", "INFORMATIVO", name="criterion_class"),
            nullable=False,
        ),
        sa.Column("is_mandatory", sa.Boolean(), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["template_id"], ["checklist_templates.id"], name=op.f("fk_checklist_criteria_template_id_checklist_templates"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_checklist_criteria")),
    )
    op.create_index(op.f("ix_checklist_criteria_template_id"), "checklist_criteria", ["template_id"], unique=False)

    op.create_table(
        "checklist_answers",
        sa.Column("receipt_item_id", sa.UUID(), nullable=False),
        sa.Column("criterion_id", sa.UUID(), nullable=False),
        sa.Column(
            "result",
            sa.Enum("CONFORME", "NAO_CONFORME", "NAO_APLICAVEL", name="checklist_result"),
            nullable=False,
        ),
        sa.Column("justification", sa.Text(), nullable=True),
        sa.Column("evaluated_by_id", sa.UUID(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["criterion_id"], ["checklist_criteria.id"], name=op.f("fk_checklist_answers_criterion_id_checklist_criteria"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["evaluated_by_id"], ["users.id"], name=op.f("fk_checklist_answers_evaluated_by_id_users"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["receipt_item_id"], ["receipt_items.id"], name=op.f("fk_checklist_answers_receipt_item_id_receipt_items"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_checklist_answers")),
    )
    op.create_index(op.f("ix_checklist_answers_criterion_id"), "checklist_answers", ["criterion_id"], unique=False)
    op.create_index(op.f("ix_checklist_answers_receipt_item_id"), "checklist_answers", ["receipt_item_id"], unique=False)

    # 5. Tabelas de DecisÃµes e CoordenaÃ§Ã£o
    op.create_table(
        "receipt_decisions",
        sa.Column("receipt_item_id", sa.UUID(), nullable=False),
        sa.Column("custody_object_id", sa.UUID(), nullable=True),
        sa.Column(
            "decision",
            RECEIPT_DECISION,
            nullable=False,
        ),
        sa.Column("justification", sa.Text(), nullable=False),
        sa.Column("decided_by_id", sa.UUID(), nullable=False),
        sa.Column("requires_coordination_review", sa.Boolean(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["custody_object_id"], ["custody_objects.id"], name=op.f("fk_receipt_decisions_custody_object_id_custody_objects"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["decided_by_id"], ["users.id"], name=op.f("fk_receipt_decisions_decided_by_id_users"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["receipt_item_id"], ["receipt_items.id"], name=op.f("fk_receipt_decisions_receipt_item_id_receipt_items"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_receipt_decisions")),
    )
    op.create_index(op.f("ix_receipt_decisions_custody_object_id"), "receipt_decisions", ["custody_object_id"], unique=False)
    op.create_index(op.f("ix_receipt_decisions_receipt_item_id"), "receipt_decisions", ["receipt_item_id"], unique=False)

    op.create_table(
        "coordination_reviews",
        sa.Column("decision_id", sa.UUID(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("PENDENTE", "APROVADO", "DEVOLVIDO", "REJEITADO", name="coordination_review_status"),
            nullable=False,
        ),
        sa.Column("reviewed_by_id", sa.UUID(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["decision_id"], ["receipt_decisions.id"], name=op.f("fk_coordination_reviews_decision_id_receipt_decisions"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewed_by_id"], ["users.id"], name=op.f("fk_coordination_reviews_reviewed_by_id_users"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_coordination_reviews")),
    )
    op.create_index(op.f("ix_coordination_reviews_decision_id"), "coordination_reviews", ["decision_id"], unique=True)
    op.create_index(op.f("ix_coordination_reviews_status"), "coordination_reviews", ["status"], unique=False)

    # 6. AlteraÃ§Ãµes aditivas em device_samples
    op.add_column("device_samples", sa.Column("solicitation_id", sa.UUID(), nullable=True))
    op.add_column("device_samples", sa.Column("origin_custody_object_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        op.f("fk_device_samples_solicitation_id_solicitations"),
        "device_samples",
        "solicitations",
        ["solicitation_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        op.f("fk_device_samples_origin_custody_object_id_custody_objects"),
        "device_samples",
        "custody_objects",
        ["origin_custody_object_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(op.f("ix_device_samples_solicitation_id"), "device_samples", ["solicitation_id"], unique=False)
    op.create_index(op.f("ix_device_samples_origin_custody_object_id"), "device_samples", ["origin_custody_object_id"], unique=False)

    # Relaxar restriÃ§Ãµes NOT NULL para sÃ©rie e lote
    op.alter_column("device_samples", "serial_number", existing_type=sa.String(length=120), nullable=True)
    op.alter_column("device_samples", "lot_number", existing_type=sa.String(length=120), nullable=True)


def downgrade() -> None:
    # Restaura a obrigatoriedade original. Linhas criadas depois do upgrade sem
    # serie/lote tornam a reversao impossivel sem perda de dados: falhar alto e
    # claro e melhor do que inventar valores.
    bind = op.get_bind()
    pendentes = bind.execute(
        sa.text(
            "SELECT count(*) FROM device_samples "
            "WHERE serial_number IS NULL OR lot_number IS NULL"
        )
    ).scalar_one()
    if pendentes:
        raise RuntimeError(
            f"Downgrade 0004 abortado: {pendentes} amostra(s) sem serial_number/lot_number. "
            "Preencha os valores (ou trate manualmente) antes de reverter."
        )

    op.drop_constraint(op.f("fk_device_samples_origin_custody_object_id_custody_objects"), "device_samples", type_="foreignkey")
    op.drop_constraint(op.f("fk_device_samples_solicitation_id_solicitations"), "device_samples", type_="foreignkey")
    op.drop_index(op.f("ix_device_samples_origin_custody_object_id"), table_name="device_samples")
    op.drop_index(op.f("ix_device_samples_solicitation_id"), table_name="device_samples")
    op.drop_column("device_samples", "origin_custody_object_id")
    op.drop_column("device_samples", "solicitation_id")
    op.alter_column("device_samples", "serial_number", existing_type=sa.String(length=120), nullable=False)
    op.alter_column("device_samples", "lot_number", existing_type=sa.String(length=120), nullable=False)

    op.drop_table("coordination_reviews")
    op.drop_table("receipt_decisions")
    op.drop_table("checklist_answers")
    op.drop_table("checklist_criteria")
    op.drop_table("checklist_templates")
    op.drop_table("custody_events")
    op.drop_table("custody_objects")
    op.drop_table("receipt_items")
    op.drop_table("receipts")
    op.drop_table("solicitation_items")
    op.drop_table("solicitations")

    if op.get_bind().dialect.name == "postgresql":
        for enum_name in (
            "coordination_review_status", "checklist_result", "criterion_class",
            "custody_event_type", "custody_object_status", "receipt_decision",
            "conference_status", "presentation_status", "receipt_status", "solicitation_status",
        ):
            op.execute(f"DROP TYPE IF EXISTS {enum_name}")
