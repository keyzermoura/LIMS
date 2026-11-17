const API_BASE = import.meta.env.VITE_API_URL ?? "/api/v1";

const ACCESS_KEY = "lims.access";
const REFRESH_KEY = "lims.refresh";

export class ApiError extends Error {
  readonly status: number;
  readonly code?: string;
  readonly requestId?: string;
  readonly details?: unknown;

  constructor(
    message: string,
    status: number,
    code?: string,
    requestId?: string,
    details?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.requestId = requestId;
    this.details = details;
  }
}

export function getAccessToken(): string | null {
  return sessionStorage.getItem(ACCESS_KEY);
}

export function getRefreshToken(): string | null {
  return sessionStorage.getItem(REFRESH_KEY);
}

export function persistSession(accessToken: string, refreshToken: string): void {
  sessionStorage.setItem(ACCESS_KEY, accessToken);
  sessionStorage.setItem(REFRESH_KEY, refreshToken);
}

export function clearSession(): void {
  sessionStorage.removeItem(ACCESS_KEY);
  sessionStorage.removeItem(REFRESH_KEY);
}

export function hasStoredSession(): boolean {
  return Boolean(getAccessToken());
}

let refreshInFlight: Promise<boolean> | null = null;

async function refreshSession(): Promise<boolean> {
  if (!refreshInFlight) {
    refreshInFlight = (async () => {
      const refreshToken = getRefreshToken();
      if (!refreshToken) return false;
      try {
        const response = await fetch(`${API_BASE}/auth/refresh`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
        if (!response.ok) {
          clearSession();
          return false;
        }
        const data = (await response.json()) as {
          access_token: string;
          refresh_token: string;
          user: unknown;
        };
        persistSession(data.access_token, data.refresh_token);
        window.dispatchEvent(
          new CustomEvent("lims:session", { detail: data.user }),
        );
        return true;
      } catch {
        return false;
      }
    })().finally(() => {
      refreshInFlight = null;
    });
  }
  return refreshInFlight;
}

interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: unknown;
  form?: URLSearchParams;
  formData?: FormData;
  signatureToken?: string;
  retry?: boolean;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const {
    method = "GET",
    body,
    form,
    formData,
    signatureToken,
    retry = true,
  } = options;

  const headers: Record<string, string> = {};
  const accessToken = getAccessToken();
  if (accessToken) headers.Authorization = `Bearer ${accessToken}`;
  if (signatureToken) headers["X-Signature-Token"] = signatureToken;

  let payload: BodyInit | undefined;
  if (form) {
    payload = form;
  } else if (formData) {
    payload = formData;
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, { method, headers, body: payload });
  } catch {
    throw new ApiError(
      "Não foi possível conectar ao servidor. Verifique a rede.",
      0,
      "NETWORK_ERROR",
    );
  }

  if (
    response.status === 401 &&
    retry &&
    !path.startsWith("/auth/login") &&
    !path.startsWith("/auth/refresh")
  ) {
    const refreshed = await refreshSession();
    if (refreshed) {
      return request<T>(path, { ...options, retry: false });
    }
    clearSession();
    window.dispatchEvent(new Event("lims:logout"));
  }

  if (response.status === 204) return undefined as T;

  const text = await response.text();
  let data: unknown = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = { detail: text };
    }
  }

  if (!response.ok) {
    const errorBody = (data ?? {}) as {
      detail?: unknown;
      code?: string;
      request_id?: string;
      context?: unknown;
      errors?: unknown;
    };
    const detail =
      typeof errorBody.detail === "string"
        ? errorBody.detail
        : "A operação não pôde ser concluída.";
    throw new ApiError(
      detail,
      response.status,
      errorBody.code,
      errorBody.request_id,
      errorBody.context ?? errorBody.errors,
    );
  }

  return data as T;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown, signatureToken?: string) =>
    request<T>(path, { method: "POST", body, signatureToken }),
  patch: <T>(path: string, body?: unknown, signatureToken?: string) =>
    request<T>(path, { method: "PATCH", body, signatureToken }),
  login: <T>(username: string, password: string) =>
    request<T>("/auth/login", {
      method: "POST",
      form: new URLSearchParams({ username, password }),
    }),
  verifyMfaLogin: <T>(mfa_token: string, code: string) =>
    request<T>("/auth/login/mfa-verify", {
      method: "POST",
      body: { mfa_token, code },
    }),
  upload: <T>(path: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return request<T>(path, { method: "POST", formData });
  },
  rawRequest: request,
};

function filenameFromDisposition(value: string | null): string | null {
  if (!value) return null;
  const encoded = /filename\*=UTF-8''([^;]+)/i.exec(value);
  if (encoded) {
    try {
      return decodeURIComponent(encoded[1]);
    } catch {
      return encoded[1];
    }
  }
  const plain = /filename="?([^";]+)"?/i.exec(value);
  return plain?.[1] ?? null;
}

async function downloadError(response: Response): Promise<ApiError> {
  const text = await response.text();
  let data: unknown = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = null;
    }
  }
  const body = (data ?? {}) as {
    detail?: unknown;
    code?: string;
    request_id?: string;
    context?: unknown;
  };
  return new ApiError(
    typeof body.detail === "string"
      ? body.detail
      : "Não foi possível baixar o arquivo.",
    response.status,
    body.code,
    body.request_id,
    body.context,
  );
}

/** Baixa um arquivo autenticado (inclusive POST) e preserva o nome sugerido. */
export async function downloadFile(
  path: string,
  options: { method?: "GET" | "POST"; body?: unknown } = {},
): Promise<{ blob: Blob; filename: string | null }> {
  const method = options.method ?? "POST";

  async function send(): Promise<Response> {
    const headers: Record<string, string> = {};
    const accessToken = getAccessToken();
    if (accessToken) headers.Authorization = `Bearer ${accessToken}`;
    if (options.body !== undefined) headers["Content-Type"] = "application/json";
    return fetch(`${API_BASE}${path}`, {
      method,
      headers,
      body:
        options.body !== undefined ? JSON.stringify(options.body) : undefined,
    });
  }

  let response: Response;
  try {
    response = await send();
    if (response.status === 401) {
      const refreshed = await refreshSession();
      if (refreshed) response = await send();
    }
  } catch {
    throw new ApiError(
      "Não foi possível conectar ao servidor. Verifique a rede.",
      0,
      "NETWORK_ERROR",
    );
  }

  if (!response.ok) throw await downloadError(response);

  return {
    blob: await response.blob(),
    filename: filenameFromDisposition(
      response.headers.get("Content-Disposition"),
    ),
  };
}

/** Baixa um recurso binário autenticado e devolve um object URL. */
export async function fetchObjectUrl(path: string): Promise<string> {
  async function download(): Promise<Response> {
    const accessToken = getAccessToken();
    return fetch(`${API_BASE}${path}`, {
      headers: accessToken ? { Authorization: `Bearer ${accessToken}` } : {},
    });
  }

  let response = await download();
  if (response.status === 401) {
    const refreshed = await refreshSession();
    if (refreshed) response = await download();
  }
  if (!response.ok) {
    throw new ApiError("Não foi possível carregar a imagem.", response.status);
  }
  return URL.createObjectURL(await response.blob());
}

export function buildQuery(
  params: Record<string, string | number | boolean | null | undefined>,
): string {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === null || value === undefined || value === "") return;
    search.set(key, String(value));
  });
  const query = search.toString();
  return query ? `?${query}` : "";
}

// ============================================================================
// Fase 2 APIs: Métodos, Equipamentos e Execuções de Bancada
// ============================================================================

import type {
  Capa,
  CapaActionItem,
  CapaCreateResponse,
  Page,
  EquipmentCalibrationPayload,
  EquipmentCreatePayload,
  LaboratoryEquipment,
  TestMethod,
  TestMethodCreatePayload,
  TestExecution,
  TestExecutionCompletePayload,
  TestExecutionInterruptPayload,
  TestExecutionRecordDataPayload,
  TestExecutionStartPayload,
  LabTest,
  TestReview,
  TestSubmitReviewPayload,
  TestReviewDecisionPayload,
  OfficialReport,
  OfficialReportGeneratePayload,
  OfficialReportAmendPayload,
  OfficialReportPublicVerify,
  TestAttachment,
  AnalystQualification,
  QualificationCheck,
  TrainingRecord,
  UncertaintyBudget,
  UncertaintyBudgetCreatePayload,
  UncertaintyCalculation,
  UncertaintySimulatePayload,
  OperationalAnalytics,
  QualityControlAnalytics,
  NotificationItem,
  NotificationSummary,
  AlertCheckResult,
  InstrumentDataImport,
  InstrumentDataSummary,
  WebhookSubscription,
  WebhookDelivery,
  WebhookPingResponse,
  MfaSetupResponse,
  MfaEnableRequest,
  MfaEnableResponse,
  MfaDisableRequest,
  Reagent,
  ReagentBatch,
  ReagentCreatePayload,
  ReagentBatchCreatePayload,
  ExecutionReagentUsagePayload,
  ExecutionReagentUsage,
  OOSInvestigation,
  OOSInvestigationCreatePayload,
  OOSPhase1UpdatePayload,
  OOSPhase2UpdatePayload,
  OOSClosePayload,
  StorageLocation,
  StorageLocationCreatePayload,
  ServiceClient,
  ServiceClientCreatePayload,
  ServiceClientCreated,
  OutboxEvent,
  InstrumentProfile,
  SampleStorageMovement,
  SampleStorageMovementCreatePayload,
  SampleRetention,
  SampleRetentionCreatePayload,
  SampleDisposalRecord,
  SampleDisposalCreatePayload,
  StorageDashboardSummary,
  QCRun,
  QCRunCreatePayload,
  QCRunResolvePayload,
  LeveyJenningsChartData,
} from "./types";

export const methodsApi = {
  list: (
    options?: { category?: string; activeOnly?: boolean } | string,
    activeOnly = true,
  ) => {
    let cat: string | undefined;
    let act = activeOnly;
    if (typeof options === "object" && options !== null) {
      cat = options.category;
      act = options.activeOnly ?? true;
    } else {
      cat = options;
    }
    return request<TestMethod[]>(
      `/catalog/methods${buildQuery({ category: cat, active_only: act })}`,
    );
  },
  get: (id: string) => request<TestMethod>(`/catalog/methods/${id}`),
  create: (payload: TestMethodCreatePayload) =>
    request<TestMethod>("/catalog/methods", {
      method: "POST",
      body: payload,
    }),
  update: (id: string, payload: Partial<TestMethodCreatePayload>) =>
    request<TestMethod>(`/catalog/methods/${id}`, {
      method: "PUT",
      body: payload,
    }),
  seedStandards: () =>
    request<TestMethod[]>("/catalog/methods/seed-standards", {
      method: "POST",
    }),
};

export const equipmentApi = {
  list: (
    options?: { status?: string; activeOnly?: boolean } | string,
    activeOnly = true,
  ) => {
    let st: string | undefined;
    let act = activeOnly;
    if (typeof options === "object" && options !== null) {
      st = options.status;
      act = options.activeOnly ?? true;
    } else {
      st = options;
    }
    return request<LaboratoryEquipment[]>(
      `/equipment${buildQuery({ calibration_status: st, active_only: act })}`,
    );
  },
  get: (id: string) => request<LaboratoryEquipment>(`/equipment/${id}`),
  create: (payload: EquipmentCreatePayload) =>
    request<LaboratoryEquipment>("/equipment", {
      method: "POST",
      body: payload,
    }),
  update: (id: string, payload: Partial<EquipmentCreatePayload>) =>
    request<LaboratoryEquipment>(`/equipment/${id}`, {
      method: "PUT",
      body: payload,
    }),
  calibrate: (id: string, payload: EquipmentCalibrationPayload) =>
    request<LaboratoryEquipment>(`/equipment/${id}/calibration`, {
      method: "POST",
      body: payload,
    }),
};

export const executionsApi = {
  list: (testId: string) =>
    request<TestExecution[]>(`/tests/${testId}/executions`),
  listForTest: (testId: string) =>
    request<TestExecution[]>(`/tests/${testId}/executions`),
  start: (testId: string, payload: TestExecutionStartPayload) =>
    request<TestExecution>(`/tests/${testId}/executions`, {
      method: "POST",
      body: payload,
    }),
  get: (executionId: string) =>
    request<TestExecution>(`/executions/${executionId}`),
  recordReadings: (executionId: string, payload: TestExecutionRecordDataPayload) =>
    request<TestExecution>(`/executions/${executionId}/readings`, {
      method: "POST",
      body: payload,
    }),
  complete: (executionId: string, payload: TestExecutionCompletePayload) =>
    request<TestExecution>(`/executions/${executionId}/complete`, {
      method: "POST",
      body: payload,
    }),
  interrupt: (executionId: string, payload: TestExecutionInterruptPayload) =>
    request<TestExecution>(`/executions/${executionId}/interrupt`, {
      method: "POST",
      body: payload,
    }),
};

// ============================================================================
// Fase 3 APIs: Revisão por Pares, Laudos Periciais Oficiais e Evidências
// ============================================================================

export const reviewsApi = {
  listPending: () => request<LabTest[]>("/reviews/tests/pending"),
  submit: (testId: string, payload?: TestSubmitReviewPayload) =>
    request<LabTest>(`/reviews/tests/${testId}/submit`, {
      method: "POST",
      body: payload ?? {},
    }),
  decide: (testId: string, payload: TestReviewDecisionPayload, signatureToken?: string) =>
    request<TestReview>(`/reviews/tests/${testId}/decide`, {
      method: "POST",
      body: payload,
      signatureToken,
    }),
  getHistory: (testId: string) =>
    request<TestReview[]>(`/reviews/tests/${testId}`),
};

export const reportsApi = {
  generateOfficial: (payload: OfficialReportGeneratePayload, signatureToken: string) =>
    request<OfficialReport>("/reports/official", {
      method: "POST",
      body: payload,
      signatureToken,
    }),
  amendOfficial: (reportId: string, payload: OfficialReportAmendPayload, signatureToken: string) =>
    request<OfficialReport>(`/reports/official/${reportId}/amend`, {
      method: "POST",
      body: payload,
      signatureToken,
    }),
  getOfficial: (reportId: string) =>
    request<OfficialReport>(`/reports/official/${reportId}`),
  listForSample: (sampleId: string) =>
    request<OfficialReport[]>(`/reports/official/sample/${sampleId}`),
  verifyPublic: (tokenOrHash: string) =>
    request<OfficialReportPublicVerify>(`/public/reports/verify/${tokenOrHash}`),
  getPdfUrl: (reportId: string) => `/api/v1/reports/official/${reportId}/pdf`,
  getPublicPdfUrl: (tokenOrHash: string) => `/api/v1/public/reports/${tokenOrHash}/pdf`,
};

export const attachmentsApi = {
  upload: (testId: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return request<TestAttachment>(`/attachments/tests/${testId}`, {
      method: "POST",
      formData,
    });
  },
  list: (testId: string) =>
    request<TestAttachment[]>(`/attachments/tests/${testId}`),
  getDownloadUrl: (attachmentId: string) =>
    `${API_BASE}/attachments/${attachmentId}/download`,
};

export const qualificationsApi = {
  list: (params?: { user_id?: string; method_id?: string; status?: string }) => {
    const query = new URLSearchParams();
    if (params?.user_id) query.set("user_id", params.user_id);
    if (params?.method_id) query.set("method_id", params.method_id);
    if (params?.status) query.set("status", params.status);
    const qs = query.toString();
    return request<AnalystQualification[]>(`/qualifications${qs ? `?${qs}` : ""}`);
  },
  check: (userId: string, methodId: string) =>
    request<QualificationCheck>(`/qualifications/check?user_id=${userId}&method_id=${methodId}`),
  grant: (payload: unknown, signatureToken?: string) =>
    request<AnalystQualification>("/qualifications/grant", {
      method: "POST",
      body: payload,
      signatureToken,
    }),
  revoke: (id: string, payload: { status: string; reason: string }, signatureToken?: string) =>
    request<AnalystQualification>(`/qualifications/${id}/revoke`, {
      method: "POST",
      body: payload,
      signatureToken,
    }),
  recordTraining: (userId: string, payload: unknown, qualificationId?: string) => {
    const query = new URLSearchParams({ user_id: userId });
    if (qualificationId) query.set("qualification_id", qualificationId);
    return request<TrainingRecord>(`/qualifications/trainings?${query.toString()}`, {
      method: "POST",
      body: payload,
    });
  },
};

export const uncertaintyApi = {
  simulate: (payload: UncertaintySimulatePayload) =>
    request<UncertaintyCalculation>("/uncertainty/simulate", {
      method: "POST",
      body: payload,
    }),
  createBudget: (payload: UncertaintyBudgetCreatePayload, signatureToken?: string) =>
    request<UncertaintyBudget>("/uncertainty/budgets", {
      method: "POST",
      body: payload,
      signatureToken,
    }),
  listBudgets: (params?: {
    lab_test_id?: string;
    method_id?: string;
    execution_id?: string;
    conformity_status?: string;
  }) => {
    const qs = buildQuery({
      lab_test_id: params?.lab_test_id,
      method_id: params?.method_id,
      execution_id: params?.execution_id,
      conformity_status: params?.conformity_status,
    });
    return request<UncertaintyBudget[]>(`/uncertainty/budgets${qs}`);
  },
  getBudget: (budgetId: string) =>
    request<UncertaintyBudget>(`/uncertainty/budgets/${budgetId}`),
};

export const capasApi = {
  list: (params?: { status?: string; source_type?: string; sample_id?: string; page?: number; size?: number }) => {
    const qs = buildQuery({
      status: params?.status,
      source_type: params?.source_type,
      sample_id: params?.sample_id,
      page: params?.page,
      size: params?.size ?? 50,
    });
    return request<Page<Capa>>(`/capas${qs}`);
  },
  get: (id: string) => request<Capa>(`/capas/${id}`),
  create: (payload: unknown, signatureToken: string) =>
    request<CapaCreateResponse>("/capas", {
      method: "POST",
      body: payload,
      signatureToken,
    }),
  update: (id: string, payload: unknown, signatureToken: string) =>
    request<Capa>(`/capas/${id}`, {
      method: "PATCH",
      body: payload,
      signatureToken,
    }),
  addActionItem: (capaId: string, payload: unknown) =>
    request<CapaActionItem>(`/capas/${capaId}/items`, {
      method: "POST",
      body: payload,
    }),
  updateActionItem: (capaId: string, itemId: string, payload: unknown) =>
    request<CapaActionItem>(`/capas/${capaId}/items/${itemId}`, {
      method: "PATCH",
      body: payload,
    }),
  deleteActionItem: (capaId: string, itemId: string) =>
    request<void>(`/capas/${capaId}/items/${itemId}`, {
      method: "DELETE",
    }),
  evaluateEffectiveness: (capaId: string, payload: unknown, signatureToken: string) =>
    request<Capa>(`/capas/${capaId}/effectiveness`, {
      method: "POST",
      body: payload,
      signatureToken,
    }),
};

export const analyticsApi = {
  getOperational: () => request<OperationalAnalytics>("/analytics/operational"),
  getQualityControl: (methodId?: string) => {
    const qs = buildQuery({ method_id: methodId });
    return request<QualityControlAnalytics>(`/analytics/quality-control${qs}`);
  },
};

export const notificationsApi = {
  list: (params?: { unread_only?: boolean; severity?: string; limit?: number }) => {
    const qs = buildQuery({
      unread_only: params?.unread_only,
      severity: params?.severity,
      limit: params?.limit ?? 50,
    });
    return request<NotificationItem[]>(`/notifications${qs}`);
  },
  getSummary: () => request<NotificationSummary>("/notifications/summary"),
  markAsRead: (notificationId: string) =>
    request<NotificationItem>(`/notifications/${notificationId}/read`, {
      method: "PATCH",
    }),
  markAllAsRead: () =>
    request<{ marked_count: number }>("/notifications/read-all", {
      method: "POST",
    }),
  checkAlerts: () =>
    request<AlertCheckResult>("/notifications/check-alerts", {
      method: "POST",
    }),
  create: (payload: unknown) =>
    request<NotificationItem>("/notifications", {
      method: "POST",
      body: payload,
    }),
};

export const instrumentDataApi = {
  list: (params?: {
    equipment_id?: string;
    test_execution_id?: string;
    status?: string;
    limit?: number;
  }) => {
    const qs = buildQuery({
      equipment_id: params?.equipment_id,
      test_execution_id: params?.test_execution_id,
      status: params?.status,
      limit: params?.limit ?? 50,
    });
    return request<InstrumentDataImport[]>(`/instrument-data${qs}`);
  },
  getSummary: () => request<InstrumentDataSummary>("/instrument-data/summary"),
  getById: (id: string) => request<InstrumentDataImport>(`/instrument-data/${id}`),
  uploadRaw: (payload: {
    equipment_id: string;
    file_name: string;
    file_format: string;
    raw_content: string;
    test_execution_id?: string;
  }) =>
    request<InstrumentDataImport>("/instrument-data/upload-raw", {
      method: "POST",
      body: payload,
    }),
  uploadMultipart: (
    equipmentId: string,
    fileFormat: string,
    file: File,
    testExecutionId?: string,
  ) => {
    const formData = new FormData();
    formData.append("equipment_id", equipmentId);
    formData.append("file_format", fileFormat);
    if (testExecutionId) {
      formData.append("test_execution_id", testExecutionId);
    }
    formData.append("file", file);
    return request<InstrumentDataImport>("/instrument-data/upload", {
      method: "POST",
      formData,
    });
  },
  mapToExecution: (importId: string, executionId: string) =>
    request<InstrumentDataImport>(`/instrument-data/${importId}/map-to-execution`, {
      method: "POST",
      body: { execution_id: executionId },
    }),
};

export const webhooksApi = {
  listSubscriptions: () => request<WebhookSubscription[]>("/webhooks/subscriptions"),
  getSubscription: (id: string) => request<WebhookSubscription>(`/webhooks/subscriptions/${id}`),
  createSubscription: (payload: { url: string; description?: string; events?: string[]; secret?: string }) =>
    request<WebhookSubscription>("/webhooks/subscriptions", {
      method: "POST",
      body: payload,
    }),
  deleteSubscription: (id: string) =>
    request<void>(`/webhooks/subscriptions/${id}`, {
      method: "DELETE",
    }),
  pingSubscription: (id: string) =>
    request<WebhookPingResponse>(`/webhooks/subscriptions/${id}/ping`, {
      method: "POST",
    }),
  listDeliveries: (params?: { subscription_id?: string; limit?: number }) => {
    const query = new URLSearchParams();
    if (params?.subscription_id) query.set("subscription_id", params.subscription_id);
    if (params?.limit) query.set("limit", String(params.limit));
    const qs = query.toString();
    return request<WebhookDelivery[]>(`/webhooks/deliveries${qs ? `?${qs}` : ""}`);
  },
};

export const mfaApi = {
  setup: () => request<MfaSetupResponse>("/auth/mfa/setup", { method: "POST" }),
  enable: (payload: MfaEnableRequest) =>
    request<MfaEnableResponse>("/auth/mfa/enable", {
      method: "POST",
      body: payload,
    }),
  disable: (payload: MfaDisableRequest) =>
    request<void>("/auth/mfa/disable", {
      method: "POST",
      body: payload,
    }),
};

export const reagentsApi = {
  list: (params?: { reagent_type?: string; is_active?: boolean; search?: string }) => {
    const query = new URLSearchParams();
    if (params?.reagent_type) query.set("reagent_type", params.reagent_type);
    if (params?.is_active !== undefined) query.set("is_active", String(params.is_active));
    if (params?.search) query.set("search", params.search);
    const qs = query.toString();
    return request<Reagent[]>(`/reagents${qs ? `?${qs}` : ""}`);
  },
  get: (id: string) => request<Reagent>(`/reagents/${id}`),
  create: (payload: ReagentCreatePayload) =>
    request<Reagent>("/reagents", {
      method: "POST",
      body: payload,
    }),
  listBatches: (params?: { reagent_id?: string; available_only?: boolean; expiring_days?: number }) => {
    const query = new URLSearchParams();
    if (params?.reagent_id) query.set("reagent_id", params.reagent_id);
    if (params?.available_only !== undefined) query.set("available_only", String(params.available_only));
    if (params?.expiring_days !== undefined) query.set("expiring_days", String(params.expiring_days));
    const qs = query.toString();
    return request<ReagentBatch[]>(`/reagents/batches${qs ? `?${qs}` : ""}`);
  },
  createBatch: (reagentId: string, payload: ReagentBatchCreatePayload) =>
    request<ReagentBatch>(`/reagents/${reagentId}/batches`, {
      method: "POST",
      body: payload,
    }),
  consumeInExecution: (executionId: string, payload: ExecutionReagentUsagePayload) =>
    request<ExecutionReagentUsage>(`/reagents/executions/${executionId}/consume`, {
      method: "POST",
      body: payload,
    }),
  listExecutionUsages: (executionId: string) =>
    request<ExecutionReagentUsage[]>(`/reagents/executions/${executionId}/reagents`),
};

export const oosApi = {
  list: (params?: {
    lab_test_id?: string;
    status?: string;
    deviation_type?: string;
    is_open?: boolean;
    search?: string;
  }) => {
    const query = new URLSearchParams();
    if (params?.lab_test_id) query.set("lab_test_id", params.lab_test_id);
    if (params?.status) query.set("status", params.status);
    if (params?.deviation_type) query.set("deviation_type", params.deviation_type);
    if (params?.is_open !== undefined) query.set("is_open", String(params.is_open));
    if (params?.search) query.set("search", params.search);
    const qs = query.toString();
    return request<OOSInvestigation[]>(`/oos${qs ? `?${qs}` : ""}`);
  },
  get: (id: string) => request<OOSInvestigation>(`/oos/${id}`),
  create: (payload: OOSInvestigationCreatePayload) =>
    request<OOSInvestigation>("/oos", {
      method: "POST",
      body: payload,
    }),
  updatePhase1: (id: string, payload: OOSPhase1UpdatePayload) =>
    request<OOSInvestigation>(`/oos/${id}/phase1`, {
      method: "PUT",
      body: payload,
    }),
  updatePhase2: (id: string, payload: OOSPhase2UpdatePayload) =>
    request<OOSInvestigation>(`/oos/${id}/phase2`, {
      method: "PUT",
      body: payload,
    }),
  close: (id: string, payload: OOSClosePayload) =>
    request<OOSInvestigation>(`/oos/${id}/close`, {
      method: "POST",
      body: payload,
    }),
};

export const storageApi = {
  getSummary: () => request<StorageDashboardSummary>("/storage/summary"),

  // Locais Físicos
  listLocations: (params?: { is_active?: boolean; location_type?: string }) => {
    const qs = buildQuery({
      is_active: params?.is_active,
      location_type: params?.location_type,
    });
    return request<StorageLocation[]>(`/storage/locations${qs}`);
  },
  getLocation: (id: string) => request<StorageLocation>(`/storage/locations/${id}`),
  createLocation: (payload: StorageLocationCreatePayload) =>
    request<StorageLocation>("/storage/locations", {
      method: "POST",
      body: payload,
    }),
  updateLocation: (id: string, payload: Partial<StorageLocationCreatePayload> & { is_active?: boolean }) =>
    request<StorageLocation>(`/storage/locations/${id}`, {
      method: "PATCH",
      body: payload,
    }),

  // Movimentações
  listMovements: (params?: { sample_id?: string }) => {
    const qs = buildQuery({ sample_id: params?.sample_id });
    return request<SampleStorageMovement[]>(`/storage/movements${qs}`);
  },
  createMovement: (payload: SampleStorageMovementCreatePayload) =>
    request<SampleStorageMovement>("/storage/movements", {
      method: "POST",
      body: payload,
    }),

  // Contraprovas Periciais
  listRetentions: (params?: { status?: string; location_id?: string }) => {
    const qs = buildQuery({
      status: params?.status,
      location_id: params?.location_id,
    });
    return request<SampleRetention[]>(`/storage/retentions${qs}`);
  },
  getRetention: (id: string) => request<SampleRetention>(`/storage/retentions/${id}`),
  createRetention: (payload: SampleRetentionCreatePayload) =>
    request<SampleRetention>("/storage/retentions", {
      method: "POST",
      body: payload,
    }),
  updateRetention: (id: string, payload: { retain_until?: string; seal_number?: string; status?: string; notes?: string }) =>
    request<SampleRetention>(`/storage/retentions/${id}`, {
      method: "PATCH",
      body: payload,
    }),

  // Descarte com Dupla Assinatura (21 CFR Part 11)
  listDisposals: (params?: { sample_id?: string }) => {
    const qs = buildQuery({ sample_id: params?.sample_id });
    return request<SampleDisposalRecord[]>(`/storage/disposals${qs}`);
  },
  executeDisposal: (payload: SampleDisposalCreatePayload) =>
    request<SampleDisposalRecord>("/storage/disposal", {
      method: "POST",
      body: payload,
    }),
};

export const spcApi = {
  createRun: (payload: QCRunCreatePayload) =>
    request<QCRun>("/spc/runs", {
      method: "POST",
      body: payload,
    }),
  listRuns: (params?: { method_id?: string; status?: string; is_active_violation?: boolean }) => {
    const qs = buildQuery({
      method_id: params?.method_id,
      status: params?.status,
      is_active_violation: params?.is_active_violation,
    });
    return request<QCRun[]>(`/spc/runs${qs}`);
  },
  getChart: (methodId: string) =>
    request<LeveyJenningsChartData>(`/spc/methods/${methodId}/chart`),
  resolveRun: (runId: string, payload: QCRunResolvePayload) =>
    request<QCRun>(`/spc/runs/${runId}/resolve`, {
      method: "POST",
      body: payload,
    }),
};

export const integrationApi = {
  // Contas de Serviço (M2M)
  listServiceClients: () => request<ServiceClient[]>("/service-clients"),
  createServiceClient: (payload: ServiceClientCreatePayload) =>
    request<ServiceClientCreated>("/service-clients", {
      method: "POST",
      body: payload,
    }),
  rotateSecret: (clientId: string) =>
    request<{ client_id: string; client_secret: string; expires_at: string }>(
      `/service-clients/${clientId}/rotate-secret`,
      { method: "POST" },
    ),
  deactivateServiceClient: (clientId: string) =>
    request<ServiceClient>(`/service-clients/${clientId}`, {
      method: "DELETE",
    }),

  // Outbox & Webhooks
  getPendingOutbox: (limit = 50) =>
    request<OutboxEvent[]>(`/outbox/pending?limit=${limit}`),
  getDeadLetterOutbox: (limit = 50) =>
    request<OutboxEvent[]>(`/outbox/dead-letter?limit=${limit}`),
  dispatchOutbox: (limit = 50) =>
    request<{ dispatched: number; failed: number }>(`/outbox/dispatch?limit=${limit}`, {
      method: "POST",
    }),
  retryDeadLetter: (id: string) =>
    request<OutboxEvent>(`/outbox/${id}/retry`, { method: "POST" }),

  // Perfis de Instrumentos
  getProfiles: () =>
    request<{ profiles: InstrumentProfile[] }>("/instrument-data/profiles"),
};







