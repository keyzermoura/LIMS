import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  AlertTriangle,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Download,
  Filter,
  Fingerprint,
  Loader2,
  RefreshCw,
  Search,
  ShieldCheck,
  ShieldX,
  Upload,
  X,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useToast } from "@/components/ui/toast";
import { api, ApiError, buildQuery, downloadFile } from "@/lib/api";
import type {
  AuditAction,
  AuditExportFormat,
  AuditExportVerifyResult,
  AuditLogEntry,
  AuditVerifyResult,
  DeviceSample,
  Page,
  UserBrief,
} from "@/lib/types";
import { formatDateTime, shortHash } from "@/lib/utils";

const ACTION_LABELS: Record<string, string> = {
  CREATE: "Criação",
  UPDATE: "Alteração",
  DELETE: "Exclusão",
  TRANSFER: "Transferência",
  STATUS_CHANGE: "Mudança de status",
  SIGN: "Assinatura",
  LOGIN: "Login",
  LOGIN_FAILED: "Falha de login",
  LOGOUT: "Logout",
  REFRESH: "Renovação de sessão",
  SIGNATURE_ISSUED: "Assinatura emitida",
  SIGNATURE_REJECTED: "Assinatura rejeitada",
  CAPA_AUTO_OPEN: "CAPA automática",
  INTEGRITY_CHECK: "Verificação de integridade",
  EXPORT: "Exportação da trilha",
  EXPORT_VERIFIED: "Exportação verificada",
};

const ENTITY_LABELS: Record<string, string> = {
  DeviceSample: "Amostra",
  LabTest: "Ensaio",
  CapaAction: "CAPA",
  ChainOfCustody: "Custódia",
  User: "Usuário",
  ElectronicSignature: "Assinatura",
  AuditLog: "Auditoria",
};

const ACTION_FILTERS: Array<{ value: AuditAction; label: string }> = [
  { value: "CREATE", label: "Criação" },
  { value: "UPDATE", label: "Alteração" },
  { value: "TRANSFER", label: "Transferência de custódia" },
  { value: "STATUS_CHANGE", label: "Mudança de status" },
  { value: "CAPA_AUTO_OPEN", label: "CAPA automática" },
  { value: "SIGNATURE_ISSUED", label: "Assinatura emitida" },
  { value: "SIGNATURE_REJECTED", label: "Assinatura rejeitada" },
  { value: "LOGIN", label: "Login" },
  { value: "LOGIN_FAILED", label: "Falha de login" },
  { value: "INTEGRITY_CHECK", label: "Verificação de integridade" },
  { value: "EXPORT", label: "Exportação da trilha" },
  { value: "EXPORT_VERIFIED", label: "Exportação verificada" },
  { value: "LOGOUT", label: "Logout" },
];

const ENTITY_FILTERS: Array<{ value: string; label: string }> = [
  { value: "DeviceSample", label: "Amostra" },
  { value: "LabTest", label: "Ensaio" },
  { value: "CapaAction", label: "CAPA" },
  { value: "User", label: "Usuário" },
  { value: "ElectronicSignature", label: "Assinatura" },
  { value: "AuditLog", label: "Auditoria" },
];

interface Filters {
  entityType: string;
  entityId: string;
  actorId: string;
  action: string;
  search: string;
  dateFrom: string;
  dateTo: string;
}

const EMPTY_FILTERS: Filters = {
  entityType: "",
  entityId: "",
  actorId: "",
  action: "",
  search: "",
  dateFrom: "",
  dateTo: "",
};

/** Converte o estado da tela para os parâmetros aceitos pela API. */
function toApiFilters(filters: Filters) {
  return {
    entity_type: filters.entityType || undefined,
    entity_id: filters.entityId || undefined,
    actor_id: filters.actorId || undefined,
    action: filters.action || undefined,
    search: filters.search || undefined,
    date_from: filters.dateFrom
      ? new Date(filters.dateFrom).toISOString()
      : undefined,
    // `datetime-local` tem precisão de minuto: inclui o minuto final inteiro.
    date_to: filters.dateTo
      ? new Date(new Date(filters.dateTo).getTime() + 59_999).toISOString()
      : undefined,
  };
}

export function AuditTrailPage() {
  const { push } = useToast();
  const [draft, setDraft] = React.useState<Filters>(EMPTY_FILTERS);
  const [applied, setApplied] = React.useState<Filters>(EMPTY_FILTERS);
  const [page, setPage] = React.useState(1);
  const [selected, setSelected] = React.useState<AuditLogEntry | null>(null);
  const [verifying, setVerifying] = React.useState(false);
  const [verification, setVerification] = React.useState<AuditVerifyResult | null>(null);
  const [exportOpen, setExportOpen] = React.useState(false);
  const [verifyExportOpen, setVerifyExportOpen] = React.useState(false);

  const usersQuery = useQuery({
    queryKey: ["users"],
    queryFn: () => api.get<UserBrief[]>("/users"),
  });

  const samplesQuery = useQuery({
    queryKey: ["samples", "recent"],
    queryFn: () => api.get<Page<DeviceSample>>("/samples?size=100"),
  });

  const auditQuery = useQuery({
    queryKey: ["audit", applied, page],
    queryFn: () => {
      const query = buildQuery({
        page,
        size: 50,
        ...toApiFilters(applied),
      });
      return api.get<Page<AuditLogEntry>>(`/audit${query}`);
    },
  });

  function applyFilters(event?: React.FormEvent) {
    event?.preventDefault();
    setPage(1);
    setApplied({ ...draft });
  }

  function clearFilters() {
    setDraft(EMPTY_FILTERS);
    setApplied(EMPTY_FILTERS);
    setPage(1);
  }

  async function verifyIntegrity() {
    setVerifying(true);
    try {
      const result = await api.post<AuditVerifyResult>("/audit/verify");
      setVerification(result);
      push({
        variant: result.ok ? "success" : "destructive",
        title: result.ok
          ? "Trilha íntegra"
          : "Integridade comprometida",
        description: result.ok
          ? `${result.checked} registros verificados · head ${shortHash(result.head_hash, 12)}`
          : `${result.issues.length} inconsistência(s) encontrada(s).`,
      });
      void auditQuery.refetch();
    } catch (error) {
      push({
        variant: "destructive",
        title: "Falha na verificação",
        description:
          error instanceof ApiError ? error.message : "Tente novamente.",
      });
    } finally {
      setVerifying(false);
    }
  }

  const data = auditQuery.data;
  const entries = data?.items ?? [];
  const hasFilters = Object.values(applied).some(Boolean);

  return (
    <div className="space-y-5">
      <Card>
        <CardHeader className="gap-4 border-b border-border pb-5 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-primary">
              Auditoria da qualidade
            </p>
            <CardTitle className="mt-1 flex items-center gap-2 text-lg">
              <ShieldCheck className="h-5 w-5" />
              Trilha de auditoria
            </CardTitle>
            <CardDescription className="mt-1 max-w-2xl">
              Registro append-only de todas as operações. Cada linha é encadeada por
              SHA-256 e autenticada por HMAC; alterações são bloqueadas no banco.
            </CardDescription>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <Button variant="outline" onClick={() => setExportOpen(true)}>
              <Download className="h-4 w-4" />
              Exportar trilha
            </Button>
            <Button variant="outline" onClick={() => setVerifyExportOpen(true)}>
              <Upload className="h-4 w-4" />
              Verificar arquivo
            </Button>
            <Button variant="outline" onClick={() => void auditQuery.refetch()}>
              <RefreshCw
                className={auditQuery.isFetching ? "h-4 w-4 animate-spin" : "h-4 w-4"}
              />
              Atualizar
            </Button>
            <Button onClick={() => void verifyIntegrity()} disabled={verifying}>
              {verifying ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Fingerprint className="h-4 w-4" />
              )}
              Verificar integridade
            </Button>
          </div>
        </CardHeader>

        <CardContent className="pt-5">
          {verification ? (
            <div
              className={`mb-5 flex flex-wrap items-start gap-3 rounded-md border px-4 py-3 text-[13px] ${
                verification.ok
                  ? "border-emerald-200 bg-emerald-50 text-emerald-950"
                  : "border-rose-200 bg-rose-50 text-rose-950"
              }`}
              role="status"
            >
              {verification.ok ? (
                <CheckCircle2 className="mt-0.5 h-5 w-5 text-emerald-700" />
              ) : (
                <ShieldX className="mt-0.5 h-5 w-5 text-rose-700" />
              )}
              <div className="min-w-0 flex-1">
                <p className="font-semibold">
                  {verification.ok
                    ? "Cadeia de auditoria íntegra"
                    : "Foram encontradas inconsistências"}
                </p>
                <p className="mt-0.5 opacity-80">
                  {verification.checked} de {verification.total_records} registros
                  verificados · último seq. {verification.last_sequence ?? "—"} ·
                  head{" "}
                  <span className="font-mono text-[11px]">
                    {shortHash(verification.head_hash, 20)}
                  </span>
                </p>
                {verification.issues.length > 0 ? (
                  <ul className="mt-2 space-y-1 font-mono text-[11px]">
                    {verification.issues.slice(0, 5).map((issue) => (
                      <li key={`${issue.sequence}-${issue.type}`}>
                        seq. {issue.sequence} · {issue.type} — {issue.detail}
                      </li>
                    ))}
                  </ul>
                ) : null}
              </div>
              <button
                type="button"
                onClick={() => setVerification(null)}
                className="rounded p-1 opacity-60 hover:opacity-100"
                aria-label="Fechar resultado da verificação"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          ) : null}

          <form onSubmit={applyFilters} className="grid gap-3 lg:grid-cols-12">
            <div className="grid gap-1.5 lg:col-span-3">
              <Label>Tipo de registro</Label>
              <Select
                value={draft.entityType || "ALL"}
                onValueChange={(value) =>
                  setDraft((current) => ({
                    ...current,
                    entityType: value === "ALL" ? "" : value,
                    entityId: "",
                  }))
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Todos" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">Todos os tipos</SelectItem>
                  {ENTITY_FILTERS.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="grid gap-1.5 lg:col-span-3">
              <Label>{draft.entityType === "DeviceSample" ? "Amostra" : "Registro"}</Label>
              {draft.entityType === "DeviceSample" ? (
                <Select
                  value={draft.entityId || "ALL"}
                  onValueChange={(value) =>
                    setDraft((current) => ({
                      ...current,
                      entityId: value === "ALL" ? "" : value,
                    }))
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Todas as amostras" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ALL">Todas as amostras</SelectItem>
                    {(samplesQuery.data?.items ?? []).map((sample) => (
                      <SelectItem key={sample.id} value={sample.id}>
                        {sample.accession_number} · {sample.commercial_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              ) : (
                <Input
                  value={draft.entityId}
                  onChange={(event) =>
                    setDraft((current) => ({
                      ...current,
                      entityId: event.target.value.trim(),
                    }))
                  }
                  placeholder="UUID do registro"
                  className="font-mono text-xs"
                />
              )}
            </div>

            <div className="grid gap-1.5 lg:col-span-3">
              <Label>Usuário</Label>
              <Select
                value={draft.actorId || "ALL"}
                onValueChange={(value) =>
                  setDraft((current) => ({
                    ...current,
                    actorId: value === "ALL" ? "" : value,
                  }))
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Todos os usuários" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">Todos os usuários</SelectItem>
                  {(usersQuery.data ?? []).map((candidate) => (
                    <SelectItem key={candidate.id} value={candidate.id}>
                      {candidate.full_name} · {candidate.username}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="grid gap-1.5 lg:col-span-3">
              <Label>Ação</Label>
              <Select
                value={draft.action || "ALL"}
                onValueChange={(value) =>
                  setDraft((current) => ({
                    ...current,
                    action: value === "ALL" ? "" : value,
                  }))
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Todas as ações" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">Todas as ações</SelectItem>
                  {ACTION_FILTERS.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="grid gap-1.5 lg:col-span-3">
              <Label htmlFor="date-from">De</Label>
              <Input
                id="date-from"
                type="datetime-local"
                value={draft.dateFrom}
                onChange={(event) =>
                  setDraft((current) => ({ ...current, dateFrom: event.target.value }))
                }
              />
            </div>
            <div className="grid gap-1.5 lg:col-span-3">
              <Label htmlFor="date-to">Até</Label>
              <Input
                id="date-to"
                type="datetime-local"
                value={draft.dateTo}
                onChange={(event) =>
                  setDraft((current) => ({ ...current, dateTo: event.target.value }))
                }
              />
            </div>
            <div className="grid gap-1.5 lg:col-span-4">
              <Label htmlFor="audit-search">Busca livre</Label>
              <div className="relative">
                <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  id="audit-search"
                  className="pl-9"
                  value={draft.search}
                  onChange={(event) =>
                    setDraft((current) => ({ ...current, search: event.target.value }))
                  }
                  placeholder="Usuário, motivo ou ID do registro"
                />
              </div>
            </div>
            <div className="flex items-end gap-2 lg:col-span-2">
              <Button type="submit" className="flex-1">
                <Filter className="h-4 w-4" />
                Filtrar
              </Button>
              {hasFilters ? (
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  onClick={clearFilters}
                  title="Limpar filtros"
                  aria-label="Limpar filtros"
                >
                  <X className="h-4 w-4" />
                </Button>
              ) : null}
            </div>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex-row items-center justify-between gap-3 border-b border-border pb-4">
          <div>
            <CardTitle className="text-[15px]">Eventos registrados</CardTitle>
            <CardDescription>
              {data
                ? `${data.total.toLocaleString("pt-BR")} evento(s) · página ${data.page} de ${Math.max(data.pages, 1)}`
                : "Carregando…"}
            </CardDescription>
          </div>
          <Badge variant="outline" className="gap-1 font-mono text-[10px]">
            <ShieldCheck className="h-3 w-3 text-success" />
            encadeado
          </Badge>
        </CardHeader>

        <CardContent className="p-0">
          {auditQuery.isPending ? (
            <div className="space-y-2 p-5">
              {[0, 1, 2, 3, 4].map((index) => (
                <div key={index} className="h-10 animate-pulse rounded bg-muted" />
              ))}
            </div>
          ) : auditQuery.isError ? (
            <div className="flex flex-col items-center gap-2 px-6 py-12 text-center">
              <AlertTriangle className="h-6 w-6 text-destructive" />
              <p className="text-sm font-medium">Não foi possível carregar a trilha</p>
              <p className="text-[13px] text-muted-foreground">
                {auditQuery.error instanceof ApiError
                  ? auditQuery.error.message
                  : "Tente novamente."}
              </p>
            </div>
          ) : entries.length === 0 ? (
            <div className="flex flex-col items-center gap-2 px-6 py-16 text-center">
              <Search className="h-7 w-7 text-muted-foreground/40" />
              <p className="text-sm font-medium">Nenhum evento encontrado</p>
              <p className="text-[13px] text-muted-foreground">
                Ajuste os filtros para ampliar a consulta.
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="bg-muted/30">
                  <TableHead className="w-[150px]">Data / Hora</TableHead>
                  <TableHead className="w-[160px]">Usuário</TableHead>
                  <TableHead className="w-[150px]">Ação</TableHead>
                  <TableHead className="w-[150px]">Entidade</TableHead>
                  <TableHead>Valor antigo</TableHead>
                  <TableHead>Valor novo</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {entries.map((entry) => (
                  <TableRow
                    key={entry.id}
                    className="cursor-pointer"
                    onClick={() => setSelected(entry)}
                  >
                    <TableCell className="whitespace-nowrap">
                      <p className="text-[12.5px]">{formatDateTime(entry.occurred_at)}</p>
                      <p className="audit-hash">seq. {entry.sequence}</p>
                    </TableCell>
                    <TableCell>
                      <p className="text-[12.5px] font-medium">{entry.actor_username}</p>
                      <p className="text-[11px] text-muted-foreground">
                        {entry.actor_role ?? "—"}
                      </p>
                    </TableCell>
                    <TableCell>
                      <ActionBadge action={entry.action} />
                    </TableCell>
                    <TableCell>
                      <p className="text-[12.5px]">
                        {ENTITY_LABELS[entry.entity_type] ?? entry.entity_type}
                      </p>
                      <p className="truncate font-mono text-[10px] text-muted-foreground">
                        {entry.entity_id.slice(0, 13)}
                      </p>
                    </TableCell>
                    <TableCell>
                      <ValuePreview value={entry.old_value} emptyLabel="—" />
                    </TableCell>
                    <TableCell>
                      <ValuePreview value={entry.new_value} />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>

        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-border px-5 py-3">
          <p className="text-[11px] text-muted-foreground">
            Clique em um evento para ver o manifesto completo e os hashes.
          </p>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={page <= 1 || auditQuery.isFetching}
              onClick={() => setPage((current) => Math.max(1, current - 1))}
            >
              <ChevronLeft className="h-4 w-4" />
              Anterior
            </Button>
            <span className="text-[11px] text-muted-foreground">
              {page} / {Math.max(data?.pages ?? 1, 1)}
            </span>
            <Button
              variant="outline"
              size="sm"
              disabled={page >= (data?.pages ?? 1) || auditQuery.isFetching}
              onClick={() => setPage((current) => current + 1)}
            >
              Próxima
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </Card>

      <AuditDetailDialog entry={selected} onClose={() => setSelected(null)} />
      <AuditExportDialog
        open={exportOpen}
        onClose={() => setExportOpen(false)}
        filters={applied}
        total={data?.total ?? 0}
        onExported={() => void auditQuery.refetch()}
      />
      <AuditExportVerifyDialog
        open={verifyExportOpen}
        onClose={() => setVerifyExportOpen(false)}
        onVerified={() => void auditQuery.refetch()}
      />
    </div>
  );
}

function ActionBadge({ action }: { action: string }) {
  const destructive = action === "SIGNATURE_REJECTED" || action === "LOGIN_FAILED";
  const success =
    action === "CREATE" ||
    action === "SIGN" ||
    action === "INTEGRITY_CHECK" ||
    action === "EXPORT" ||
    action === "EXPORT_VERIFIED";
  const warning = action === "STATUS_CHANGE" || action === "CAPA_AUTO_OPEN";
  const variant = destructive
    ? "destructive"
    : success
      ? "success"
      : warning
        ? "warning"
        : "outline";

  return (
    <Badge variant={variant} className="normal-case tracking-normal">
      {ACTION_LABELS[action] ?? action}
    </Badge>
  );
}

function ValuePreview({
  value,
  emptyLabel = "—",
}: {
  value: Record<string, unknown> | null;
  emptyLabel?: string;
}) {
  if (!value) return <span className="text-muted-foreground">{emptyLabel}</span>;

  const entries = Object.entries(value)
    .filter(([, item]) => item !== null && item !== undefined)
    .slice(0, 2);

  if (entries.length === 0) {
    return <span className="text-muted-foreground">{emptyLabel}</span>;
  }

  return (
    <div className="space-y-1">
      {entries.map(([key, item]) => (
        <div key={key} className="flex items-baseline gap-1.5 text-[11px]">
          <span className="shrink-0 text-muted-foreground">{key}:</span>
          <span className="truncate font-mono text-foreground/90">
            {formatValue(item)}
          </span>
        </div>
      ))}
      {Object.keys(value).length > entries.length ? (
        <span className="text-[10px] text-muted-foreground">
          +{Object.keys(value).length - entries.length} campo(s)
        </span>
      ) : null}
    </div>
  );
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "string") return value.length > 40 ? `${value.slice(0, 40)}…` : value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  try {
    const serialized = JSON.stringify(value);
    return serialized.length > 40 ? `${serialized.slice(0, 40)}…` : serialized;
  } catch {
    return String(value);
  }
}

function AuditDetailDialog({
  entry,
  onClose,
}: {
  entry: AuditLogEntry | null;
  onClose: () => void;
}) {
  return (
    <Dialog open={Boolean(entry)} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-h-[90vh] max-w-4xl overflow-y-auto">
        {entry ? (
          <>
            <DialogHeader>
              <div className="flex flex-wrap items-center gap-2">
                <ActionBadge action={entry.action} />
                <Badge variant="outline" className="font-mono">
                  seq. {entry.sequence}
                </Badge>
                <span className="text-[11px] text-muted-foreground">
                  {formatDateTime(entry.occurred_at)}
                </span>
              </div>
              <DialogTitle className="mt-1">
                {ENTITY_LABELS[entry.entity_type] ?? entry.entity_type} ·{" "}
                <span className="font-mono text-sm">{entry.entity_id}</span>
              </DialogTitle>
              <DialogDescription>
                {entry.reason ?? "Sem motivo declarado."}
              </DialogDescription>
            </DialogHeader>

            <div className="grid gap-3 md:grid-cols-2">
              <JsonPanel title="Valor antigo" value={entry.old_value} />
              <JsonPanel title="Valor novo" value={entry.new_value} />
            </div>

            <div className="grid gap-2 rounded-md border border-border bg-muted/30 p-4 text-[12px] sm:grid-cols-2">
              <Metadata label="Usuário" value={`${entry.actor_username} (${entry.actor_role ?? "—"})`} />
              <Metadata label="IP de origem" value={entry.ip_address ?? "—"} mono />
              <Metadata label="Request ID" value={entry.request_id ?? "—"} mono />
              <Metadata
                label="Assinatura eletrônica"
                value={entry.signature_id ?? "não vinculada"}
                mono
              />
              <Metadata label="Hash do registro" value={entry.hash} mono breakAll />
              <Metadata label="Hash anterior" value={entry.prev_hash} mono breakAll />
              <Metadata label="HMAC" value={entry.hmac} mono breakAll />
              <Metadata label="User agent" value={entry.user_agent ?? "—"} small />
            </div>

            <p className="text-[11px] leading-relaxed text-muted-foreground">
              Este evento é imutável. O hash encadeia o registro anterior e o HMAC
              autentica o conjunto com chave mantida fora do banco de dados.
            </p>
          </>
        ) : null}
      </DialogContent>
    </Dialog>
  );
}

function JsonPanel({
  title,
  value,
}: {
  title: string;
  value: Record<string, unknown> | null;
}) {
  return (
    <div>
      <p className="data-label mb-1.5">{title}</p>
      <pre className="max-h-72 overflow-auto rounded-md border border-border bg-slate-950 p-3 font-mono text-[11px] leading-relaxed text-slate-100 scrollbar-thin">
        {value ? JSON.stringify(value, null, 2) : "—"}
      </pre>
    </div>
  );
}

function Metadata({
  label,
  value,
  mono,
  breakAll,
  small,
}: {
  label: string;
  value: string;
  mono?: boolean;
  breakAll?: boolean;
  small?: boolean;
}) {
  return (
    <div className="min-w-0">
      <p className="data-label">{label}</p>
      <p
        className={`mt-0.5 ${mono ? "font-mono text-[10.5px]" : ""} ${
          breakAll ? "break-all" : "truncate"
        } ${small ? "text-[10px]" : ""}`}
        title={value}
      >
        {value}
      </p>
    </div>
  );
}

function AuditExportDialog({
  open,
  onClose,
  filters,
  total,
  onExported,
}: {
  open: boolean;
  onClose: () => void;
  filters: Filters;
  total: number;
  onExported: () => void;
}) {
  const { push } = useToast();
  const [format, setFormat] = React.useState<AuditExportFormat>("csv");
  const [busy, setBusy] = React.useState(false);
  const hasFilters = Object.values(filters).some(Boolean);

  async function handleExport() {
    setBusy(true);
    try {
      const { blob, filename } = await downloadFile("/audit/export", {
        body: { format, ...toApiFilters(filters) },
      });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename ?? "trilha-auditoria.zip";
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);

      push({
        variant: "success",
        title: "Trilha exportada",
        description: `${total.toLocaleString("pt-BR")} evento(s) · pacote com manifesto SHA-256/HMAC.`,
      });
      onExported();
      onClose();
    } catch (error) {
      push({
        variant: "destructive",
        title: "Falha na exportação",
        description:
          error instanceof ApiError ? error.message : "Tente novamente.",
      });
    } finally {
      setBusy(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={(value) => !value && onClose()}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Exportar trilha assinada</DialogTitle>
          <DialogDescription>
            Gera um pacote ZIP com os eventos, um arquivo canônico e um
            manifesto autenticado por SHA-256/HMAC. A exportação é registrada
            na própria trilha.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="rounded-md border border-border bg-muted/30 px-4 py-3 text-[12.5px]">
            <p className="font-medium">
              {hasFilters
                ? "Somente o recorte filtrado será exportado."
                : "A trilha completa será exportada."}
            </p>
            <p className="mt-1 text-muted-foreground">
              {total.toLocaleString("pt-BR")} evento(s) no escopo atual.
            </p>
          </div>

          <div className="grid gap-1.5">
            <Label htmlFor="export-format">Formato de apresentação</Label>
            <Select
              value={format}
              onValueChange={(value) => setFormat(value as AuditExportFormat)}
            >
              <SelectTrigger id="export-format">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="csv">CSV (planilha)</SelectItem>
                <SelectItem value="json">JSON (legível por máquina)</SelectItem>
              </SelectContent>
            </Select>
            <p className="text-[11px] text-muted-foreground">
              O arquivo verificável <span className="font-mono">events.jsonl</span>{" "}
              é sempre incluído, independentemente do formato escolhido.
            </p>
          </div>

          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={onClose} disabled={busy}>
              Cancelar
            </Button>
            <Button onClick={() => void handleExport()} disabled={busy}>
              {busy ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Download className="h-4 w-4" />
              )}
              Exportar
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function AuditExportVerifyDialog({
  open,
  onClose,
  onVerified,
}: {
  open: boolean;
  onClose: () => void;
  onVerified: () => void;
}) {
  const { push } = useToast();
  const [file, setFile] = React.useState<File | null>(null);
  const [result, setResult] = React.useState<AuditExportVerifyResult | null>(null);
  const [busy, setBusy] = React.useState(false);

  React.useEffect(() => {
    if (!open) {
      setFile(null);
      setResult(null);
    }
  }, [open]);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!file) return;
    setBusy(true);
    try {
      const report = await api.upload<AuditExportVerifyResult>(
        "/audit/export/verify",
        file,
      );
      setResult(report);
      push({
        variant: report.ok ? "success" : "destructive",
        title: report.ok ? "Arquivo íntegro" : "Arquivo não confere",
        description: report.ok
          ? `${report.checked} registro(s) verificados · manifesto ${shortHash(report.manifest_hash, 12)}`
          : `${report.issues.length} inconsistência(s) encontrada(s).`,
      });
      onVerified();
    } catch (error) {
      push({
        variant: "destructive",
        title: "Falha na verificação",
        description:
          error instanceof ApiError ? error.message : "Tente novamente.",
      });
    } finally {
      setBusy(false);
    }
  }

  const checks = result
    ? [
        { label: "Manifesto (SHA-256)", ok: result.manifest_hash_ok },
        { label: "Manifesto (HMAC)", ok: result.manifest_hmac_ok },
        { label: "Eventos (SHA-256)", ok: result.data_hash_ok },
        { label: "Eventos (HMAC)", ok: result.data_hmac_ok },
        { label: "Arquivos do pacote", ok: result.files_ok },
        { label: "Cadeia interna", ok: result.chain_ok },
        { label: "Âncora no banco", ok: result.matches_database },
      ]
    : [];

  return (
    <Dialog open={open} onOpenChange={(value) => !value && onClose()}>
      <DialogContent className="max-h-[90vh] max-w-2xl overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Verificar arquivo exportado</DialogTitle>
          <DialogDescription>
            Selecione o ZIP gerado pela exportação. O servidor recalcula os
            hashes/HMACs, valida a cadeia interna e ancora a cabeça no banco
            atual.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="grid gap-1.5">
            <Label htmlFor="audit-export-file">Pacote da trilha (.zip)</Label>
            <Input
              id="audit-export-file"
              type="file"
              accept=".zip,application/zip"
              onChange={(event) => {
                setFile(event.target.files?.[0] ?? null);
                setResult(null);
              }}
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="ghost" onClick={onClose} disabled={busy}>
              Fechar
            </Button>
            <Button type="submit" disabled={!file || busy}>
              {busy ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Upload className="h-4 w-4" />
              )}
              Verificar arquivo
            </Button>
          </div>
        </form>

        {result ? (
          <div
            className={`space-y-3 rounded-md border px-4 py-3 text-[12.5px] ${
              result.ok
                ? "border-emerald-200 bg-emerald-50 text-emerald-950"
                : "border-rose-200 bg-rose-50 text-rose-950"
            }`}
          >
            <div className="flex items-start gap-2">
              {result.ok ? (
                <ShieldCheck className="mt-0.5 h-5 w-5 text-emerald-700" />
              ) : (
                <ShieldX className="mt-0.5 h-5 w-5 text-rose-700" />
              )}
              <div className="min-w-0 flex-1">
                <p className="font-semibold">
                  {result.ok
                    ? "Arquivo íntegro e ancorado no banco"
                    : "O arquivo não pôde ser validado"}
                </p>
                <p className="mt-0.5 opacity-80">
                  {result.checked} de {result.record_count} registro(s)
                  {result.chain_gaps > 0
                    ? ` · ${result.chain_gaps} lacuna(s) de filtro`
                    : ""}
                  {result.generated_at
                    ? ` · exportado em ${formatDateTime(result.generated_at)}`
                    : ""}
                </p>
                {result.generated_by ? (
                  <p className="opacity-80">Por {result.generated_by}</p>
                ) : null}
              </div>
            </div>

            <ul className="grid gap-1 sm:grid-cols-2">
              {checks.map((check) => (
                <li key={check.label} className="flex items-center gap-1.5">
                  {check.ok ? (
                    <CheckCircle2 className="h-3.5 w-3.5 text-emerald-700" />
                  ) : (
                    <AlertTriangle className="h-3.5 w-3.5 text-rose-700" />
                  )}
                  {check.label}
                </li>
              ))}
            </ul>

            {result.issues.length > 0 ? (
              <ul className="space-y-1 font-mono text-[11px]">
                {result.issues.slice(0, 8).map((issue) => (
                  <li key={`${issue.sequence}-${issue.type}-${issue.detail}`}>
                    seq. {issue.sequence} · {issue.type} — {issue.detail}
                  </li>
                ))}
              </ul>
            ) : null}
          </div>
        ) : null}
      </DialogContent>
    </Dialog>
  );
}
