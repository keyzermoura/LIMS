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
  OfficialReportPublicVerify,
  TestAttachment,
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
  getOfficial: (reportId: string) =>
    request<OfficialReport>(`/reports/official/${reportId}`),
  listForSample: (sampleId: string) =>
    request<OfficialReport[]>(`/reports/official/sample/${sampleId}`),
  verifyPublic: (authToken: string) =>
    request<OfficialReportPublicVerify>(`/reports/verify/${authToken}`),
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
