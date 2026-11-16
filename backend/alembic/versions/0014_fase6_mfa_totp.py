"""Horizonte 1: MFA TOTP e Códigos de Recuperação para Assinatura Eletrônica (21 CFR Part 11).

Revision ID: 0014_fase6_mfa_totp
Revises: 0013_fase6_laudos_emendas
Create Date: 2026-11-16
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0014_fase6_mfa_totp"
down_revision: str | None = "0013_fase6_laudos_emendas"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"
    json_type = postgresql.JSONB(astext_type=sa.Text()) if is_pg else sa.JSON()

    # Adicionar colunas de MFA TOTP na tabela users
    op.add_column("users", sa.Column("mfa_secret", sa.String(length=64), nullable=True))
    op.add_column("users", sa.Column("mfa_recovery_codes", json_type, nullable=True))


def downgrade() -> None:
    op.drop_column("users", "mfa_recovery_codes")
    op.drop_column("users", "mfa_secret")
