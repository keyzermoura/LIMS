"""Registro central dos modelos (necessário para o metadata do SQLAlchemy)."""

from app.models.audit_log import AuditLog
from app.models.base import Base
from app.models.capa_action import CapaAction
from app.models.capa_action_item import CapaActionItem
from app.models.chain_of_custody import ChainOfCustody
from app.models.checklist import ChecklistAnswer, ChecklistCriterion, ChecklistTemplate
from app.models.decision import CoordinationReview, ReceiptDecision
from app.models.device_sample import DeviceSample
from app.models.electronic_signature import ElectronicSignature
from app.models.equipment import LaboratoryEquipment
from app.models.idempotency import IdempotencyKey
from app.models.instrument_data import InstrumentDataImport
from app.models.lab_test import LabTest, LabTestResult
from app.models.notification import Notification
from app.models.official_report import OfficialReport
from app.models.oos_investigation import OOSInvestigation
from app.models.outbox import IntegrationOutbox
from app.models.qc_spc import QCRun
from app.models.qualification import AnalystQualification, TrainingRecord
from app.models.reagent import Reagent, ReagentBatch, TestExecutionReagentUsage
from app.models.receipt import CustodyEvent, CustodyObject, Receipt, ReceiptItem
from app.models.service_client import ServiceClient
from app.models.solicitation import Solicitation, SolicitationItem
from app.models.storage_and_disposal import (
    SampleDisposalRecord,
    SampleRetention,
    SampleStorageMovement,
    StorageLocation,
)
from app.models.test_attachment import TestAttachment
from app.models.test_execution import TestExecution
from app.models.test_method import TestMethod
from app.models.test_review import TestReview
from app.models.uncertainty import UncertaintyBudget
from app.models.user import RefreshToken, User
from app.models.webhook import WebhookDelivery, WebhookSubscription

__all__ = [
    "AnalystQualification",
    "AuditLog",
    "Base",
    "CapaAction",
    "CapaActionItem",
    "ChainOfCustody",
    "ChecklistAnswer",
    "ChecklistCriterion",
    "ChecklistTemplate",
    "CoordinationReview",
    "CustodyEvent",
    "CustodyObject",
    "DeviceSample",
    "ElectronicSignature",
    "IdempotencyKey",
    "InstrumentDataImport",
    "IntegrationOutbox",
    "LabTest",
    "LabTestResult",
    "LaboratoryEquipment",
    "Notification",
    "OfficialReport",
    "OOSInvestigation",
    "QCRun",
    "Reagent",
    "ReagentBatch",
    "Receipt",
    "ReceiptDecision",
    "ReceiptItem",
    "RefreshToken",
    "SampleDisposalRecord",
    "SampleRetention",
    "SampleStorageMovement",
    "ServiceClient",
    "Solicitation",
    "SolicitationItem",
    "StorageLocation",
    "TestAttachment",
    "TestExecution",
    "TestExecutionReagentUsage",
    "TestMethod",
    "TestReview",
    "TrainingRecord",
    "UncertaintyBudget",
    "User",
    "WebhookDelivery",
    "WebhookSubscription",
]
