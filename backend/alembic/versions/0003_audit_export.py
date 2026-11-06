"""Ações de auditoria para exportação assinada da trilha.

O enum `audit_action` é nativo no PostgreSQL; incluir valores exige `ALTER
TYPE`. No SQLite (testes) a coluna é VARCHAR e não há alteração de schema.

Revision ID: 0003_audit_export
Revises: 0002_guards
Create Date: 2026-11-05
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0003_audit_export"
down_revision: str | None = "0002_guards"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return
    op.execute("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'EXPORT'")
    op.execute("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'EXPORT_VERIFIED'")


def downgrade() -> None:
    # PostgreSQL não remove valores de enum sem recriar o tipo e reescrever a
    # coluna. Como a trilha é append-only, os valores permanecem disponíveis;
    # o downgrade é intencionalmente no-op.
    pass
