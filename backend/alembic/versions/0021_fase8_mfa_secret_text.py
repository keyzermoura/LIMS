"""Altera mfa_secret para Text para suportar cifra simétrica em repouso (Gate G-B).

Revision ID: 0021_fase8_mfa_secret_text
Revises: 0020_fase8_outbox_webhooks
Create Date: 2026-11-17
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0021_fase8_mfa_secret_text"
down_revision = "0020_fase8_outbox_webhooks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Permite armazenar tokens cifrados (AES-GCM / Fernet) que excedem 64 caracteres
    op.alter_column(
        "users",
        "mfa_secret",
        type_=sa.Text(),
        existing_type=sa.String(length=64),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "users",
        "mfa_secret",
        type_=sa.String(length=64),
        existing_type=sa.Text(),
        existing_nullable=True,
    )
