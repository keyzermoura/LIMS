"""Registro central dos modelos (necessário para o metadata do SQLAlchemy)."""

from app.models.audit_log import AuditLog
from app.models.base import Base
from app.models.capa_action import CapaAction
from app.models.chain_of_custody import ChainOfCustody
from app.models.device_sample import DeviceSample
from app.models.electronic_signature import ElectronicSignature
from app.models.lab_test import LabTest, LabTestResult
from app.models.user import RefreshToken, User

__all__ = [
    "AuditLog",
    "Base",
    "CapaAction",
    "ChainOfCustody",
    "DeviceSample",
    "ElectronicSignature",
    "LabTest",
    "LabTestResult",
    "RefreshToken",
    "User",
]
