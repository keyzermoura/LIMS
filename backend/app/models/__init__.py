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
from app.models.instrument_data import InstrumentDataImport
from app.models.lab_test import LabTest, LabTestResult
from app.models.notification import Notification
from app.models.official_report import OfficialReport
from app.models.qualification import AnalystQualification, TrainingRecord
from app.models.receipt import CustodyEvent, CustodyObject, Receipt, ReceiptItem
from app.models.solicitation import Solicitation, SolicitationItem
from app.models.test_attachment import TestAttachment
from app.models.test_execution import TestExecution
from app.models.test_method import TestMethod
from app.models.test_review import TestReview
from app.models.uncertainty import UncertaintyBudget
from app.models.user import RefreshToken, User

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
    "InstrumentDataImport",
    "LabTest",
    "LabTestResult",
    "LaboratoryEquipment",
    "Notification",
    "OfficialReport",
    "Receipt",
    "ReceiptDecision",
    "ReceiptItem",
    "RefreshToken",
    "Solicitation",
    "SolicitationItem",
    "TestAttachment",
    "TestExecution",
    "TestMethod",
    "TestReview",
    "TrainingRecord",
    "UncertaintyBudget",
    "User",
]
