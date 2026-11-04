-- Proteções de imutabilidade exigidas por 21 CFR Part 11 e RDC 665.
-- Este arquivo é idempotente e executado no startup (ou no deploy).
-- Cada bloco é separado por "-- @@statement".

CREATE SEQUENCE IF NOT EXISTS sample_accession_seq START WITH 1 INCREMENT BY 1;

-- @@statement

CREATE SEQUENCE IF NOT EXISTS capa_code_seq START WITH 1 INCREMENT BY 1;

-- @@statement

CREATE OR REPLACE FUNCTION lims_reject_mutation() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION
        'Operacao % bloqueada em %: registro append-only (21 CFR Part 11 / RDC 665)',
        TG_OP, TG_TABLE_NAME
        USING ERRCODE = 'insufficient_privilege';
END;
$$;

-- @@statement

DROP TRIGGER IF EXISTS trg_audit_logs_append_only ON audit_logs;

-- @@statement

CREATE TRIGGER trg_audit_logs_append_only
BEFORE UPDATE OR DELETE ON audit_logs
FOR EACH ROW EXECUTE FUNCTION lims_reject_mutation();

-- @@statement

DROP TRIGGER IF EXISTS trg_audit_logs_no_truncate ON audit_logs;

-- @@statement

CREATE TRIGGER trg_audit_logs_no_truncate
BEFORE TRUNCATE ON audit_logs
FOR EACH STATEMENT EXECUTE FUNCTION lims_reject_mutation();

-- @@statement

DROP TRIGGER IF EXISTS trg_lab_test_results_append_only ON lab_test_results;

-- @@statement

CREATE TRIGGER trg_lab_test_results_append_only
BEFORE UPDATE OR DELETE ON lab_test_results
FOR EACH ROW EXECUTE FUNCTION lims_reject_mutation();

-- @@statement

DROP TRIGGER IF EXISTS trg_custody_append_only ON chain_of_custody;

-- @@statement

CREATE TRIGGER trg_custody_append_only
BEFORE UPDATE OR DELETE ON chain_of_custody
FOR EACH ROW EXECUTE FUNCTION lims_reject_mutation();

-- @@statement

-- Assinaturas: manifesto imutável. Só é permitido gravar, uma única vez,
-- o consumo do token e o vínculo do payload assinado.
CREATE OR REPLACE FUNCTION lims_esignature_guard() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'Assinaturas eletronicas nao podem ser removidas (21 CFR Part 11)'
            USING ERRCODE = 'insufficient_privilege';
    END IF;

    IF NEW.user_id IS DISTINCT FROM OLD.user_id
       OR NEW.username_snapshot IS DISTINCT FROM OLD.username_snapshot
       OR NEW.full_name_snapshot IS DISTINCT FROM OLD.full_name_snapshot
       OR NEW.role_snapshot IS DISTINCT FROM OLD.role_snapshot
       OR NEW.entity_type IS DISTINCT FROM OLD.entity_type
       OR NEW.entity_id IS DISTINCT FROM OLD.entity_id
       OR NEW.action IS DISTINCT FROM OLD.action
       OR NEW.meaning IS DISTINCT FROM OLD.meaning
       OR NEW.reason IS DISTINCT FROM OLD.reason
       OR NEW.method IS DISTINCT FROM OLD.method
       OR NEW.manifest IS DISTINCT FROM OLD.manifest
       OR NEW.manifest_hash IS DISTINCT FROM OLD.manifest_hash
       OR NEW.token_jti IS DISTINCT FROM OLD.token_jti
       OR NEW.signed_at IS DISTINCT FROM OLD.signed_at
       OR NEW.expires_at IS DISTINCT FROM OLD.expires_at THEN
        RAISE EXCEPTION 'Manifesto de assinatura eletronica e imutavel (21 CFR Part 11)'
            USING ERRCODE = 'insufficient_privilege';
    END IF;

    -- Consumo é write-once: depois de consumido, não pode ser alterado nem
    -- "desconsumido" (o que permitiria reutilizar o token).
    IF OLD.consumed_at IS NOT NULL
       AND (NEW.consumed_at IS DISTINCT FROM OLD.consumed_at
            OR NEW.consumed_ip IS DISTINCT FROM OLD.consumed_ip
            OR NEW.consumed_user_agent IS DISTINCT FROM OLD.consumed_user_agent
            OR NEW.consumed_request_id IS DISTINCT FROM OLD.consumed_request_id) THEN
        RAISE EXCEPTION 'Consumo de assinatura eletronica e imutavel (21 CFR Part 11)'
            USING ERRCODE = 'insufficient_privilege';
    END IF;

    -- Vínculo ao payload também é write-once.
    IF (OLD.payload_hash IS NOT NULL
        AND NEW.payload_hash IS DISTINCT FROM OLD.payload_hash)
       OR (OLD.payload_snapshot IS NOT NULL
           AND NEW.payload_snapshot IS DISTINCT FROM OLD.payload_snapshot) THEN
        RAISE EXCEPTION 'Vinculo de assinatura eletronica e imutavel (21 CFR Part 11)'
            USING ERRCODE = 'insufficient_privilege';
    END IF;

    RETURN NEW;
END;
$$;

-- @@statement

DROP TRIGGER IF EXISTS trg_esignature_guard ON electronic_signatures;

-- @@statement

CREATE TRIGGER trg_esignature_guard
BEFORE UPDATE OR DELETE ON electronic_signatures
FOR EACH ROW EXECUTE FUNCTION lims_esignature_guard();

-- @@statement

-- Registros regulados nunca são apagados; usam-se estados (ex.: DESCARTADO).
CREATE OR REPLACE FUNCTION lims_reject_delete() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION
        'Exclusao de % bloqueada: registros regulados sao preservados (ALCOA+)',
        TG_TABLE_NAME
        USING ERRCODE = 'insufficient_privilege';
END;
$$;

-- @@statement

DROP TRIGGER IF EXISTS trg_device_samples_no_delete ON device_samples;

-- @@statement

CREATE TRIGGER trg_device_samples_no_delete
BEFORE DELETE ON device_samples
FOR EACH ROW EXECUTE FUNCTION lims_reject_delete();

-- @@statement

DROP TRIGGER IF EXISTS trg_lab_tests_no_delete ON lab_tests;

-- @@statement

CREATE TRIGGER trg_lab_tests_no_delete
BEFORE DELETE ON lab_tests
FOR EACH ROW EXECUTE FUNCTION lims_reject_delete();

-- @@statement

DROP TRIGGER IF EXISTS trg_capa_no_delete ON capa_actions;

-- @@statement

CREATE TRIGGER trg_capa_no_delete
BEFORE DELETE ON capa_actions
FOR EACH ROW EXECUTE FUNCTION lims_reject_delete();
