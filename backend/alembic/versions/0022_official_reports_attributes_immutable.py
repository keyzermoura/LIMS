"""Adiciona attributes à lista de campos imutáveis do guarda de laudos oficiais (P4.1 / 21 CFR Part 11).

Revision ID: 0022_official_reports_attributes_immutable
Revises: 0021_fase8_mfa_secret_text
Create Date: 2026-11-18
"""

from __future__ import annotations

from alembic import op

revision = "0022_official_reports_attributes_immutable"
down_revision = "0021_fase8_mfa_secret_text"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION lims_official_reports_guard() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                RAISE EXCEPTION 'Laudos oficiais nao podem ser excluidos (21 CFR Part 11)'
                    USING ERRCODE = 'insufficient_privilege';
            END IF;

            IF OLD.pdf_data IS NOT NULL AND NEW.pdf_data IS DISTINCT FROM OLD.pdf_data THEN
                RAISE EXCEPTION 'PDF do laudo e write-once'
                    USING ERRCODE = 'insufficient_privilege';
            END IF;

            IF OLD.report_number IS DISTINCT FROM NEW.report_number
               OR OLD.solicitation_id IS DISTINCT FROM NEW.solicitation_id
               OR OLD.device_sample_id IS DISTINCT FROM NEW.device_sample_id
               OR OLD.title IS DISTINCT FROM NEW.title
               OR OLD.conclusion IS DISTINCT FROM NEW.conclusion
               OR OLD.summary IS DISTINCT FROM NEW.summary
               OR OLD.sha256_hash IS DISTINCT FROM NEW.sha256_hash
               OR OLD.issued_by_id IS DISTINCT FROM NEW.issued_by_id
               OR OLD.issued_at IS DISTINCT FROM NEW.issued_at
               OR OLD.signature_id IS DISTINCT FROM NEW.signature_id
               OR OLD.auth_token IS DISTINCT FROM NEW.auth_token
               OR OLD.attributes IS DISTINCT FROM NEW.attributes THEN
                RAISE EXCEPTION 'Campos de laudo oficial sao imutaveis (21 CFR Part 11)'
                    USING ERRCODE = 'insufficient_privilege';
            END IF;

            RETURN NEW;
        END;
        $$;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION lims_official_reports_guard() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                RAISE EXCEPTION 'Laudos oficiais nao podem ser excluidos (21 CFR Part 11)'
                    USING ERRCODE = 'insufficient_privilege';
            END IF;

            IF OLD.pdf_data IS NOT NULL AND NEW.pdf_data IS DISTINCT FROM OLD.pdf_data THEN
                RAISE EXCEPTION 'PDF do laudo e write-once'
                    USING ERRCODE = 'insufficient_privilege';
            END IF;

            IF OLD.report_number IS DISTINCT FROM NEW.report_number
               OR OLD.solicitation_id IS DISTINCT FROM NEW.solicitation_id
               OR OLD.device_sample_id IS DISTINCT FROM NEW.device_sample_id
               OR OLD.title IS DISTINCT FROM NEW.title
               OR OLD.conclusion IS DISTINCT FROM NEW.conclusion
               OR OLD.summary IS DISTINCT FROM NEW.summary
               OR OLD.sha256_hash IS DISTINCT FROM NEW.sha256_hash
               OR OLD.issued_by_id IS DISTINCT FROM NEW.issued_by_id
               OR OLD.issued_at IS DISTINCT FROM NEW.issued_at
               OR OLD.signature_id IS DISTINCT FROM NEW.signature_id
               OR OLD.auth_token IS DISTINCT FROM NEW.auth_token THEN
                RAISE EXCEPTION 'Campos de laudo oficial sao imutaveis (21 CFR Part 11)'
                    USING ERRCODE = 'insufficient_privilege';
            END IF;

            RETURN NEW;
        END;
        $$;
        """
    )
