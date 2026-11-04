"""Tipos SQLAlchemy compartilhados.

Reutilizar a MESMA instância de `Enum` entre tabelas evita `CREATE TYPE`
duplicado no PostgreSQL (ex.: `test_outcome` usado em `lab_tests` e
`lab_test_results`).
"""

from __future__ import annotations

from sqlalchemy import Enum as SAEnum

from app.models.enums import (
    AuditAction,
    CapaStatus,
    SampleStatus,
    SignatureAction,
    SignatureMeaning,
    TestOutcome,
    TestStatus,
    UserRole,
)

user_role_type = SAEnum(UserRole, name="user_role", validate_strings=True)
sample_status_type = SAEnum(SampleStatus, name="sample_status", validate_strings=True)
test_status_type = SAEnum(TestStatus, name="test_status", validate_strings=True)
test_outcome_type = SAEnum(TestOutcome, name="test_outcome", validate_strings=True)
capa_status_type = SAEnum(CapaStatus, name="capa_status", validate_strings=True)
audit_action_type = SAEnum(AuditAction, name="audit_action", validate_strings=True)
signature_action_type = SAEnum(
    SignatureAction, name="signature_action", validate_strings=True
)
signature_meaning_type = SAEnum(
    SignatureMeaning, name="signature_meaning", validate_strings=True
)
