"""Enums de domínio compartilhados entre modelos, schemas e front-end.

Os valores são strings estáveis (nunca renomear sem migração), pois são
persistidos no banco e usados nos filtros da trilha de auditoria.
"""

from __future__ import annotations

from enum import Enum


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    FISCAL = "FISCAL"              # fiscal sanitário / inspetor
    TECNICO = "TECNICO"            # técnico de laboratório
    CUSTODIANTE = "CUSTODIANTE"    # responsável pela guarda física
    AUDITOR = "AUDITOR"            # auditor da qualidade (somente leitura)


class SampleStatus(str, Enum):
    RECEBIDO = "RECEBIDO"
    EM_TESTE = "EM_TESTE"
    REPROVADO = "REPROVADO"
    APROVADO = "APROVADO"
    DESCARTADO = "DESCARTADO"


class TestStatus(str, Enum):
    PENDENTE = "PENDENTE"
    CONCLUIDO = "CONCLUIDO"


class TestOutcome(str, Enum):
    APROVADO = "APROVADO"
    REPROVADO = "REPROVADO"
    INCONCLUSIVO = "INCONCLUSIVO"


class CapaStatus(str, Enum):
    ABERTA = "ABERTA"
    EM_ANDAMENTO = "EM_ANDAMENTO"
    CONCLUIDA = "CONCLUIDA"
    CANCELADA = "CANCELADA"


class AuditAction(str, Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    TRANSFER = "TRANSFER"
    STATUS_CHANGE = "STATUS_CHANGE"
    SIGN = "SIGN"
    LOGIN = "LOGIN"
    LOGIN_FAILED = "LOGIN_FAILED"
    LOGOUT = "LOGOUT"
    REFRESH = "REFRESH"
    SIGNATURE_ISSUED = "SIGNATURE_ISSUED"
    SIGNATURE_REJECTED = "SIGNATURE_REJECTED"
    CAPA_AUTO_OPEN = "CAPA_AUTO_OPEN"
    INTEGRITY_CHECK = "INTEGRITY_CHECK"


class SignatureMeaning(str, Enum):
    """Significado da assinatura — exibido no manifesto (Part 11 §11.50)."""

    AUTORIA = "AUTORIA"
    REVISAO = "REVISAO"
    APROVACAO = "APROVACAO"
    RESPONSABILIDADE_TECNICA = "RESPONSABILIDADE_TECNICA"
    TRANSFERENCIA_DE_CUSTODIA = "TRANSFERENCIA_DE_CUSTODIA"
    VERIFICACAO = "VERIFICACAO"


class SignatureAction(str, Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    TRANSFER = "TRANSFER"
    CLOSE = "CLOSE"


class AuditEntity(str, Enum):
    DEVICE_SAMPLE = "DeviceSample"
    CHAIN_OF_CUSTODY = "ChainOfCustody"
    LAB_TEST = "LabTest"
    CAPA_ACTION = "CapaAction"
    USER = "User"
    ELECTRONIC_SIGNATURE = "ElectronicSignature"
    AUDIT_LOG = "AuditLog"
