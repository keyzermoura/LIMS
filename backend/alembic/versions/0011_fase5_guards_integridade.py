"""Guardas de Integridade, Imutabilidade e No-Delete (Fase 5 / Sprint 5.4).

Revision ID: 0011_fase5_guards_integridade
Revises: 0010_fase5_instrument_data
Create Date: 2026-11-16
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0011_fase5_guards_integridade"
down_revision: str | None = "0010_fase5_instrument_data"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"

    # 1. Constraint única de deduplicação de instrumentos
    op.create_unique_constraint(
        "uq_instrument_import_dedup",
        "instrument_data_imports",
        ["equipment_id", "raw_file_hash_sha256"],
    )

    if is_pg:
        # 2. Sequence oficial de laudos
        op.execute("CREATE SEQUENCE IF NOT EXISTS official_report_seq START WITH 1 INCREMENT BY 1;")

        # 3. Função de congelamento pós-terminal
        op.execute(
            """
            CREATE OR REPLACE FUNCTION lims_freeze_after_terminal() RETURNS trigger
            LANGUAGE plpgsql AS $$
            BEGIN
                IF TG_OP = 'DELETE' THEN
                    RAISE EXCEPTION 'Exclusao bloqueada em % (ALCOA+)', TG_TABLE_NAME
                        USING ERRCODE = 'insufficient_privilege';
                END IF;

                IF OLD.status::text = ANY (TG_ARGV[0]::text[]) THEN
                    RAISE EXCEPTION 'Registro terminal em % nao pode ser alterado (21 CFR Part 11)',
                        TG_TABLE_NAME USING ERRCODE = 'insufficient_privilege';
                END IF;

                RETURN NEW;
            END;
            $$;
            """
        )

        # Triggers de freeze
        op.execute("DROP TRIGGER IF EXISTS trg_test_executions_freeze ON test_executions;")
        op.execute(
            """
            CREATE TRIGGER trg_test_executions_freeze
            BEFORE UPDATE OR DELETE ON test_executions
            FOR EACH ROW EXECUTE FUNCTION lims_freeze_after_terminal('{CONCLUIDA,CANCELADA,INTERROMPIDA}');
            """
        )

        op.execute("DROP TRIGGER IF EXISTS trg_test_reviews_freeze ON test_reviews;")
        op.execute(
            """
            CREATE TRIGGER trg_test_reviews_freeze
            BEFORE UPDATE OR DELETE ON test_reviews
            FOR EACH ROW EXECUTE FUNCTION lims_freeze_after_terminal('{APROVADO,REJEITADO,RESSALVAS}');
            """
        )

        # 4. Guarda de Laudos Oficiais (Write-Once para PDF, metadados imutáveis, no-delete)
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
        op.execute("DROP TRIGGER IF EXISTS trg_official_reports_guard ON official_reports;")
        op.execute(
            """
            CREATE TRIGGER trg_official_reports_guard
            BEFORE UPDATE OR DELETE ON official_reports
            FOR EACH ROW EXECUTE FUNCTION lims_official_reports_guard();
            """
        )

        # 5. Guarda de Instrument Data (imutabilidade dos dados brutos e no-delete)
        op.execute(
            """
            CREATE OR REPLACE FUNCTION lims_instrument_data_guard() RETURNS trigger
            LANGUAGE plpgsql AS $$
            BEGIN
                IF TG_OP = 'DELETE' THEN
                    RAISE EXCEPTION 'Exclusao de dados de instrumentos bloqueada (ALCOA+)'
                        USING ERRCODE = 'insufficient_privilege';
                END IF;

                IF OLD.raw_content IS DISTINCT FROM NEW.raw_content
                   OR OLD.raw_file_hash_sha256 IS DISTINCT FROM NEW.raw_file_hash_sha256
                   OR OLD.file_name IS DISTINCT FROM NEW.file_name
                   OR OLD.file_format IS DISTINCT FROM NEW.file_format
                   OR OLD.equipment_id IS DISTINCT FROM NEW.equipment_id
                   OR OLD.imported_by_id IS DISTINCT FROM NEW.imported_by_id THEN
                    RAISE EXCEPTION 'Dados brutos de aquisicao de instrumento sao imutaveis (21 CFR Part 11)'
                        USING ERRCODE = 'insufficient_privilege';
                END IF;

                RETURN NEW;
            END;
            $$;
            """
        )
        op.execute("DROP TRIGGER IF EXISTS trg_instrument_data_guard ON instrument_data_imports;")
        op.execute(
            """
            CREATE TRIGGER trg_instrument_data_guard
            BEFORE UPDATE OR DELETE ON instrument_data_imports
            FOR EACH ROW EXECUTE FUNCTION lims_instrument_data_guard();
            """
        )

        # 6. Append-only para anexos, treinamentos e eventos de custódia
        op.execute("DROP TRIGGER IF EXISTS trg_test_attachments_append_only ON test_attachments;")
        op.execute(
            """
            CREATE TRIGGER trg_test_attachments_append_only
            BEFORE UPDATE OR DELETE ON test_attachments
            FOR EACH ROW EXECUTE FUNCTION lims_reject_mutation();
            """
        )

        op.execute("DROP TRIGGER IF EXISTS trg_training_records_append_only ON training_records;")
        op.execute(
            """
            CREATE TRIGGER trg_training_records_append_only
            BEFORE UPDATE OR DELETE ON training_records
            FOR EACH ROW EXECUTE FUNCTION lims_reject_mutation();
            """
        )

        op.execute("DROP TRIGGER IF EXISTS trg_custody_events_append_only ON custody_events;")
        op.execute(
            """
            CREATE TRIGGER trg_custody_events_append_only
            BEFORE UPDATE OR DELETE ON custody_events
            FOR EACH ROW EXECUTE FUNCTION lims_reject_mutation();
            """
        )

        # 7. No-delete para registros regulados preservados
        no_delete_tables = [
            "solicitations",
            "solicitation_items",
            "receipts",
            "receipt_items",
            "custody_objects",
            "receipt_decisions",
            "coordination_reviews",
            "analyst_qualifications",
        ]
        for tbl in no_delete_tables:
            op.execute(f"DROP TRIGGER IF EXISTS trg_{tbl}_no_delete ON {tbl};")
            op.execute(
                f"""
                CREATE TRIGGER trg_{tbl}_no_delete
                BEFORE DELETE ON {tbl}
                FOR EACH ROW EXECUTE FUNCTION lims_reject_delete();
                """
            )


def downgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"

    if is_pg:
        no_delete_tables = [
            "solicitations",
            "solicitation_items",
            "receipts",
            "receipt_items",
            "custody_objects",
            "receipt_decisions",
            "coordination_reviews",
            "analyst_qualifications",
        ]
        for tbl in no_delete_tables:
            op.execute(f"DROP TRIGGER IF EXISTS trg_{tbl}_no_delete ON {tbl};")

        op.execute("DROP TRIGGER IF EXISTS trg_custody_events_append_only ON custody_events;")
        op.execute("DROP TRIGGER IF EXISTS trg_training_records_append_only ON training_records;")
        op.execute("DROP TRIGGER IF EXISTS trg_test_attachments_append_only ON test_attachments;")
        op.execute("DROP TRIGGER IF EXISTS trg_instrument_data_guard ON instrument_data_imports;")
        op.execute("DROP TRIGGER IF EXISTS trg_official_reports_guard ON official_reports;")
        op.execute("DROP TRIGGER IF EXISTS trg_test_reviews_freeze ON test_reviews;")
        op.execute("DROP TRIGGER IF EXISTS trg_test_executions_freeze ON test_executions;")

        op.execute("DROP FUNCTION IF EXISTS lims_instrument_data_guard();")
        op.execute("DROP FUNCTION IF EXISTS lims_official_reports_guard();")
        op.execute("DROP FUNCTION IF EXISTS lims_freeze_after_terminal();")
        op.execute("DROP SEQUENCE IF EXISTS official_report_seq;")

    op.drop_constraint("uq_instrument_import_dedup", "instrument_data_imports", type_="unique")
