import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

const dateTimeFormatter = new Intl.DateTimeFormat("pt-BR", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit",
});

const dateFormatter = new Intl.DateTimeFormat("pt-BR", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
});

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return dateTimeFormatter.format(date);
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  // Datas puras (`YYYY-MM-DD`) não têm fuso; interpretá-las como UTC faria
  // a data exibir o dia anterior em fusos negativos (ex.: America/Sao_Paulo).
  const dateOnly = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  const date = dateOnly
    ? new Date(Number(dateOnly[1]), Number(dateOnly[2]) - 1, Number(dateOnly[3]))
    : new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return dateFormatter.format(date);
}

export function formatTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat("pt-BR", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

export function dayKey(value: string): string {
  const date = new Date(value);
  return date.toDateString();
}

export function dayLabel(value: string): string {
  const date = new Date(value);
  const today = new Date();
  const yesterday = new Date();
  yesterday.setDate(today.getDate() - 1);

  if (date.toDateString() === today.toDateString()) return "Hoje";
  if (date.toDateString() === yesterday.toDateString()) return "Ontem";
  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  }).format(date);
}

export function relativeTime(value: string): string {
  const date = new Date(value).getTime();
  const diffSeconds = Math.round((date - Date.now()) / 1000);
  const formatter = new Intl.RelativeTimeFormat("pt-BR", { numeric: "auto" });
  const ranges: Array<[Intl.RelativeTimeFormatUnit, number]> = [
    ["year", 60 * 60 * 24 * 365],
    ["month", 60 * 60 * 24 * 30],
    ["day", 60 * 60 * 24],
    ["hour", 60 * 60],
    ["minute", 60],
    ["second", 1],
  ];
  for (const [unit, seconds] of ranges) {
    if (Math.abs(diffSeconds) >= seconds || unit === "second") {
      return formatter.format(Math.round(diffSeconds / seconds), unit);
    }
  }
  return "";
}

export function initials(name: string): string {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("");
}

export function shortHash(hash: string | null | undefined, size = 10): string {
  if (!hash) return "—";
  return `${hash.slice(0, size)}…`;
}

export function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const index = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / 1024 ** index).toFixed(1)} ${units[index]}`;
}

/** Converte strings vazias em `null` para campos numéricos opcionais. */
export function toNumberOrNull(value: unknown): number | null {
  if (value === "" || value === null || value === undefined) return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

export const SAMPLE_STATUS_LABELS: Record<string, string> = {
  RECEBIDO: "Recebido",
  EM_TESTE: "Em teste",
  APROVADO: "Aprovado",
  REPROVADO: "Reprovado",
  DESCARTADO: "Descartado",
};

export const TEST_STATUS_LABELS: Record<string, string> = {
  PENDENTE: "Pendente",
  CONCLUIDO: "Concluído",
};

export const OUTCOME_LABELS: Record<string, string> = {
  APROVADO: "Aprovado",
  REPROVADO: "Reprovado",
  INCONCLUSIVO: "Inconclusivo",
};

export const CAPA_STATUS_LABELS: Record<string, string> = {
  ABERTA: "Aberta",
  EM_ANDAMENTO: "Em andamento",
  CONCLUIDA: "Concluída",
  CANCELADA: "Cancelada",
};

export const SOLICITATION_STATUS_LABELS: Record<string, string> = {
  DRAFT: "Rascunho",
  SUBMITTED: "Submetida",
  CANCELLED: "Cancelada",
};

export const RECEIPT_STATUS_LABELS: Record<string, string> = {
  DRAFT: "Rascunho",
  EM_CONFERENCIA: "Em conferência",
  CONCLUIDO: "Concluído",
  CANCELADO: "Cancelado",
};

export const CONFERENCE_STATUS_LABELS: Record<string, string> = {
  PENDENTE: "Pendente",
  CONFORME: "Conforme",
  COM_RESSALVA: "Com ressalva",
  NAO_CONFORME: "Não conforme",
};

export const CUSTODY_OBJECT_STATUS_LABELS: Record<string, string> = {
  AGUARDANDO_RECEBIMENTO: "Aguardando",
  RECEBIDO_INTEGRO: "Íntegro",
  RECEBIDO_AVARIADO: "Avariado",
  RETIDO: "Retido",
  TRANSFERIDO: "Transferido",
  ACEITO: "Aceito (Amostra)",
  REJEITADO: "Rejeitado",
};

export const CRITERION_CLASS_LABELS: Record<string, string> = {
  ELIMINATORIO: "Eliminatório",
  SANEAVEL: "Saneável",
  INFORMATIVO: "Informativo",
};

export const CHECKLIST_RESULT_LABELS: Record<string, string> = {
  CONFORME: "Conforme",
  NAO_CONFORME: "Não conforme",
  NAO_APLICA: "Não se aplica",
};

export const COORDINATION_STATUS_LABELS: Record<string, string> = {
  PENDENTE: "Pendente de revisão",
  APROVADO: "Aprovado",
  DEVOLVIDO: "Devolvido para diligência",
  REJEITADO: "Rejeitado",
};

export const RECEIPT_DECISION_LABELS: Record<string, string> = {
  ACCEPTED: "Aceito",
  PENDING: "Pendente de revisão",
  REJECTED: "Rejeitado",
};

export const ROLE_LABELS: Record<string, string> = {
  ADMIN: "Administrador",
  FISCAL: "Fiscal sanitário",
  TECNICO: "Técnico de laboratório",
  CUSTODIANTE: "Custodiante",
  AUDITOR: "Auditor da qualidade",
};

export const MEANING_LABELS: Record<string, string> = {
  AUTORIA: "Autoria",
  REVISAO: "Revisão",
  APROVACAO: "Aprovação",
  RESPONSABILIDADE_TECNICA: "Responsabilidade técnica",
  TRANSFERENCIA_DE_CUSTODIA: "Transferência de custódia",
  VERIFICACAO: "Verificação",
};

/** Classes de cor por status — mantidas em um único lugar. */
export const STATUS_TONE: Record<string, string> = {
  RECEBIDO: "border-sky-200 bg-sky-50 text-sky-800",
  EM_TESTE: "border-amber-200 bg-amber-50 text-amber-900",
  APROVADO: "border-emerald-200 bg-emerald-50 text-emerald-800",
  REPROVADO: "border-rose-200 bg-rose-50 text-rose-800",
  DESCARTADO: "border-slate-200 bg-slate-100 text-slate-600",
  PENDENTE: "border-sky-200 bg-sky-50 text-sky-800",
  CONCLUIDO: "border-emerald-200 bg-emerald-50 text-emerald-800",
  ABERTA: "border-rose-200 bg-rose-50 text-rose-800",
  EM_ANDAMENTO: "border-amber-200 bg-amber-50 text-amber-900",
  CONCLUIDA: "border-emerald-200 bg-emerald-50 text-emerald-800",
  CANCELADA: "border-slate-200 bg-slate-100 text-slate-600",
  INCONCLUSIVO: "border-slate-200 bg-slate-100 text-slate-700",
  DRAFT: "border-slate-200 bg-slate-100 text-slate-700",
  SUBMITTED: "border-sky-200 bg-sky-50 text-sky-800",
  CANCELLED: "border-rose-200 bg-rose-50 text-rose-800",
  EM_CONFERENCIA: "border-amber-200 bg-amber-50 text-amber-900",
  CONFORME: "border-emerald-200 bg-emerald-50 text-emerald-800",
  COM_RESSALVA: "border-amber-200 bg-amber-50 text-amber-900",
  NAO_CONFORME: "border-rose-200 bg-rose-50 text-rose-800",
  AGUARDANDO_RECEBIMENTO: "border-slate-200 bg-slate-100 text-slate-600",
  RECEBIDO_INTEGRO: "border-emerald-200 bg-emerald-50 text-emerald-800",
  RECEBIDO_AVARIADO: "border-rose-200 bg-rose-50 text-rose-800",
  RETIDO: "border-amber-200 bg-amber-50 text-amber-900",
  TRANSFERIDO: "border-sky-200 bg-sky-50 text-sky-800",
  ACEITO: "border-emerald-200 bg-emerald-50 text-emerald-800",
  REJEITADO: "border-rose-200 bg-rose-50 text-rose-800",
  ELIMINATORIO: "border-rose-200 bg-rose-50 text-rose-800",
  SANEAVEL: "border-amber-200 bg-amber-50 text-amber-900",
  INFORMATIVO: "border-blue-200 bg-blue-50 text-blue-800",
  NAO_APLICA: "border-slate-200 bg-slate-100 text-slate-600",
  DEVOLVIDO: "border-amber-200 bg-amber-50 text-amber-900",
};
