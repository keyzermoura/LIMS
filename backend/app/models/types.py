"""Tipos SQLAlchemy compartilhados.

Reutilizar a MESMA instância de `Enum` entre tabelas evita `CREATE TYPE`
duplicado no PostgreSQL (ex.: `test_outcome` usado em `lab_tests` e
`lab_test_results`).
"""

from __future__ import annotations

from sqlalchemy import Enum as SAEnum

from app.models.enums import (
    AuditAction,
    CapaActionType,
    CapaEffectivenessStatus,
    CapaItemStatus,
    CapaSourceType,
    CapaStatus,
    ChecklistResult,
    ConferenceStatus,
    ConformityStatus,
    CoordinationReviewStatus,
    CriterionClass,
    CustodyEventType,
    CustodyObjectStatus,
    DecisionRuleType,
    EquipmentCalibrationStatus,
    ExecutionStatus,
    InstrumentFileFormat,
    InstrumentImportStatus,
    NotificationCategory,
    NotificationSeverity,
    PresentationStatus,
    QualificationStatus,
    ReceiptDecisionEnum,
    ReceiptStatus,
    SampleStatus,
    SignatureAction,
    SignatureMeaning,
    SolicitationStatus,
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
solicitation_status_type = SAEnum(
    SolicitationStatus, name="solicitation_status", validate_strings=True
)
receipt_status_type = SAEnum(ReceiptStatus, name="receipt_status", validate_strings=True)
presentation_status_type = SAEnum(
    PresentationStatus, name="presentation_status", validate_strings=True
)
conference_status_type = SAEnum(
    ConferenceStatus, name="conference_status", validate_strings=True
)
receipt_decision_type = SAEnum(
    ReceiptDecisionEnum, name="receipt_decision", validate_strings=True
)
custody_object_status_type = SAEnum(
    CustodyObjectStatus, name="custody_object_status", validate_strings=True
)
custody_event_type = SAEnum(CustodyEventType, name="custody_event_type", validate_strings=True)
criterion_class_type = SAEnum(CriterionClass, name="criterion_class", validate_strings=True)
checklist_result_type = SAEnum(ChecklistResult, name="checklist_result", validate_strings=True)
coordination_review_status_type = SAEnum(
    CoordinationReviewStatus, name="coordination_review_status", validate_strings=True
)
equipment_calibration_status_type = SAEnum(
    EquipmentCalibrationStatus, name="equipment_calibration_status", validate_strings=True
)
execution_status_type = SAEnum(
    ExecutionStatus, name="execution_status", validate_strings=True
)
qualification_status_type = SAEnum(
    QualificationStatus, name="qualification_status", validate_strings=True
)
decision_rule_type = SAEnum(
    DecisionRuleType, name="decision_rule_type", validate_strings=True
)
conformity_status_type = SAEnum(
    ConformityStatus, name="conformity_status", validate_strings=True
)
capa_source_type = SAEnum(
    CapaSourceType, name="capa_source_type", validate_strings=True
)
capa_action_type = SAEnum(
    CapaActionType, name="capa_action_type", validate_strings=True
)
capa_item_status = SAEnum(
    CapaItemStatus, name="capa_item_status", validate_strings=True
)
capa_effectiveness_status = SAEnum(
    CapaEffectivenessStatus, name="capa_effectiveness_status", validate_strings=True
)
notification_severity_type = SAEnum(
    NotificationSeverity, name="notification_severity", validate_strings=True
)
notification_category_type = SAEnum(
    NotificationCategory, name="notification_category", validate_strings=True
)
instrument_file_format_type = SAEnum(
    InstrumentFileFormat, name="instrument_file_format", validate_strings=True
)
instrument_import_status_type = SAEnum(
    InstrumentImportStatus, name="instrument_import_status", validate_strings=True
)
