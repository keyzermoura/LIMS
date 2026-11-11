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
    EXPORT = "EXPORT"
    EXPORT_VERIFIED = "EXPORT_VERIFIED"


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
    SOLICITATION = "Solicitation"
    RECEIPT = "Receipt"
    CUSTODY_OBJECT = "CustodyObject"


class SolicitationStatus(str, Enum):
    RASCUNHO = "RASCUNHO"
    SUBMETIDA = "SUBMETIDA"
    RECEBIMENTO_REGISTRADO = "RECEBIMENTO_REGISTRADO"
    EM_TRATAMENTO = "EM_TRATAMENTO"
    CONCLUIDA = "CONCLUIDA"
    CANCELADA = "CANCELADA"


class ReceiptStatus(str, Enum):
    REGISTRADO = "REGISTRADO"
    EM_CONFERENCIA = "EM_CONFERENCIA"
    PENDENTE = "PENDENTE"
    CONCLUIDO = "CONCLUIDO"
    CANCELADO = "CANCELADO"


class PresentationStatus(str, Enum):
    PRESENTED = "PRESENTED"
    NOT_PRESENTED = "NOT_PRESENTED"


class ConferenceStatus(str, Enum):
    PENDENTE = "PENDENTE"
    CONFORME = "CONFORME"
    COM_RESSALVA = "COM_RESSALVA"
    NAO_CONFORME = "NAO_CONFORME"


class ReceiptDecisionEnum(str, Enum):
    ACCEPTED = "ACCEPTED"
    PENDING = "PENDING"
    REJECTED = "REJECTED"


class CustodyObjectStatus(str, Enum):
    SOB_GUARDA = "SOB_GUARDA"
    EM_CONFERENCIA = "EM_CONFERENCIA"
    ACEITO = "ACEITO"
    RECUSADO = "RECUSADO"
    DEVOLVIDO = "DEVOLVIDO"
    DESCARTADO = "DESCARTADO"


class CustodyEventType(str, Enum):
    INGRESSO = "INGRESSO"
    TRANSFERENCIA = "TRANSFERENCIA"
    MUDANCA_LOCAL = "MUDANCA_LOCAL"
    SAIDA = "SAIDA"
    ENCERRAMENTO = "ENCERRAMENTO"


class CriterionClass(str, Enum):
    ELIMINATORIO = "ELIMINATORIO"
    SANEAVEL = "SANEAVEL"
    INFORMATIVO = "INFORMATIVO"


class ChecklistResult(str, Enum):
    CONFORME = "CONFORME"
    NAO_CONFORME = "NAO_CONFORME"
    NAO_APLICAVEL = "NAO_APLICAVEL"


class CoordinationReviewStatus(str, Enum):
    PENDENTE = "PENDENTE"
    APROVADO = "APROVADO"
    DEVOLVIDO = "DEVOLVIDO"
    REJEITADO = "REJEITADO"
