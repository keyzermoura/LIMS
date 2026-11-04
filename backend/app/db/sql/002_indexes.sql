-- Índices de consulta da trilha de auditoria e da cadeia de custódia.
-- @@statement

CREATE INDEX IF NOT EXISTS ix_audit_sequence_desc ON audit_logs (sequence DESC);

-- @@statement

CREATE INDEX IF NOT EXISTS ix_audit_action_time ON audit_logs (action, occurred_at DESC);

-- @@statement

CREATE INDEX IF NOT EXISTS ix_custody_sample_time ON chain_of_custody (device_sample_id, transferred_at DESC);

-- @@statement

CREATE INDEX IF NOT EXISTS ix_tests_sample_status ON lab_tests (device_sample_id, status);
