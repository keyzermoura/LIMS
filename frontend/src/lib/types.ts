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
