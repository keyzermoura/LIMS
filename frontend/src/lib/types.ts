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
  user: Me;
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
  title: string;
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
  effective: boolean | null;
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
