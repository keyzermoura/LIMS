export type UserRole = "ADMIN" | "FISCAL" | "TECNICO" | "CUSTODIANTE" | "AUDITOR";

export type SampleStatus =
  | "RECEBIDO"
  | "EM_TESTE"
  | "APROVADO"
  | "REPROVADO"
  | "DESCARTADO";

export type TestStatus = "PENDENTE" | "CONCLUIDO";
export type TestOutcome = "APROVADO" | "REPROVADO" | "INCONCLUSIVO";
export type CapaStatus = "ABERTA" | "EM_ANDAMENTO" | "CONCLUIDA" | "CANCELADA";
export type CapaSourceType =
  | "ENSAIO_REPROVADO"
  | "INCERTEZA_METROLOGICA"
  | "EQUIPAMENTO_DESVIO"
  | "AUDITORIA_INTERNA"
  | "RECLAMACAO_CLIENTE"
  | "CONTROLE_QUALIDADE"
  | "OUTRO";
export type CapaActionType = "CONTENCAO" | "CORRETIVA" | "PREVENTIVA";
export type CapaItemStatus = "PENDENTE" | "EM_ANDAMENTO" | "CONCLUIDA" | "CANCELADA";
export type CapaEffectivenessStatus = "PENDENTE" | "EFICAZ" | "INEFICAZ";

export interface IshikawaCauses {
  metodo?: string[];
  maquina?: string[];
  material?: string[];
  mao_de_obra?: string[];
  meio_ambiente?: string[];
  medicao?: string[];
}

export interface FiveWhysItem {
  why_number: number;
  question: string;
  answer: string;
}

export interface CapaActionItem {
  id: string;
  capa_id: string;
  title: string;
  description: string;
  action_type: CapaActionType;
  assigned_to: UserBrief;
  due_date: string;
  status: CapaItemStatus;
  completed_at: string | null;
  completion_evidence: string | null;
  created_at: string;
  updated_at: string;
}

export type SignatureMeaning =
  | "AUTORIA"
  | "REVISAO"
  | "APROVACAO"
  | "RESPONSABILIDADE_TECNICA"
  | "TRANSFERENCIA_DE_CUSTODIA"
  | "VERIFICACAO";

export type SignatureAction = "CREATE" | "UPDATE" | "TRANSFER" | "CLOSE";

export interface UserBrief {
  id: string;
  username: string;
  full_name: string;
  role: UserRole;
  registration_number: string | null;
}

export interface Me extends UserBrief {
  email: string;
  is_active: boolean;
  last_login_at: string | null;
  mfa_enabled: boolean;
  created_at: string;
  permissions: string[];
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user?: Me;
  mfa_required?: boolean;
  mfa_token?: string;
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface DeviceSample {
  id: string;
  accession_number: string;
  serial_number: string;
  lot_number: string;
  manufacturer: string;
  commercial_name: string;
  model: string | null;
  registration_number: string | null;
  description: string | null;
  status: SampleStatus;
  received_at: string;
  received_by_id: string;
  current_custodian: UserBrief | null;
  current_location: string | null;
  attributes: Record<string, unknown>;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface TimelineEvent {
  id: string;
  type:
    | "RECEIPT"
    | "CUSTODY"
    | "TEST_CREATED"
    | "TEST_SIGNED"
    | "CAPA_OPENED"
    | "STATUS_CHANGE";
  occurred_at: string;
  title: string;
  description: string | null;
  actor_name: string | null;
  location: string | null;
  metadata: Record<string, unknown>;
}

export interface CustodyEvent {
  id: string;
  device_sample_id: string;
  from_custodian: UserBrief | null;
  to_custodian: UserBrief;
  transferred_at: string;
  reason: string;
  location_from: string | null;
  location_to: string;
  seal_number: string | null;
  notes: string | null;
  signature_id: string | null;
}

export interface LabTest {
  id: string;
  device_sample_id: string;
  name: string;
  method: string | null;
  method_id?: string | null;
  equipment_id?: string | null;
  parameters: Record<string, unknown>;
  unit: string;
  lower_limit: string | null;
  upper_limit: string | null;
  acceptance_criteria: string | null;
  result_value: string | null;
  result_text: string | null;
  outcome: TestOutcome | null;
  notes: string | null;
  status: TestStatus;
  review_status?: CoordinationReviewStatus | null;
  assigned_to_id: string | null;
  tested_by: UserBrief | null;
  tested_at: string | null;
  signed_at: string | null;
  signed_by: UserBrief | null;
  signature_id: string | null;
  result_version: number;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface LabTestResultVersion {
  id: string;
  version: number;
  result_value: string | null;
  result_text: string | null;
  unit: string;
  outcome: TestOutcome;
  notes: string | null;
  is_amendment: boolean;
  amendment_reason: string | null;
  signed_by: UserBrief;
  signed_at: string;
  signature_id: string;
}

export interface TestAlert {
  code: string;
  severity: string;
  message: string;
  capa_id: string | null;
  capa_code: string | null;
  capa_required: boolean;
}

export interface TestResultResponse {
  test: LabTest;
  result_version: LabTestResultVersion;
  alert: TestAlert | null;
  capa_id: string | null;
  audit_log_id: number;
  signature_id: string;
  signature_manifest_hash: string;
}

export interface Capa {
  id: string;
  code: string;
  device_sample_id: string | null;
  lab_test_id: string | null;
  source_type: CapaSourceType;
  title: string;
  containment_action: string | null;
  ishikawa_causes: IshikawaCauses | null;
  five_whys: FiveWhysItem[] | null;
  root_cause: string;
  action_plan: string;
  owner: UserBrief;
  status: CapaStatus;
  due_date: string;
  opened_at: string;
  closed_at: string | null;
  auto_opened: boolean;
  created_by_id: string;
  effectiveness_check: string | null;
  target_effectiveness_date: string | null;
  effectiveness_status: CapaEffectivenessStatus;
  effectiveness_evaluator: UserBrief | null;
  effectiveness_evaluated_at: string | null;
  recurrence_detected: boolean;
  effective: boolean | null;
  action_items: CapaActionItem[];
  version: number;
  created_at: string;
  updated_at: string;
}

export interface CapaCreateResponse {
  capa: Capa;
  audit_log_id: number;
  signature_id: string;
}

export type AuditAction =
  | "CREATE"
  | "UPDATE"
  | "DELETE"
  | "TRANSFER"
  | "STATUS_CHANGE"
  | "SIGN"
  | "LOGIN"
  | "LOGIN_FAILED"
  | "LOGOUT"
  | "REFRESH"
  | "SIGNATURE_ISSUED"
  | "SIGNATURE_REJECTED"
  | "CAPA_AUTO_OPEN"
  | "INTEGRITY_CHECK"
  | "EXPORT"
  | "EXPORT_VERIFIED";

export interface AuditLogEntry {
  id: number;
  sequence: number;
  occurred_at: string;
  actor_id: string | null;
  actor_username: string;
  actor_role: string | null;
  action: AuditAction;
  entity_type: string;
  entity_id: string;
  old_value: Record<string, unknown> | null;
  new_value: Record<string, unknown> | null;
  reason: string | null;
  ip_address: string | null;
  user_agent: string | null;
  request_id: string | null;
  signature_id: string | null;
  prev_hash: string;
  hash: string;
  hmac: string;
}

export interface AuditVerifyResult {
  ok: boolean;
  checked: number;
  total_records: number;
  from_sequence: number;
  last_sequence: number | null;
  head_hash: string | null;
  canonicalization: string;
  issues: Array<{ sequence: number; type: string; detail: string }>;
}

export type AuditExportFormat = "csv" | "json";

export interface AuditExportVerifyResult {
  ok: boolean;
  export_id: string | null;
  generated_at: string | null;
  generated_by: string | null;
  record_count: number;
  checked: number;
  first_sequence: number | null;
  last_sequence: number | null;
  head_hash: string | null;
  manifest_hash: string | null;
  manifest_hash_ok: boolean;
  manifest_hmac_ok: boolean;
  data_hash_ok: boolean;
  data_hmac_ok: boolean;
  files_ok: boolean;
  chain_ok: boolean;
  chain_contiguous: boolean;
  chain_gaps: number;
  matches_database: boolean;
  canonicalization: string | null;
  issues: Array<{ sequence: number; type: string; detail: string }>;
}

export interface ESignatureGrant {
  token: string;
  signature_id: string;
  expires_at: string;
  manifest: Record<string, unknown>;
  manifest_hash: string;
}

export interface AppMetadata {
  project: string;
  esignature_ttl_seconds: number;
  session_idle_timeout_minutes: number;
  access_token_expire_minutes: number;
  auto_open_capa_on_failure: boolean;
  password_min_length: number;
}

// ==========================================
// Fase 1: Solicitação, Recebimento e Custódia
// ==========================================

export type SolicitationStatus = "DRAFT" | "SUBMITTED" | "CANCELLED";

export type PresentationStatus = "PRESENTED" | "ABSENT" | "DAMAGED";

export type ConferenceStatus =
  | "PENDENTE"
  | "CONFORME"
  | "COM_RESSALVA"
  | "NAO_CONFORME";

export type CustodyObjectStatus =
  | "AGUARDANDO_RECEBIMENTO"
  | "RECEBIDO_INTEGRO"
  | "RECEBIDO_AVARIADO"
  | "RETIDO"
  | "TRANSFERIDO"
  | "ACEITO"
  | "REJEITADO";

export type ReceiptStatus =
  | "DRAFT"
  | "EM_CONFERENCIA"
  | "CONCLUIDO"
  | "CANCELADO";

export type CustodyEventType =
  | "RECEIPT"
  | "TRANSFER"
  | "ACCEPTANCE"
  | "REJECTION"
  | "SEAL_CHANGE"
  | "INSPECTION";

export type CriterionClass = "ELIMINATORIO" | "SANEAVEL" | "INFORMATIVO";

export type ChecklistResult = "CONFORME" | "NAO_CONFORME" | "NAO_APLICA";

export type ReceiptDecisionEnum = "ACCEPTED" | "PENDING" | "REJECTED";

export type CoordinationReviewStatus =
  | "PENDENTE"
  | "APROVADO"
  | "DEVOLVIDO"
  | "REJEITADO";

export interface SolicitationItem {
  id: string;
  solicitation_id: string;
  item_number: number;
  product_name: string;
  category: string | null;
  manufacturer: string | null;
  model: string | null;
  serial_number: string | null;
  lot_number: string | null;
  declared_quantity: number;
  unit_of_measure: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface Solicitation {
  id: string;
  solicitation_number: string;
  requester_name: string;
  requester_email: string | null;
  requester_document: string | null;
  requester_organization: string | null;
  created_by_id: string;
  created_by: UserBrief | null;
  purpose: string | null;
  request_type: string;
  priority: string;
  status: SolicitationStatus;
  submitted_at: string | null;
  items: SolicitationItem[];
  has_receipt: boolean;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface CustodyEventBrief {
  id: string;
  custody_object_id: string;
  event_type: CustodyEventType;
  effective_at: string;
  from_custodian_id: string | null;
  from_custodian: UserBrief | null;
  to_custodian_id: string | null;
  to_custodian: UserBrief | null;
  from_location: string | null;
  to_location: string | null;
  reason: string;
  registered_by_id: string;
  registered_by: UserBrief | null;
  created_at: string;
}

export interface CustodyObject {
  id: string;
  receipt_item_id: string;
  object_code: string;
  grouping_description: string | null;
  represented_quantity: number;
  current_location: string | null;
  seal_number: string | null;
  status: CustodyObjectStatus;
  current_custodian_id: string | null;
  current_custodian: UserBrief | null;
  linked_device_sample_id: string | null;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface ReceiptItem {
  id: string;
  receipt_id: string;
  solicitation_item_id: string;
  solicitation_item: SolicitationItem | null;
  presentation_status: PresentationStatus;
  presented_quantity: number;
  conference_status: ConferenceStatus;
  decision: ReceiptDecisionEnum | null;
  notes: string | null;
  custody_objects: CustodyObject[];
  version: number;
  created_at: string;
  updated_at: string;
}

export interface Receipt {
  id: string;
  solicitation_id: string;
  receipt_number: string;
  arrived_at: string;
  received_by_id: string;
  received_by: UserBrief | null;
  arrival_location: string | null;
  external_protocol: string | null;
  delivery_method: string | null;
  packaging_condition: string | null;
  notes: string | null;
  status: ReceiptStatus;
  items: ReceiptItem[];
  version: number;
  created_at: string;
  updated_at: string;
}

export interface ChecklistCriterion {
  id: string;
  template_id: string;
  code: string;
  description: string;
  criterion_class: CriterionClass;
  is_mandatory: boolean;
  order: number;
  created_at: string;
  updated_at: string;
}

export interface ChecklistTemplate {
  id: string;
  code: string;
  name: string;
  category: string | null;
  version: number;
  is_active: boolean;
  criteria: ChecklistCriterion[];
  created_at: string;
  updated_at: string;
}

export interface ChecklistAnswer {
  id: string;
  receipt_item_id: string;
  criterion_id: string;
  criterion: ChecklistCriterion | null;
  result: ChecklistResult;
  justification: string | null;
  evaluated_by_id: string;
  evaluated_by: UserBrief | null;
  created_at: string;
  updated_at: string;
}

export interface DecisionBrief {
  id: string;
  decision: ReceiptDecisionEnum;
  justification: string;
  decided_by: UserBrief | null;
  created_at: string;
}

export interface CoordinationReview {
  id: string;
  decision_id: string;
  decision?: DecisionBrief | null;
  status: CoordinationReviewStatus;
  reviewed_by_id: string | null;
  reviewed_by: UserBrief | null;
  reviewed_at: string | null;
  review_notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface ReceiptDecision {
  id: string;
  receipt_item_id: string;
  custody_object_id: string | null;
  decision: ReceiptDecisionEnum;
  justification: string;
  decided_by_id: string;
  decided_by: UserBrief | null;
  requires_coordination_review: boolean;
  coordination_review: CoordinationReview | null;
  version: number;
  created_at: string;
  updated_at: string;
}

// ============================================================================
// Fase 2: Métodos de Ensaio, Equipamentos Metrológicos e Execuções de Bancada
// ============================================================================

export type EquipmentCalibrationStatus =
  | "CALIBRADO"
  | "VENCIDO"
  | "EM_MANUTENCAO"
  | "NAO_APLICAVEL";

export type ExecutionStatus =
  | "EM_ANDAMENTO"
  | "CONCLUIDA"
  | "INTERROMPIDA"
  | "CANCELADA";

export interface LaboratoryEquipment {
  id: string;
  code: string;
  name: string;
  equipment_type: string | null;
  manufacturer: string | null;
  model: string | null;
  serial_number: string | null;
  location: string | null;
  calibration_status: EquipmentCalibrationStatus;
  last_calibration_at: string | null;
  calibration_due_date: string | null;
  certificate_number: string | null;
  calibration_agency: string | null;
  notes: string | null;
  is_active: boolean;
  is_calibration_valid: boolean;
  created_at: string;
  updated_at: string;
}

export interface EquipmentCreatePayload {
  code: string;
  name: string;
  equipment_type?: string | null;
  manufacturer?: string | null;
  model?: string | null;
  serial_number?: string | null;
  location?: string | null;
  calibration_status?: EquipmentCalibrationStatus;
  last_calibration_at?: string | null;
  calibration_due_date?: string | null;
  certificate_number?: string | null;
  calibration_agency?: string | null;
  notes?: string | null;
  is_active?: boolean;
}

export interface EquipmentCalibrationPayload {
  last_calibration_at: string;
  calibration_due_date: string;
  certificate_number: string;
  calibration_agency: string;
  calibration_status?: EquipmentCalibrationStatus;
  notes?: string | null;
}

export interface TestMethod {
  id: string;
  code: string;
  name: string;
  standard: string;
  version: number;
  category: string | null;
  description: string | null;
  parameters_schema: Record<string, unknown>;
  default_unit: string;
  default_lower_limit: number | string | null;
  default_upper_limit: number | string | null;
  default_acceptance_criteria: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface TestMethodCreatePayload {
  code: string;
  name: string;
  standard: string;
  category?: string | null;
  description?: string | null;
  default_unit?: string;
  default_lower_limit?: number | string | null;
  default_upper_limit?: number | string | null;
  default_acceptance_criteria?: string | null;
  parameters_schema?: Record<string, unknown>;
  is_active?: boolean;
}

export interface TestExecution {
  id: string;
  lab_test_id: string;
  execution_number: number;
  attempt_label: string;
  status: ExecutionStatus;
  equipment_id: string | null;
  equipment?: LaboratoryEquipment | null;
  executed_by_id: string | null;
  executed_by: UserBrief | null;
  started_at: string;
  finished_at: string | null;
  temperature_celsius: number | string | null;
  humidity_percent: number | string | null;
  pressure_hpa: number | string | null;
  raw_data: Record<string, unknown>;
  result_value: number | string | null;
  result_text: string | null;
  outcome: TestOutcome | null;
  interruption_reason: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface TestExecutionStartPayload {
  equipment_id?: string | null;
  temperature_celsius?: number | null;
  humidity_percent?: number | null;
  pressure_hpa?: number | null;
  notes?: string | null;
}

export interface TestExecutionRecordDataPayload {
  raw_data?: Record<string, unknown>;
  temperature_celsius?: number | null;
  humidity_percent?: number | null;
  pressure_hpa?: number | null;
  result_value?: number | null;
  result_text?: string | null;
  notes?: string | null;
}

export interface TestExecutionCompletePayload {
  raw_data: Record<string, unknown>;
  result_value?: number | null;
  result_text?: string | null;
  outcome: TestOutcome;
  temperature_celsius?: number | null;
  humidity_percent?: number | null;
  pressure_hpa?: number | null;
  notes?: string | null;
}

export interface TestExecutionInterruptPayload {
  reason: string;
}

// =============================================================================
// FASE 3: Revisão por Pares, Laudos Periciais e Evidências (M3)
// =============================================================================

export interface TestReview {
  id: string;
  lab_test_id: string;
  review_number: number;
  reviewed_by_id: string;
  reviewed_by: UserBrief | null;
  status: CoordinationReviewStatus;
  justification: string | null;
  notes: string | null;
  signature_id: string | null;
  reviewed_at: string;
  created_at: string;
}

export interface TestSubmitReviewPayload {
  notes?: string | null;
}

export interface TestReviewDecisionPayload {
  status: CoordinationReviewStatus;
  justification?: string | null;
  notes?: string | null;
  findings?: Record<string, unknown>;
}

export interface OfficialReport {
  id: string;
  report_number: string;
  device_sample_id: string;
  title: string;
  conclusion: TestOutcome;
  summary: string | null;
  sha256_hash: string;
  auth_token: string;
  version: number;
  root_report_id?: string | null;
  supersedes_id?: string | null;
  is_latest: boolean;
  amendment_reason?: string | null;
  issued_by_id: string;
  issued_by: UserBrief | null;
  signature_id: string;
  issued_at: string;
  created_at: string;
}

export interface OfficialReportGeneratePayload {
  device_sample_id: string;
  test_ids: string[];
  title?: string;
  conclusion?: TestOutcome;
  summary?: string | null;
  observations?: string | null;
}

export interface OfficialReportAmendPayload {
  amendment_reason: string;
  title?: string;
  conclusion?: TestOutcome;
  summary?: string | null;
}

export interface OfficialReportHistoryItem {
  version: number;
  report_number: string;
  is_latest: boolean;
  amendment_reason?: string | null;
  issued_at: string;
  sha256_hash: string;
}

export interface OfficialReportPublicVerify {
  is_valid: boolean;
  report_number: string;
  version: number;
  is_latest: boolean;
  amendment_reason?: string | null;
  supersedes_number?: string | null;
  latest_report_number?: string | null;
  sample_acc_number: string;
  sample_commercial_name: string;
  sample_serial_number: string | null;
  sample_lot_number: string | null;
  conclusion: TestOutcome;
  sha256_hash: string;
  issued_by_name: string;
  issued_at: string;
  history?: OfficialReportHistoryItem[];
}

export interface TestAttachment {
  id: string;
  lab_test_id: string;
  filename: string;
  content_type: string;
  file_size: number;
  sha256_hash: string;
  description: string | null;
  uploaded_by_id: string;
  uploaded_by: UserBrief | null;
  created_at: string;
}

export type QualificationStatus =
  | "QUALIFICADO"
  | "EM_SUPERVISAO"
  | "SUSPENSO"
  | "EXPIRADO";

export interface TrainingRecord {
  id: string;
  user_id: string;
  qualification_id?: string | null;
  title: string;
  provider?: string | null;
  completed_at: string;
  hours: number;
  certificate_code?: string | null;
  notes?: string | null;
  created_at: string;
}

export interface AnalystQualification {
  id: string;
  user_id: string;
  method_id: string;
  status: QualificationStatus;
  granted_at: string;
  expires_at: string | null;
  authorized_by_id: string;
  signature_id: string | null;
  scope: string | null;
  notes: string | null;
  is_active: boolean;
  version: number;
  created_at: string;
  user_name?: string | null;
  method_code?: string | null;
  method_name?: string | null;
  trainings: TrainingRecord[];
}

export interface QualificationCheck {
  is_qualified: boolean;
  status?: QualificationStatus | null;
  user_id: string;
  method_id: string;
  user_name: string;
  method_code: string;
  reason?: string | null;
}

// =============================================================================
// FASE 4 - Sprint 4.2: Incerteza de Medição GUM & Regras de Decisão ILAC-G8
// =============================================================================

export type UncertaintySourceType = "TYPE_A" | "TYPE_B";

export type UncertaintyDistribution =
  | "NORMAL"
  | "RECTANGULAR"
  | "TRIANGULAR"
  | "U_SHAPED";

export type DecisionRuleType =
  | "SIMPLE_ACCEPTANCE"
  | "GUARD_BAND_CONSERVATIVE"
  | "GUARD_BAND_NON_BINARY";

export type ConformityStatus =
  | "CONFORME"
  | "CONFORME_CONDICIONAL"
  | "NAO_CONFORME_CONDICIONAL"
  | "NAO_CONFORME";

export interface UncertaintyComponentIn {
  name: string;
  symbol?: string | null;
  source_type: UncertaintySourceType;
  distribution: UncertaintyDistribution;
  half_width: number;
  divisor?: number | null;
  sensitivity_coefficient?: number;
  degrees_of_freedom?: number | null;
}

export interface UncertaintyComponentOut {
  name: string;
  symbol?: string | null;
  source_type: UncertaintySourceType;
  distribution: UncertaintyDistribution;
  half_width: number | string;
  divisor: number | string;
  sensitivity_coefficient: number | string;
  degrees_of_freedom?: number | null;
  standard_uncertainty: number | string;
  combined_contribution: number | string;
  weight_percent: number | string;
}

export interface UncertaintySimulatePayload {
  unit: string;
  measured_value?: number | null;
  repeatability_readings: number[];
  lower_limit?: number | null;
  upper_limit?: number | null;
  components: UncertaintyComponentIn[];
  coverage_factor?: number | null;
  confidence_level?: number;
  guard_band_multiplier?: number;
  decision_rule: DecisionRuleType;
}

export interface UncertaintyBudgetCreatePayload extends UncertaintySimulatePayload {
  method_id?: string | null;
  lab_test_id?: string | null;
  execution_id?: string | null;
  equipment_id?: string | null;
  notes?: string | null;
}

export interface UncertaintyCalculation {
  unit: string;
  measured_value: number | string;
  lower_limit: number | string | null;
  upper_limit: number | string | null;
  lower_acceptance_limit: number | string | null;
  upper_acceptance_limit: number | string | null;
  repeatability_mean: number | string | null;
  repeatability_std_dev: number | string | null;
  repeatability_count: number;
  components: UncertaintyComponentOut[];
  combined_uncertainty: number | string;
  effective_df: number | string | null;
  coverage_factor: number | string;
  confidence_level: number | string;
  expanded_uncertainty: number | string;
  guard_band_multiplier: number | string;
  guard_band_width: number | string;
  decision_rule: DecisionRuleType;
  conformity_status: ConformityStatus;
  recommended_outcome: TestOutcome;
  conformity_statement: string;
  formatted_result: string;
}

export interface UncertaintyBudget extends UncertaintyCalculation {
  id: string;
  method_id: string | null;
  lab_test_id: string | null;
  execution_id: string | null;
  equipment_id: string | null;
  repeatability_readings: Array<number | string>;
  calculated_by_id: string;
  calculated_by_name?: string | null;
  method_code?: string | null;
  test_name?: string | null;
  equipment_code?: string | null;
  signature_id: string | null;
  notes: string | null;
  version: number;
  created_at: string;
}

// ---------------------------------------------------------------------------
// BI e Controle Metrológico (Fase 5 / Sprint 5.1)
// ---------------------------------------------------------------------------

export interface TurnaroundTimeMetrics {
  global_avg_hours: number | null;
  receipt_to_testing_avg_hours: number | null;
  testing_to_review_avg_hours: number | null;
  review_to_report_avg_hours: number | null;
  samples_measured_count: number;
  data_quality?: string;
}

export interface SampleBacklogMetrics {
  age_0_to_5_days: number;
  age_6_to_15_days: number;
  age_above_15_days: number;
  total_active: number;
}

export interface TestConformityMetrics {
  total_tests: number;
  conforming_count: number;
  non_conforming_count: number;
  inconclusive_count: number;
  pending_count: number;
  conformity_rate_pct: number | null;
  data_quality?: string;
}

export interface CapaMetrics {
  total_capas: number;
  open_capas: number;
  closed_capas: number;
  effective_capas: number;
  ineffective_capas: number;
  effectiveness_rate_pct: number | null;
  data_quality?: string;
}

export interface AnalystWorkloadItem {
  user_id: string;
  full_name: string;
  active_tests_count: number;
  completed_tests_count: number;
}

export interface OperationalAnalytics {
  turnaround_time: TurnaroundTimeMetrics;
  sample_backlog: SampleBacklogMetrics;
  test_conformity: TestConformityMetrics;
  capa_metrics: CapaMetrics;
  analysts_workload: AnalystWorkloadItem[];
  equipment_status_summary: Record<string, number>;
}

export interface QualityControlPoint {
  run_number: number;
  measured_at: string;
  value: number;
  operator_name: string;
  violation?: string | null;
}

export interface WestgardViolation {
  rule_code: string;
  description: string;
  run_numbers: number[];
  severity: "WARNING" | "ALARM";
}

export interface QualityControlAnalytics {
  method_id?: string | null;
  method_name: string;
  parameter_name: string;
  unit: string;
  mean: number | null;
  standard_deviation: number | null;
  warning_limit_upper: number | null;
  warning_limit_lower: number | null;
  action_limit_upper: number | null;
  action_limit_lower: number | null;
  data_points: QualityControlPoint[];
  violations: WestgardViolation[];
  data_quality?: string;
}

// ---------------------------------------------------------------------------
// Notificações e Alertas em Tempo Real (Fase 5 / Sprint 5.2)
// ---------------------------------------------------------------------------

export type NotificationSeverity = "INFO" | "WARNING" | "CRITICAL";

export type NotificationCategory =
  | "CALIBRATION"
  | "COMPETENCE"
  | "CAPA"
  | "TAT"
  | "SAMPLE_ISSUE"
  | "SYSTEM";

export interface NotificationItem {
  id: string;
  user_id: string | null;
  target_role: UserRole | null;
  title: string;
  message: string;
  severity: NotificationSeverity;
  category: NotificationCategory;
  link_url: string | null;
  is_read: boolean;
  read_at: string | null;
  created_at: string;
}

export interface NotificationSummary {
  unread_count: number;
  critical_count: number;
  warning_count: number;
  info_count: number;
}

export interface AlertCheckResult {
  alerts_generated: number;
  details: string[];
}

// ---------------------------------------------------------------------------
// Conectores e Aquisição de Instrumentos (Fase 5 / Sprint 5.3)
// ---------------------------------------------------------------------------

export type InstrumentFileFormat =
  | "BALANCA_ASCII"
  | "UV_VIS_CSV"
  | "CHROMATOGRAPHY_CSV"
  | "GENERIC_JSON";

export type InstrumentImportStatus = "IMPORTED" | "MAPPED" | "REJECTED";

export interface InstrumentDataImport {
  id: string;
  equipment_id: string;
  test_execution_id: string | null;
  imported_by_id: string;
  file_name: string;
  file_format: InstrumentFileFormat;
  raw_file_hash_sha256: string;
  raw_content?: string;
  parsed_data: Record<string, any>;
  status: InstrumentImportStatus;
  rejection_reason: string | null;
  mapped_at: string | null;
  created_at: string;
}

export interface InstrumentDataSummary {
  total_imports: number;
  mapped_imports: number;
  unmapped_imports: number;
}

// ---------------------------------------------------------------------------
// Webhooks e Interoperabilidade (Fase 5 / Sprint 5.4)
// ---------------------------------------------------------------------------

export interface WebhookSubscription {
  id: string;
  url: string;
  description?: string | null;
  events: string[];
  is_active: boolean;
  created_by_id: string;
  created_at: string;
  updated_at: string;
}

export interface WebhookDelivery {
  id: string;
  subscription_id: string;
  event: string;
  payload: Record<string, unknown>;
  status: string;
  status_code?: number | null;
  response_body?: string | null;
  attempt_count: number;
  delivered_at?: string | null;
  created_at: string;
}

export interface WebhookPingResponse {
  subscription_id: string;
  delivery_id: string;
  event: string;
  status: string;
  status_code?: number | null;
  signature_header: string;
}

// ---------------------------------------------------------------------------
// MFA TOTP e Segurança Reforçada (Horizonte 1 / Sprint 6.2 - 21 CFR Part 11)
// ---------------------------------------------------------------------------

export interface MfaSetupResponse {
  secret: string;
  otpauth_url: string;
  qr_code_base64: string;
}

export interface MfaEnableRequest {
  secret: string;
  code: string;
  password: string;
}

export interface MfaEnableResponse {
  recovery_codes: string[];
  message: string;
}

export interface MfaDisableRequest {
  password: string;
  code: string;
}

// ---------------------------------------------------------------------------
// Reagentes, Padrões Analíticos e Insumos (Horizonte 2 / Sprint 7.1 - ISO 17025 §6.4)
// ---------------------------------------------------------------------------

export type ReagentType =
  | "REAGENT"
  | "PRIMARY_STANDARD_CRM"
  | "SECONDARY_STANDARD"
  | "SOLVENT"
  | "INDICATOR";

export type ReagentBatchStatus =
  | "AVAILABLE"
  | "IN_USE"
  | "EXPIRED"
  | "DEPLETED"
  | "QUARANTINE";

export type ReagentGrade = "PA" | "HPLC" | "USP" | "ANALYTICAL";

export interface Reagent {
  id: string;
  code: string;
  name: string;
  chemical_formula?: string | null;
  cas_number?: string | null;
  reagent_type: ReagentType;
  grade: ReagentGrade;
  storage_temperature_min?: number | null;
  storage_temperature_max?: number | null;
  hazard_classification?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ReagentBatch {
  id: string;
  reagent_id: string;
  lot_number: string;
  manufacturer: string;
  catalog_number?: string | null;
  received_at: string;
  opened_at?: string | null;
  expiration_date: string;
  initial_quantity: number;
  current_quantity: number;
  unit: string;
  certificate_number?: string | null;
  uncertainty_value?: number | null;
  k_factor?: number | null;
  status: ReagentBatchStatus;
  is_expired: boolean;
  is_usable: boolean;
  notes?: string | null;
  reagent?: Reagent | null;
}

export interface ReagentCreatePayload {
  code: string;
  name: string;
  chemical_formula?: string;
  cas_number?: string;
  reagent_type: ReagentType;
  grade?: ReagentGrade;
  storage_temperature_min?: number;
  storage_temperature_max?: number;
  hazard_classification?: string;
}

export interface ReagentBatchCreatePayload {
  lot_number: string;
  manufacturer: string;
  catalog_number?: string;
  expiration_date: string;
  initial_quantity: number;
  unit?: string;
  certificate_number?: string;
  uncertainty_value?: number;
  k_factor?: number;
  notes?: string;
}

export interface ExecutionReagentUsagePayload {
  batch_id: string;
  quantity_used: number;
  unit: string;
  notes?: string;
}

export interface ExecutionReagentUsage {
  id: string;
  execution_id: string;
  batch_id: string;
  quantity_used: number;
  unit: string;
  consumed_at: string;
  recorded_by_id: string;
  batch?: ReagentBatch | null;
  recorded_by?: { id?: string; full_name?: string } | null;
}

// ============================================================================
// Fase 7 / Sprint 7.2: Desvios Analíticos OOS e OOT (ISO 17025 §7.10)
// ============================================================================

export type DeviationType = "OOS" | "OOT";

export type OOSInvestigationStatus =
  | "PHASE_I_PENDING"
  | "PHASE_I_COMPLETED"
  | "PHASE_II_REQUIRED"
  | "CONFIRMED_LAB_ERROR"
  | "CONFIRMED_PRODUCT_FAILURE"
  | "CLOSED";

export type OOSRootCauseCategory =
  | "EQUIPMENT_MALFUNCTION"
  | "REAGENT_CONTAMINATION"
  | "OPERATOR_ERROR"
  | "CALCULATION_ERROR"
  | "ENVIRONMENTAL_FLUCTUATION"
  | "SAMPLE_ANOMALY"
  | "METHOD_LIMITATION"
  | "OTHER";

export interface RetestResultItem {
  retest_number: number;
  analyst_name: string;
  result_value?: number | null;
  result_text?: string | null;
  retest_date: string;
  outcome: string;
  notes?: string | null;
}

export interface OOSInvestigation {
  id: string;
  investigation_number: string;
  lab_test_id: string;
  execution_id?: string | null;
  deviation_type: DeviationType;
  status: OOSInvestigationStatus;
  initial_result?: number | null;
  initial_result_text?: string | null;
  specification_min?: number | null;
  specification_max?: number | null;
  specification_text?: string | null;
  detected_by_id: string;
  detected_at: string;
  phase_1_checklist: {
    calculation_verified?: boolean;
    instrument_verified?: boolean;
    reagent_verified?: boolean;
    analyst_interviewed?: boolean;
    sample_integrity_verified?: boolean;
    checklist_notes?: string;
  };
  phase_1_conclusion?: string | null;
  phase_1_completed_at?: string | null;
  phase_1_responsible_id?: string | null;
  phase_2_required: boolean;
  phase_2_plan?: string | null;
  phase_2_retest_results: RetestResultItem[];
  root_cause_category?: OOSRootCauseCategory | null;
  root_cause_description?: string | null;
  capa_action_id?: string | null;
  final_disposition?: string | null;
  closed_at?: string | null;
  closed_by_id?: string | null;
  version: number;
  created_at: string;
  updated_at: string;

  detected_by?: { id: string; full_name: string; email: string } | null;
  phase_1_responsible?: { id: string; full_name: string; email: string } | null;
  closed_by?: { id: string; full_name: string; email: string } | null;
  lab_test?: {
    id: string;
    name: string;
    code?: string | null;
    unit?: string | null;
    device_sample_id: string;
  } | null;
}

export interface OOSInvestigationCreatePayload {
  lab_test_id: string;
  execution_id?: string;
  deviation_type?: DeviationType;
  initial_result?: number;
  initial_result_text?: string;
  specification_min?: number;
  specification_max?: number;
  specification_text?: string;
}

export interface OOSPhase1UpdatePayload {
  calculation_verified: boolean;
  instrument_verified: boolean;
  reagent_verified: boolean;
  analyst_interviewed: boolean;
  sample_integrity_verified: boolean;
  checklist_notes?: string;
  phase_1_conclusion: string;
  phase_2_required: boolean;
}

export interface OOSPhase2UpdatePayload {
  phase_2_plan: string;
  retest_results: RetestResultItem[];
  root_cause_category: OOSRootCauseCategory;
  root_cause_description: string;
  confirmed_status: "CONFIRMED_LAB_ERROR" | "CONFIRMED_PRODUCT_FAILURE";
  capa_action_id?: string;
  auto_create_capa?: boolean;
}

export interface OOSClosePayload {
  final_disposition: string;
}

// ============================================================================
// Fase 7 (Horizonte 2 — Sprint 7.3): Cadeia Física, Contraprova e Descarte (H2.3 & H2.4)
// ============================================================================

export type StorageLocationType =
  | "ULTRA_FREEZER"
  | "COLD_CHAMBER"
  | "REFRIGERATOR"
  | "CONTROLLED_ROOM"
  | "DESICCATOR"
  | "HAZARDOUS_CABINET";

export type RetentionType =
  | "CONTRAPROVA_PERICIAL"
  | "TESTEMUNHA_QUALIDADE"
  | "RETENCAO_REGULATORIA";

export type RetentionStatus =
  | "ACTIVE"
  | "EXTENDED"
  | "EXPIRED"
  | "DISPOSED";

export type DisposalMethod =
  | "INCINERACAO"
  | "AUTOCLAVAGEM"
  | "DESCARTE_QUIMICO_ESPECIALIZADO"
  | "DEVOLUCAO_ORGAO_REGULADOR"
  | "RECICLAGEM_CONTROLADA";

export interface StorageLocation {
  id: string;
  code: string;
  name: string;
  location_type: StorageLocationType;
  room: string;
  temperature_target_celsius: number;
  temperature_min_celsius: number;
  temperature_max_celsius: number;
  humidity_max_percent?: number | null;
  capacity_units: number;
  current_occupancy: number;
  is_active: boolean;
  metadata?: Record<string, any>;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface StorageLocationCreatePayload {
  code: string;
  name: string;
  location_type: StorageLocationType;
  room: string;
  temperature_target_celsius: number;
  temperature_min_celsius: number;
  temperature_max_celsius: number;
  humidity_max_percent?: number | null;
  capacity_units: number;
  metadata?: Record<string, any>;
}

export interface SampleStorageMovement {
  id: string;
  sample_id: string;
  from_location_id?: string | null;
  to_location_id: string;
  moved_by_id: string;
  moved_at: string;
  reason: string;
  temperature_at_movement?: number | null;
  notes?: string | null;
  from_location?: StorageLocation | null;
  to_location?: StorageLocation | null;
  moved_by?: { id: string; full_name: string; email: string } | null;
  sample?: {
    id: string;
    accession_number: string;
    commercial_name: string;
    manufacturer: string;
    lot_number?: string | null;
    serial_number?: string | null;
    status: string;
  } | null;
}

export interface SampleStorageMovementCreatePayload {
  sample_id: string;
  to_location_id: string;
  reason: string;
  temperature_at_movement?: number | null;
  notes?: string | null;
}

export interface SampleRetention {
  id: string;
  sample_id: string;
  storage_location_id: string;
  retention_type: RetentionType;
  retained_at: string;
  retain_until: string;
  quantity_retained: number;
  unit: string;
  seal_number: string;
  status: RetentionStatus;
  is_expired: boolean;
  responsible_id: string;
  notes?: string | null;
  version: number;
  created_at: string;
  updated_at: string;
  storage_location?: StorageLocation | null;
  responsible?: { id: string; full_name: string; email: string } | null;
  sample?: {
    id: string;
    accession_number: string;
    commercial_name: string;
    manufacturer: string;
    lot_number?: string | null;
    serial_number?: string | null;
    status: string;
  } | null;
}

export interface SampleRetentionCreatePayload {
  sample_id: string;
  storage_location_id: string;
  retention_type?: RetentionType;
  retain_until: string;
  quantity_retained: number;
  unit?: string;
  seal_number: string;
  notes?: string | null;
}

export interface SampleDisposalRecord {
  id: string;
  sample_id: string;
  retention_id?: string | null;
  disposal_manifest_number: string;
  disposal_method: DisposalMethod;
  disposed_at: string;
  disposed_by_id: string;
  witness_id: string;
  primary_signature_id: string;
  witness_signature_id: string;
  environmental_license_number?: string | null;
  waste_company_name?: string | null;
  notes?: string | null;
  version: number;
  created_at: string;
  sample?: {
    id: string;
    accession_number: string;
    commercial_name: string;
    manufacturer: string;
    lot_number?: string | null;
    serial_number?: string | null;
    status: string;
  } | null;
  disposed_by?: { id: string; full_name: string; email: string } | null;
  witness?: { id: string; full_name: string; email: string } | null;
}

export interface SampleDisposalCreatePayload {
  sample_id: string;
  disposal_method: DisposalMethod;
  primary_esign_token: string;
  witness_id: string;
  witness_esign_token: string;
  environmental_license_number?: string | null;
  waste_company_name?: string | null;
  notes?: string | null;
  force_legal_override?: boolean;
}

export interface StorageDashboardSummary {
  total_locations: number;
  active_locations: number;
  total_retentions: number;
  active_retentions: number;
  expired_retentions: number;
  total_disposals: number;
}

// ============================================================================
// Fase 7 (Horizonte 2 — Sprint 7.4): CEP Real e Regras de Westgard (H2.5)
// ============================================================================

export type QCStatus = "CONFORMING" | "WARNING" | "REJECTED";

export interface QCRun {
  id: string;
  code: string;
  method_id: string;
  equipment_id?: string | null;
  reagent_batch_id?: string | null;
  operator_id: string;
  run_at: string;
  target_mean: number;
  target_sd: number;
  measured_value: number;
  z_score: number;
  status: QCStatus;
  violation_rules: string[];
  is_active_violation: boolean;
  corrective_notes?: string | null;
  version: number;
  created_at: string;
  updated_at: string;
  method?: { id: string; code: string; name: string; category: string } | null;
  operator?: { id: string; full_name: string; email: string } | null;
}

export interface QCRunCreatePayload {
  method_id: string;
  equipment_id?: string;
  reagent_batch_id?: string;
  measured_value: number;
  target_mean: number;
  target_sd: number;
  notes?: string;
}

export interface QCRunResolvePayload {
  corrective_notes: string;
}

export interface LeveyJenningsChartData {
  method_id: string;
  method_name: string;
  target_mean: number;
  target_sd: number;
  plus_1s: number;
  minus_1s: number;
  plus_2s: number;
  minus_2s: number;
  plus_3s: number;
  minus_3s: number;
  points: {
    run_id: string;
    code: string;
    run_at: string;
    measured_value: number;
    z_score: number;
    status: QCStatus;
    violation_rules: string[];
    operator_name: string;
  }[];
  total_runs: number;
  active_rejections: number;
  active_warnings: number;
}

// ---------------------------------------------------------------------------
// Integrações M2M & Ecossistema (Horizonte 3 / Fase 8)
// ---------------------------------------------------------------------------

export interface ServiceClient {
  id: string;
  client_id: string;
  name: string;
  scopes: string[];
  service_user_id: string;
  is_active: boolean;
  expires_at: string;
  last_used_at: string | null;
  created_at: string;
  ip_allowlist?: string[] | null;
}

export interface ServiceClientCreatePayload {
  name: string;
  scopes: string[];
  expires_in_days: number;
  ip_allowlist?: string[];
  service_username?: string;
}

export interface ServiceClientCreated {
  id: string;
  client_id: string;
  client_secret: string;
  name: string;
  scopes: string[];
  expires_at: string;
  service_user_id: string;
}

export interface OutboxEvent {
  id: string;
  event_name: string;
  aggregate_type: string;
  aggregate_id: string;
  payload: Record<string, unknown>;
  delivery_id: string;
  status: "PENDING" | "DISPATCHED" | "DEAD_LETTER";
  retry_count: number;
  max_retries: number;
  last_error?: string | null;
  created_at: string;
  dispatched_at?: string | null;
}

export interface InstrumentProfile {
  profile_id: string;
  name: string;
  version: number;
  manufacturer: string;
  format: "csv" | "txt" | "astm" | "json";
  delimiter?: string;
  decimal_separator?: string;
  columns?: Record<string, string>;
  units?: Record<string, string>;
  description?: string;
}



