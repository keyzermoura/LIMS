"""Modelos da Fase 4: Gestão Avançada de CAPA, RCA e Eficácia (Sprint 4.3).

Revision ID: 0008_fase4_capa
Revises: 0007_fase4_competencias
Create Date: 2026-11-16
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008_fase4_capa"
down_revision: str | None = "0007_fase4_competencias"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CAPA_SOURCE_TYPE = postgresql.ENUM(
    "ENSAIO_REPROVADO",
    "INCERTEZA_METROLOGICA",
    "EQUIPAMENTO_DESVIO",
    "AUDITORIA_INTERNA",
    "RECLAMACAO_CLIENTE",
    "CONTROLE_QUALIDADE",
    "OUTRO",
    name="capa_source_type",
    create_type=False,
)

CAPA_ACTION_TYPE = postgresql.ENUM(
    "CONTENCAO",
    "CORRETIVA",
    "PREVENTIVA",
    name="capa_action_type",
    create_type=False,
)

CAPA_ITEM_STATUS = postgresql.ENUM(
    "PENDENTE",
    "EM_ANDAMENTO",
    "CONCLUIDA",
    "CANCELADA",
    name="capa_item_status",
    create_type=False,
)

CAPA_EFFECTIVENESS_STATUS = postgresql.ENUM(
    "PENDENTE",
    "EFICAZ",
    "INEFICAZ",
    name="capa_effectiveness_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"

    if is_pg:
        op.execute(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'capa_source_type') THEN
                    CREATE TYPE capa_source_type AS ENUM (
                        'ENSAIO_REPROVADO', 'INCERTEZA_METROLOGICA', 'EQUIPAMENTO_DESVIO',
                        'AUDITORIA_INTERNA', 'RECLAMACAO_CLIENTE', 'CONTROLE_QUALIDADE', 'OUTRO'
                    );
                END IF;
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'capa_action_type') THEN
                    CREATE TYPE capa_action_type AS ENUM ('CONTENCAO', 'CORRETIVA', 'PREVENTIVA');
                END IF;
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'capa_item_status') THEN
                    CREATE TYPE capa_item_status AS ENUM ('PENDENTE', 'EM_ANDAMENTO', 'CONCLUIDA', 'CANCELADA');
                END IF;
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'capa_effectiveness_status') THEN
                    CREATE TYPE capa_effectiveness_status AS ENUM ('PENDENTE', 'EFICAZ', 'INEFICAZ');
                END IF;
            END$$;
            """
        )

    json_type = postgresql.JSONB(astext_type=sa.Text()) if is_pg else sa.JSON()
    source_enum = CAPA_SOURCE_TYPE if is_pg else sa.Enum(
        "ENSAIO_REPROVADO", "INCERTEZA_METROLOGICA", "EQUIPAMENTO_DESVIO",
        "AUDITORIA_INTERNA", "RECLAMACAO_CLIENTE", "CONTROLE_QUALIDADE", "OUTRO",
        name="capa_source_type"
    )
    action_type_enum = CAPA_ACTION_TYPE if is_pg else sa.Enum(
        "CONTENCAO", "CORRETIVA", "PREVENTIVA", name="capa_action_type"
    )
    item_status_enum = CAPA_ITEM_STATUS if is_pg else sa.Enum(
        "PENDENTE", "EM_ANDAMENTO", "CONCLUIDA", "CANCELADA", name="capa_item_status"
    )
    eff_status_enum = CAPA_EFFECTIVENESS_STATUS if is_pg else sa.Enum(
        "PENDENTE", "EFICAZ", "INEFICAZ", name="capa_effectiveness_status"
    )

    # 1. Novas colunas em capa_actions
    op.add_column(
        "capa_actions",
        sa.Column(
            "source_type",
            source_enum,
            nullable=False,
            server_default="ENSAIO_REPROVADO",
        ),
    )
    op.add_column("capa_actions", sa.Column("containment_action", sa.Text(), nullable=True))
    op.add_column("capa_actions", sa.Column("ishikawa_causes", json_type, nullable=True))
    op.add_column("capa_actions", sa.Column("five_whys", json_type, nullable=True))
    op.add_column("capa_actions", sa.Column("target_effectiveness_date", sa.Date(), nullable=True))
    op.add_column(
        "capa_actions",
        sa.Column(
            "effectiveness_status",
            eff_status_enum,
            nullable=False,
            server_default="PENDENTE",
        ),
    )
    op.add_column("capa_actions", sa.Column("effectiveness_evaluator_id", sa.Uuid(), nullable=True))
    op.add_column("capa_actions", sa.Column("effectiveness_evaluated_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "capa_actions",
        sa.Column("recurrence_detected", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )

    op.create_foreign_key(
        op.f("fk_capa_actions_effectiveness_evaluator_id_users"),
        "capa_actions",
        "users",
        ["effectiveness_evaluator_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(op.f("ix_capa_actions_source_type"), "capa_actions", ["source_type"], unique=False)
    op.create_index(op.f("ix_capa_actions_effectiveness_status"), "capa_actions", ["effectiveness_status"], unique=False)

    # 2. Tabela capa_action_items
    op.create_table(
        "capa_action_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("capa_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("action_type", action_type_enum, nullable=False),
        sa.Column("assigned_to_id", sa.Uuid(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("status", item_status_enum, nullable=False, server_default="PENDENTE"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completion_evidence", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(
            ["assigned_to_id"],
            ["users.id"],
            name=op.f("fk_capa_action_items_assigned_to_id_users"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["capa_id"],
            ["capa_actions.id"],
            name=op.f("fk_capa_action_items_capa_id_capa_actions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_capa_action_items")),
    )
    op.create_index(op.f("ix_capa_action_items_capa_id"), "capa_action_items", ["capa_id"], unique=False)
    op.create_index(op.f("ix_capa_action_items_action_type"), "capa_action_items", ["action_type"], unique=False)
    op.create_index(op.f("ix_capa_action_items_assigned_to_id"), "capa_action_items", ["assigned_to_id"], unique=False)
    op.create_index(op.f("ix_capa_action_items_status"), "capa_action_items", ["status"], unique=False)


def downgrade() -> None:
    op.drop_table("capa_action_items")
    op.drop_index(op.f("ix_capa_actions_effectiveness_status"), table_name="capa_actions")
    op.drop_index(op.f("ix_capa_actions_source_type"), table_name="capa_actions")
    op.drop_constraint(op.f("fk_capa_actions_effectiveness_evaluator_id_users"), "capa_actions", type_="foreignkey")
    op.drop_column("capa_actions", "recurrence_detected")
    op.drop_column("capa_actions", "effectiveness_evaluated_at")
    op.drop_column("capa_actions", "effectiveness_evaluator_id")
    op.drop_column("capa_actions", "effectiveness_status")
    op.drop_column("capa_actions", "target_effectiveness_date")
    op.drop_column("capa_actions", "five_whys")
    op.drop_column("capa_actions", "ishikawa_causes")
    op.drop_column("capa_actions", "containment_action")
    op.drop_column("capa_actions", "source_type")

    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP TYPE IF EXISTS capa_effectiveness_status CASCADE")
        op.execute("DROP TYPE IF EXISTS capa_item_status CASCADE")
        op.execute("DROP TYPE IF EXISTS capa_action_type CASCADE")
        op.execute("DROP TYPE IF EXISTS capa_source_type CASCADE")
