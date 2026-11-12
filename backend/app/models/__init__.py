"""Registro central dos modelos (necessário para o metadata do SQLAlchemy)."""

from app.models.audit_log import AuditLog
from app.models.base import Base
from app.models.capa_action import CapaAction
from app.models.chain_of_custody import ChainOfCustody
from app.models.checklist import ChecklistAnswer, ChecklistCriterion, ChecklistTemplate
from app.models.decision import CoordinationReview, ReceiptDecision
from app.models.device_sample import DeviceSample
from app.models.electronic_signature import ElectronicSignature
from app.models.equipment import LaboratoryEquipment
from app.models.lab_test import LabTest, LabTestResult
from app.models.receipt import CustodyEvent, CustodyObject, Receipt, ReceiptItem
from app.models.solicitation import Solicitation, SolicitationItem
from app.models.test_execution import TestExecution
from app.models.test_method import TestMethod
from app.models.user import RefreshToken, User

__all__ = [
    "AuditLog",
    "Base",
    "CapaAction",
    "ChainOfCustody",
    "ChecklistAnswer",
    "ChecklistCriterion",
    "ChecklistTemplate",
    "CoordinationReview",
    "CustodyEvent",
    "CustodyObject",
    "DeviceSample",
    "ElectronicSignature",
    "LabTest",
    "LabTestResult",
    "LaboratoryEquipment",
    "Receipt",
    "ReceiptDecision",
    "ReceiptItem",
    "RefreshToken",
    "Solicitation",
    "SolicitationItem",
    "TestExecution",
    "TestMethod",
    "User",
]
