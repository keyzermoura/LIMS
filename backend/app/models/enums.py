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


class QCStatus(str, Enum):
    CONFORMING = "CONFORMING"
    WARNING = "WARNING"
    REJECTED = "REJECTED"


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
    DATA_ACQUISITION = "DATA_ACQUISITION"


class SignatureMeaning(str, Enum):
    """Significado da assinatura — exibido no manifesto (Part 11 §11.50)."""

    AUTORIA = "AUTORIA"
    REVISAO = "REVISAO"
    APROVACAO = "APROVACAO"
    RESPONSABILIDADE_TECNICA = "RESPONSABILIDADE_TECNICA"
    TRANSFERENCIA_DE_CUSTODIA = "TRANSFERENCIA_DE_CUSTODIA"
    VERIFICACAO = "VERIFICACAO"
    EXECUCAO_DESCARTE = "EXECUCAO_DESCARTE"
    TESTEMUNHA_DESCARTE = "TESTEMUNHA_DESCARTE"


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
    CHECKLIST = "Checklist"
    RECEIPT_DECISION = "ReceiptDecision"
    COORDINATION_REVIEW = "CoordinationReview"
    TEST_METHOD = "TestMethod"
    LABORATORY_EQUIPMENT = "LaboratoryEquipment"
    TEST_EXECUTION = "TestExecution"
    TEST_REVIEW = "TestReview"
    OFFICIAL_REPORT = "OfficialReport"
    TEST_ATTACHMENT = "TestAttachment"
    ANALYST_QUALIFICATION = "AnalystQualification"
    TRAINING_RECORD = "TrainingRecord"
    UNCERTAINTY_BUDGET = "UncertaintyBudget"
    CAPA_ACTION_ITEM = "CapaActionItem"
    NOTIFICATION = "Notification"
    INSTRUMENT_DATA_IMPORT = "InstrumentDataImport"
    REAGENT = "Reagent"
    REAGENT_BATCH = "ReagentBatch"
    OOS_INVESTIGATION = "OOSInvestigation"
    STORAGE_LOCATION = "StorageLocation"
    STORAGE_MOVEMENT = "StorageMovement"
    SAMPLE_RETENTION = "SampleRetention"
    SAMPLE_DISPOSAL = "SampleDisposal"
    QC_RUN = "QCRun"


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


class EquipmentCalibrationStatus(str, Enum):
    CALIBRADO = "CALIBRADO"
    VENCIDO = "VENCIDO"
    EM_MANUTENCAO = "EM_MANUTENCAO"
    NAO_APLICAVEL = "NAO_APLICAVEL"


class ExecutionStatus(str, Enum):
    EM_ANDAMENTO = "EM_ANDAMENTO"
    CONCLUIDA = "CONCLUIDA"
    INTERROMPIDA = "INTERROMPIDA"
    CANCELADA = "CANCELADA"


class QualificationStatus(str, Enum):
    """Status de habilitação formal do analista para método analítico (ISO/IEC 17025 §6.2)."""

    QUALIFICADO = "QUALIFICADO"
    EM_SUPERVISAO = "EM_SUPERVISAO"
    SUSPENSO = "SUSPENSO"
    EXPIRADO = "EXPIRADO"


class UncertaintySourceType(str, Enum):
    """Classificação GUM das componentes de incerteza (JCGM 100:2008 §4)."""

    TYPE_A = "TYPE_A"
    TYPE_B = "TYPE_B"


class UncertaintyDistribution(str, Enum):
    """Distribuição de probabilidade associada à fonte de incerteza."""

    NORMAL = "NORMAL"
    RECTANGULAR = "RECTANGULAR"
    TRIANGULAR = "TRIANGULAR"
    U_SHAPED = "U_SHAPED"


class DecisionRuleType(str, Enum):
    """Regra de decisão metrológica para declaração de conformidade (ILAC-G8:09/2019)."""

    SIMPLE_ACCEPTANCE = "SIMPLE_ACCEPTANCE"
    GUARD_BAND_CONSERVATIVE = "GUARD_BAND_CONSERVATIVE"
    GUARD_BAND_NON_BINARY = "GUARD_BAND_NON_BINARY"


class ConformityStatus(str, Enum):
    """Status metrológico detalhado frente aos limites e faixa de guarda (ISO 17025 §7.8.6)."""

    CONFORME = "CONFORME"
    CONFORME_CONDICIONAL = "CONFORME_CONDICIONAL"
    NAO_CONFORME_CONDICIONAL = "NAO_CONFORME_CONDICIONAL"
    NAO_CONFORME = "NAO_CONFORME"


class CapaSourceType(str, Enum):
    """Origem da não conformidade ou desvio operacional (ISO/IEC 17025 §8.7)."""

    ENSAIO_REPROVADO = "ENSAIO_REPROVADO"
    INCERTEZA_METROLOGICA = "INCERTEZA_METROLOGICA"
    EQUIPAMENTO_DESVIO = "EQUIPAMENTO_DESVIO"
    AUDITORIA_INTERNA = "AUDITORIA_INTERNA"
    RECLAMACAO_CLIENTE = "RECLAMACAO_CLIENTE"
    CONTROLE_QUALIDADE = "CONTROLE_QUALIDADE"
    OUTRO = "OUTRO"


class CapaActionType(str, Enum):
    """Tipologia de ação no plano CAPA (ISO 17025 §8.7)."""

    CONTENCAO = "CONTENCAO"
    CORRETIVA = "CORRETIVA"
    PREVENTIVA = "PREVENTIVA"


class CapaItemStatus(str, Enum):
    """Status de execução de item do plano de ação CAPA."""

    PENDENTE = "PENDENTE"
    EM_ANDAMENTO = "EM_ANDAMENTO"
    CONCLUIDA = "CONCLUIDA"
    CANCELADA = "CANCELADA"


class CapaEffectivenessStatus(str, Enum):
    """Status formal da avaliação de eficácia temporal (ISO 17025 §8.7.3)."""

    PENDENTE = "PENDENTE"
    EFICAZ = "EFICAZ"
    INEFICAZ = "INEFICAZ"


class NotificationSeverity(str, Enum):
    """Severidade de notificações e alertas operacionais (Fase 5 / Sprint 5.2)."""

    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class NotificationCategory(str, Enum):
    """Categoria do evento gerador de alerta no laboratório."""

    CALIBRATION = "CALIBRATION"
    COMPETENCE = "COMPETENCE"
    CAPA = "CAPA"
    TAT = "TAT"
    SAMPLE_ISSUE = "SAMPLE_ISSUE"
    SYSTEM = "SYSTEM"


class InstrumentFileFormat(str, Enum):
    """Formatos de arquivos suportados pelos conectores de instrumentos (Sprint 5.3)."""

    BALANCA_ASCII = "BALANCA_ASCII"
    UV_VIS_CSV = "UV_VIS_CSV"
    CHROMATOGRAPHY_CSV = "CHROMATOGRAPHY_CSV"
    GENERIC_JSON = "GENERIC_JSON"


class InstrumentImportStatus(str, Enum):
    """Status do ciclo de vida da importação direta de instrumento (ALCOA+)."""

    IMPORTED = "IMPORTED"
    MAPPED = "MAPPED"
    REJECTED = "REJECTED"


# ---------------------------------------------------------------------------
# Reagentes, Padrões Analíticos e Insumos (Horizonte 2 / Sprint 7.1)
# ---------------------------------------------------------------------------


class ReagentType(str, Enum):
    """Tipologia de reagentes, padrões e consumíveis analíticos (ISO/IEC 17025 §6.4)."""

    REAGENT = "REAGENT"
    PRIMARY_STANDARD_CRM = "PRIMARY_STANDARD_CRM"
    SECONDARY_STANDARD = "SECONDARY_STANDARD"
    SOLVENT = "SOLVENT"
    INDICATOR = "INDICATOR"


class ReagentBatchStatus(str, Enum):
    """Ciclo de vida e disponibilidade de lote de reagente/padrão analítico."""

    AVAILABLE = "AVAILABLE"
    IN_USE = "IN_USE"
    EXPIRED = "EXPIRED"
    DEPLETED = "DEPLETED"
    QUARANTINE = "QUARANTINE"


class ReagentGrade(str, Enum):
    """Grau de pureza e qualidade técnica do reagente."""

    PA = "PA"
    HPLC = "HPLC"
    USP = "USP"
    ANALYTICAL = "ANALYTICAL"


class VolumeMassUnit(str, Enum):
    """Unidades físicas padronizadas para estoque e consumo de reagentes."""

    G = "g"
    MG = "mg"
    ML = "mL"
    L = "L"


# ---------------------------------------------------------------------------
# Desvios Analíticos OOS / OOT (Horizonte 2 / Sprint 7.2 - ISO 17025 §7.10)
# ---------------------------------------------------------------------------


class DeviationType(str, Enum):
    """Tipologia do desvio analítico detectado."""

    OOS = "OOS"
    OOT = "OOT"


class OOSInvestigationStatus(str, Enum):
    """Fases da investigação analítica segundo FDA Guidance e ISO/IEC 17025 §7.10."""

    PHASE_I_PENDING = "PHASE_I_PENDING"
    PHASE_I_COMPLETED = "PHASE_I_COMPLETED"
    PHASE_II_REQUIRED = "PHASE_II_REQUIRED"
    CONFIRMED_LAB_ERROR = "CONFIRMED_LAB_ERROR"
    CONFIRMED_PRODUCT_FAILURE = "CONFIRMED_PRODUCT_FAILURE"
    CLOSED = "CLOSED"


class OOSRootCauseCategory(str, Enum):
    """Categorias padronizadas de causa raiz para desvios analíticos."""

    EQUIPMENT_MALFUNCTION = "EQUIPMENT_MALFUNCTION"
    REAGENT_CONTAMINATION = "REAGENT_CONTAMINATION"
    OPERATOR_ERROR = "OPERATOR_ERROR"
    CALCULATION_ERROR = "CALCULATION_ERROR"
    ENVIRONMENTAL_FLUCTUATION = "ENVIRONMENTAL_FLUCTUATION"
    SAMPLE_ANOMALY = "SAMPLE_ANOMALY"
    METHOD_LIMITATION = "METHOD_LIMITATION"
    OTHER = "OTHER"


# ---------------------------------------------------------------------------
# Cadeia de Armazenamento, Contraprova e Descarte (Horizonte 2 / Sprint 7.3)
# ---------------------------------------------------------------------------


class StorageLocationType(str, Enum):
    """Tipologia de ambientes de conservação física com controle térmico."""

    ULTRA_FREEZER = "ULTRA_FREEZER"
    COLD_CHAMBER = "COLD_CHAMBER"
    REFRIGERATOR = "REFRIGERATOR"
    CONTROLLED_ROOM = "CONTROLLED_ROOM"
    DESICCATOR = "DESICCATOR"
    HAZARDOUS_CABINET = "HAZARDOUS_CABINET"


class RetentionType(str, Enum):
    """Classificação regulatória da guarda de contraprova pericial."""

    CONTRAPROVA_PERICIAL = "CONTRAPROVA_PERICIAL"
    TESTEMUNHA_QUALIDADE = "TESTEMUNHA_QUALIDADE"
    RETENCAO_REGULATORIA = "RETENCAO_REGULATORIA"


class RetentionStatus(str, Enum):
    """Estado do ciclo de vida da guarda de contraprova."""

    ACTIVE = "ACTIVE"
    EXTENDED = "EXTENDED"
    EXPIRED = "EXPIRED"
    DISPOSED = "DISPOSED"


class DisposalMethod(str, Enum):
    """Metodologia sanitária e ambiental de descarte irreversível."""

    INCINERACAO = "INCINERACAO"
    AUTOCLAVAGEM = "AUTOCLAVAGEM"
    DESCARTE_QUIMICO_ESPECIALIZADO = "DESCARTE_QUIMICO_ESPECIALIZADO"
    DEVOLUCAO_ORGAO_REGULADOR = "DEVOLUCAO_ORGAO_REGULADOR"
    RECICLAGEM_CONTROLADA = "RECICLAGEM_CONTROLADA"




