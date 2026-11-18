-- Proteções de integridade, imutabilidade e no-delete da Fase 5 (Sprint 5.4 / ALCOA+ / 21 CFR Part 11).
-- Este arquivo é idempotente e executado no startup de desenvolvimento e testes.
-- Cada bloco é separado por "-- @@statement".

CREATE SEQUENCE IF NOT EXISTS official_report_seq START WITH 1 INCREMENT BY 1;

-- @@statement

CREATE UNIQUE INDEX IF NOT EXISTS uq_instrument_import_dedup
ON instrument_data_imports (equipment_id, raw_file_hash_sha256);

-- @@statement

-- Função que congela registros após atingirem status terminal
CREATE OR REPLACE FUNCTION lims_freeze_after_terminal() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'Exclusao bloqueada em % (ALCOA+)', TG_TABLE_NAME
            USING ERRCODE = 'insufficient_privilege';
    END IF;

    -- Só congela quando o estado anterior já era terminal
    IF OLD.status::text = ANY (TG_ARGV[0]::text[]) THEN
        RAISE EXCEPTION 'Registro terminal em % nao pode ser alterado (21 CFR Part 11)',
            TG_TABLE_NAME USING ERRCODE = 'insufficient_privilege';
    END IF;

    RETURN NEW;
END;
$$;

-- @@statement

DROP TRIGGER IF EXISTS trg_test_executions_freeze ON test_executions;

-- @@statement

CREATE TRIGGER trg_test_executions_freeze
BEFORE UPDATE OR DELETE ON test_executions
FOR EACH ROW EXECUTE FUNCTION lims_freeze_after_terminal('{CONCLUIDA,CANCELADA,INTERROMPIDA}');

-- @@statement

DROP TRIGGER IF EXISTS trg_test_reviews_freeze ON test_reviews;

-- @@statement

CREATE TRIGGER trg_test_reviews_freeze
BEFORE UPDATE OR DELETE ON test_reviews
FOR EACH ROW EXECUTE FUNCTION lims_freeze_after_terminal('{APROVADO,REJEITADO,RESSALVAS}');

-- @@statement

-- Guarda para laudos oficiais: write-once para pdf_data e imutabilidade dos metadados
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

-- @@statement

DROP TRIGGER IF EXISTS trg_official_reports_guard ON official_reports;

-- @@statement

CREATE TRIGGER trg_official_reports_guard
BEFORE UPDATE OR DELETE ON official_reports
FOR EACH ROW EXECUTE FUNCTION lims_official_reports_guard();

-- @@statement

-- Guarda para importação de instrumentos: no-delete e imutabilidade do dado bruto
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

-- @@statement

DROP TRIGGER IF EXISTS trg_instrument_data_guard ON instrument_data_imports;

-- @@statement

CREATE TRIGGER trg_instrument_data_guard
BEFORE UPDATE OR DELETE ON instrument_data_imports
FOR EACH ROW EXECUTE FUNCTION lims_instrument_data_guard();

-- @@statement

DROP TRIGGER IF EXISTS trg_test_attachments_append_only ON test_attachments;

-- @@statement

CREATE TRIGGER trg_test_attachments_append_only
BEFORE UPDATE OR DELETE ON test_attachments
FOR EACH ROW EXECUTE FUNCTION lims_reject_mutation();

-- @@statement

DROP TRIGGER IF EXISTS trg_training_records_append_only ON training_records;

-- @@statement

CREATE TRIGGER trg_training_records_append_only
BEFORE UPDATE OR DELETE ON training_records
FOR EACH ROW EXECUTE FUNCTION lims_reject_mutation();

-- @@statement

DROP TRIGGER IF EXISTS trg_custody_events_append_only ON custody_events;

-- @@statement

CREATE TRIGGER trg_custody_events_append_only
BEFORE UPDATE OR DELETE ON custody_events
FOR EACH ROW EXECUTE FUNCTION lims_reject_mutation();

-- @@statement

DROP TRIGGER IF EXISTS trg_solicitations_no_delete ON solicitations;

-- @@statement

CREATE TRIGGER trg_solicitations_no_delete
BEFORE DELETE ON solicitations
FOR EACH ROW EXECUTE FUNCTION lims_reject_delete();

-- @@statement

DROP TRIGGER IF EXISTS trg_solicitation_items_no_delete ON solicitation_items;

-- @@statement

CREATE TRIGGER trg_solicitation_items_no_delete
BEFORE DELETE ON solicitation_items
FOR EACH ROW EXECUTE FUNCTION lims_reject_delete();

-- @@statement

DROP TRIGGER IF EXISTS trg_receipts_no_delete ON receipts;

-- @@statement

CREATE TRIGGER trg_receipts_no_delete
BEFORE DELETE ON receipts
FOR EACH ROW EXECUTE FUNCTION lims_reject_delete();

-- @@statement

DROP TRIGGER IF EXISTS trg_receipt_items_no_delete ON receipt_items;

-- @@statement

CREATE TRIGGER trg_receipt_items_no_delete
BEFORE DELETE ON receipt_items
FOR EACH ROW EXECUTE FUNCTION lims_reject_delete();

-- @@statement

DROP TRIGGER IF EXISTS trg_custody_objects_no_delete ON custody_objects;

-- @@statement

CREATE TRIGGER trg_custody_objects_no_delete
BEFORE DELETE ON custody_objects
FOR EACH ROW EXECUTE FUNCTION lims_reject_delete();

-- @@statement

DROP TRIGGER IF EXISTS trg_receipt_decisions_no_delete ON receipt_decisions;

-- @@statement

CREATE TRIGGER trg_receipt_decisions_no_delete
BEFORE DELETE ON receipt_decisions
FOR EACH ROW EXECUTE FUNCTION lims_reject_delete();

-- @@statement

DROP TRIGGER IF EXISTS trg_coordination_reviews_no_delete ON coordination_reviews;

-- @@statement

CREATE TRIGGER trg_coordination_reviews_no_delete
BEFORE DELETE ON coordination_reviews
FOR EACH ROW EXECUTE FUNCTION lims_reject_delete();

-- @@statement

DROP TRIGGER IF EXISTS trg_analyst_qualifications_no_delete ON analyst_qualifications;

-- @@statement

CREATE TRIGGER trg_analyst_qualifications_no_delete
BEFORE DELETE ON analyst_qualifications
FOR EACH ROW EXECUTE FUNCTION lims_reject_delete();
