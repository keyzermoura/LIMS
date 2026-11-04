import * as React from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertOctagon,
  CalendarClock,
  CheckCircle2,
  ClipboardCheck,
  ClipboardList,
  ExternalLink,
  Loader2,
  Plus,
  Search,
  ShieldCheck,
  Sparkles,
  Timer,
  TriangleAlert,
} from "lucide-react";
import { Link, useSearchParams } from "react-router-dom";

import { StatusBadge } from "@/components/StatusBadge";
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
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input, Textarea } from "@/components/ui/input";
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
import { useAuth } from "@/hooks/use-auth";
import { useESignature } from "@/hooks/use-esignature";
import { api, ApiError } from "@/lib/api";
import type {
  Capa,
  CapaCreateResponse,
  CapaStatus,
  DeviceSample,
  LabTest,
  Page,
  UserBrief,
  UserRole,
} from "@/lib/types";
import {
  CAPA_STATUS_LABELS,
  ROLE_LABELS,
  cn,
  formatDate,
  formatDateTime,
  initials,
} from "@/lib/utils";

const ALL = "ALL";

const STATUS_OPTIONS: CapaStatus[] = [
  "ABERTA",
  "EM_ANDAMENTO",
  "CONCLUIDA",
  "CANCELADA",
];

const FINAL_STATUSES: CapaStatus[] = ["CONCLUIDA", "CANCELADA"];

// Espelha a regra do backend: apenas estes perfis podem ser responsáveis por uma CAPA.
const CAPA_OWNER_ROLES: UserRole[] = ["ADMIN", "FISCAL", "TECNICO"];

function isCapaOwnerRole(role: UserRole): boolean {
  return CAPA_OWNER_ROLES.includes(role);
}

function pad(value: number): string {
  return String(value).padStart(2, "0");
}

function localIso(date: Date): string {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

function todayIso(): string {
  return localIso(new Date());
}

function tomorrowIso(): string {
  const date = new Date();
  date.setDate(date.getDate() + 1);
  return localIso(date);
}

function dueLabel(dueDate: string): string {
  const [year, month, day] = dueDate.split("-").map(Number);
  if (!year || !month || !day) return "";
  const target = new Date(year, month - 1, day).getTime();
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const difference = Math.round((target - today.getTime()) / 86_400_000);

  if (difference === 0) return "vence hoje";
  if (difference === 1) return "vence amanhã";
  if (difference > 1) return `em ${difference} dias`;
  if (difference === -1) return "1 dia em atraso";
  return `${Math.abs(difference)} dias em atraso`;
}

function isOverdue(capa: Capa): boolean {
  return !FINAL_STATUSES.includes(capa.status) && capa.due_date < todayIso();
}

function canManageCapa(capa: Capa, user: { id: string; role: string } | null): boolean {
  if (!user) return false;
  if (FINAL_STATUSES.includes(capa.status)) return false;
  if (user.role === "ADMIN" || user.role === "FISCAL") return true;
  return user.role === "TECNICO" && capa.owner.id === user.id;
}

export function CapasPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [searchParams, setSearchParams] = useSearchParams();
  const [search, setSearch] = React.useState("");
  const [newOpen, setNewOpen] = React.useState(false);
  const [selected, setSelected] = React.useState<Capa | null>(null);

  const statusFilter = (searchParams.get("status") ?? ALL) as CapaStatus | typeof ALL;
  const sampleFilter = searchParams.get("sample") ?? ALL;

  const canCreate =
    user?.role === "ADMIN" || user?.role === "FISCAL" || user?.role === "TECNICO";

  const capasQuery = useQuery({
    queryKey: ["capas", "all"],
    queryFn: () => api.get<Page<Capa>>("/capas?size=100"),
  });
  const samplesQuery = useQuery({
    queryKey: ["samples", "recent"],
    queryFn: () => api.get<Page<DeviceSample>>("/samples?size=100"),
  });
  const testsQuery = useQuery({
    queryKey: ["tests", "all"],
    queryFn: () => api.get<Page<LabTest>>("/tests?size=100"),
  });
  const usersQuery = useQuery({
    queryKey: ["users", "active"],
    queryFn: () => api.get<UserBrief[]>("/users"),
  });

  const capas = capasQuery.data?.items ?? [];
  const samples = samplesQuery.data?.items ?? [];
  const tests = testsQuery.data?.items ?? [];
  const users = usersQuery.data ?? [];

  const sampleById = React.useMemo(
    () => new Map(samples.map((sample) => [sample.id, sample])),
    [samples],
  );
  const testById = React.useMemo(
    () => new Map(tests.map((test) => [test.id, test])),
    [tests],
  );

  const stats = React.useMemo(() => {
    const open = capas.filter((capa) => capa.status === "ABERTA").length;
    const inProgress = capas.filter((capa) => capa.status === "EM_ANDAMENTO").length;
    const overdue = capas.filter(isOverdue).length;
    const closed = capas.filter((capa) => capa.status === "CONCLUIDA").length;
    const automatic = capas.filter(
      (capa) => capa.auto_opened && !FINAL_STATUSES.includes(capa.status),
    ).length;
    return { open, inProgress, overdue, closed, automatic };
  }, [capas]);

  const filtered = React.useMemo(() => {
    const term = search.trim().toLowerCase();
    return capas.filter((capa) => {
      if (statusFilter !== ALL && capa.status !== statusFilter) return false;
      if (sampleFilter !== ALL && capa.device_sample_id !== sampleFilter) return false;
      if (!term) return true;
      return [capa.code, capa.title, capa.root_cause, capa.action_plan, capa.owner.full_name]
        .join(" ")
        .toLowerCase()
        .includes(term);
    });
  }, [capas, statusFilter, sampleFilter, search]);

  const filtersActive = statusFilter !== ALL || sampleFilter !== ALL || search.trim() !== "";

  function updateFilter(key: "status" | "sample", value: string) {
    const next = new URLSearchParams(searchParams);
    if (value === ALL) next.delete(key);
    else next.set(key, value);
    setSearchParams(next, { replace: true });
  }

  function clearFilters() {
    setSearch("");
    setSearchParams(new URLSearchParams(), { replace: true });
  }

  function refresh() {
    void queryClient.invalidateQueries({ queryKey: ["capas"] });
    void queryClient.invalidateQueries({ queryKey: ["tests"] });
    void queryClient.invalidateQueries({ queryKey: ["samples"] });
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="gap-4 border-b border-border pb-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="min-w-0 flex-1">
            <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-primary">
              Qualidade
            </p>
            <CardTitle className="mt-1 text-lg">
              Ações corretivas e preventivas (CAPA)
            </CardTitle>
            <CardDescription className="mt-1 max-w-2xl">
              Todo resultado reprovado abre uma CAPA automaticamente. Cada mudança de
              causa raiz, plano de ação ou responsável exige assinatura eletrônica.
            </CardDescription>
          </div>

          <div className="flex w-full items-center gap-2 sm:w-auto">
            {stats.automatic > 0 ? (
              <span className="inline-flex items-center gap-1.5 rounded-full border border-rose-200 bg-rose-50 px-2.5 py-1 text-[11px] font-medium text-rose-800">
                <Sparkles className="h-3.5 w-3.5" />
                {stats.automatic} automática{stats.automatic > 1 ? "s" : ""}
              </span>
            ) : null}
            {canCreate ? (
              <Button onClick={() => setNewOpen(true)} disabled={samples.length === 0}>
                <Plus className="h-4 w-4" />
                Abrir CAPA
              </Button>
            ) : null}
          </div>
        </CardHeader>

        <CardContent className="grid gap-3 pt-5 sm:grid-cols-2 xl:grid-cols-4">
          <SummaryTile
            icon={<ClipboardList className="h-4 w-4" />}
            label="Abertas"
            value={stats.open}
            tone="rose"
          />
          <SummaryTile
            icon={<Timer className="h-4 w-4" />}
            label="Em andamento"
            value={stats.inProgress}
            tone="amber"
          />
          <SummaryTile
            icon={<AlertOctagon className="h-4 w-4" />}
            label="Atrasadas"
            value={stats.overdue}
            tone="rose"
          />
          <SummaryTile
            icon={<CheckCircle2 className="h-4 w-4" />}
            label="Concluídas"
            value={stats.closed}
            tone="emerald"
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="gap-3 border-b border-border pb-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <CardTitle className="text-[15px]">Registro de CAPAs</CardTitle>
              <CardDescription className="mt-0.5 text-[12px]">
                {filtered.length} de {capas.length} registros
                {stats.overdue > 0 ? ` · ${stats.overdue} em atraso` : ""}
              </CardDescription>
            </div>
            {filtersActive ? (
              <Button variant="ghost" size="sm" onClick={clearFilters}>
                Limpar filtros
              </Button>
            ) : null}
          </div>

          <div className="grid gap-2 md:grid-cols-[1fr_200px_260px]">
            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Buscar por código, título, causa ou responsável"
                className="pl-9"
                aria-label="Buscar CAPA"
              />
            </div>

            <Select
              value={statusFilter}
              onValueChange={(value) => updateFilter("status", value)}
            >
              <SelectTrigger aria-label="Filtrar por status">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={ALL}>Todos os status</SelectItem>
                {STATUS_OPTIONS.map((status) => (
                  <SelectItem key={status} value={status}>
                    {CAPA_STATUS_LABELS[status]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select
              value={sampleFilter}
              onValueChange={(value) => updateFilter("sample", value)}
            >
              <SelectTrigger aria-label="Filtrar por amostra">
                <SelectValue placeholder="Amostra" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={ALL}>Todas as amostras</SelectItem>
                {samples.map((sample) => (
                  <SelectItem key={sample.id} value={sample.id}>
                    {sample.accession_number} · {sample.commercial_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardHeader>

        <CardContent className="p-0">
          {capasQuery.isLoading ? (
            <div className="space-y-2 p-5">
              {[0, 1, 2].map((index) => (
                <div key={index} className="h-14 animate-pulse rounded-md bg-muted" />
              ))}
            </div>
          ) : capasQuery.isError ? (
            <div className="flex flex-col items-center gap-2 py-16 text-center">
              <TriangleAlert className="h-8 w-8 text-rose-500" />
              <p className="text-sm font-medium">Não foi possível carregar as CAPAs</p>
              <p className="text-[13px] text-muted-foreground">
                {capasQuery.error instanceof ApiError
                  ? capasQuery.error.message
                  : "Tente novamente em instantes."}
              </p>
              <Button variant="outline" size="sm" onClick={() => void capasQuery.refetch()}>
                Recarregar
              </Button>
            </div>
          ) : filtered.length === 0 ? (
            <div className="flex flex-col items-center gap-3 py-16 text-center">
              <ClipboardCheck className="h-8 w-8 text-muted-foreground/40" />
              <div>
                <p className="text-sm font-medium">
                  {capas.length === 0 ? "Nenhuma CAPA registrada" : "Nenhum resultado"}
                </p>
                <p className="mt-1 text-[13px] text-muted-foreground">
                  {capas.length === 0
                    ? "CAPAs são abertas automaticamente em reprovações ou manualmente pelo controle de qualidade."
                    : "Ajuste os filtros para visualizar outros registros."}
                </p>
              </div>
              {capas.length === 0 && canCreate ? (
                <Button variant="outline" onClick={() => setNewOpen(true)}>
                  <Plus className="h-4 w-4" />
                  Abrir CAPA
                </Button>
              ) : null}
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="pl-5">CAPA</TableHead>
                  <TableHead>Origem</TableHead>
                  <TableHead>Título</TableHead>
                  <TableHead>Responsável</TableHead>
                  <TableHead>Prazo</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="pr-5 text-right">Ações</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map((capa) => {
                  const sample = capa.device_sample_id
                    ? sampleById.get(capa.device_sample_id)
                    : null;
                  const test = capa.lab_test_id ? testById.get(capa.lab_test_id) : null;
                  const overdue = isOverdue(capa);
                  const editable = canManageCapa(capa, user);

                  return (
                    <TableRow key={`${capa.id}-${capa.version}`}>
                      <TableCell className="pl-5">
                        <div className="flex flex-col items-start gap-1">
                          <span className="font-mono text-[12px] font-semibold">
                            {capa.code}
                          </span>
                          {capa.auto_opened ? (
                            <Badge
                              variant="destructive"
                              className="gap-1 px-1.5 py-0 text-[9px]"
                            >
                              <Sparkles className="h-2.5 w-2.5" />
                              automática
                            </Badge>
                          ) : (
                            <span className="text-[10px] uppercase tracking-wider text-muted-foreground">
                              manual
                            </span>
                          )}
                        </div>
                      </TableCell>

                      <TableCell>
                        {sample ? (
                          <Link
                            to={`/tests?sample=${sample.id}`}
                            className="group inline-flex max-w-[210px] flex-col gap-0.5"
                          >
                            <span className="inline-flex items-center gap-1 text-[12px] font-medium text-foreground group-hover:text-primary">
                              {sample.accession_number}
                              <ExternalLink className="h-3 w-3 opacity-0 transition-opacity group-hover:opacity-100" />
                            </span>
                            <span className="truncate text-[11px] text-muted-foreground">
                              {sample.commercial_name}
                            </span>
                            {test ? (
                              <span className="truncate text-[10px] text-muted-foreground/80">
                                {test.name}
                              </span>
                            ) : null}
                          </Link>
                        ) : (
                          <span className="text-[12px] text-muted-foreground">—</span>
                        )}
                      </TableCell>

                      <TableCell className="max-w-[300px]">
                        <p className="truncate text-[13px] font-medium">{capa.title}</p>
                        <p className="mt-0.5 line-clamp-1 text-[11px] text-muted-foreground">
                          {capa.root_cause}
                        </p>
                      </TableCell>

                      <TableCell>
                        <div className="flex items-center gap-2">
                          <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/10 text-[10px] font-semibold text-primary">
                            {initials(capa.owner.full_name)}
                          </span>
                          <div className="min-w-0">
                            <p className="truncate text-[12px] font-medium">
                              {capa.owner.full_name}
                            </p>
                            <p className="text-[10px] text-muted-foreground">
                              {ROLE_LABELS[capa.owner.role] ?? capa.owner.role}
                            </p>
                          </div>
                        </div>
                      </TableCell>

                      <TableCell>
                        <div className="flex flex-col gap-0.5">
                          <span
                            className={cn(
                              "text-[12px] font-medium tabular-nums",
                              overdue && "text-rose-700",
                            )}
                          >
                            {formatDate(capa.due_date)}
                          </span>
                          <span
                            className={cn(
                              "text-[10px]",
                              overdue ? "text-rose-600" : "text-muted-foreground",
                            )}
                          >
                            {FINAL_STATUSES.includes(capa.status)
                              ? capa.closed_at
                                ? `encerrada ${formatDate(capa.closed_at)}`
                                : "encerrada"
                              : dueLabel(capa.due_date)}
                          </span>
                        </div>
                      </TableCell>

                      <TableCell>
                        <StatusBadge status={capa.status} kind="capa" />
                      </TableCell>

                      <TableCell className="pr-5 text-right">
                        <Button
                          variant={editable ? "outline" : "ghost"}
                          size="sm"
                          onClick={() => setSelected(capa)}
                        >
                          {editable ? "Gerenciar" : "Detalhes"}
                        </Button>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {canCreate ? (
        <NewCapaDialog
          open={newOpen}
          onOpenChange={setNewOpen}
          samples={samples}
          tests={tests}
          users={users}
          onCreated={refresh}
        />
      ) : null}

      <CapaDialog
        capa={selected}
        samples={sampleById}
        tests={testById}
        users={users}
        onOpenChange={(open) => {
          if (!open) setSelected(null);
        }}
        onUpdated={refresh}
      />
    </div>
  );
}

function SummaryTile({
  icon,
  label,
  value,
  tone,
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
  tone: "rose" | "amber" | "emerald";
}) {
  const styles = {
    rose: "border-rose-200 bg-rose-50/60 text-rose-800",
    amber: "border-amber-200 bg-amber-50/60 text-amber-900",
    emerald: "border-emerald-200 bg-emerald-50/60 text-emerald-800",
  } as const;

  return (
    <div className={cn("rounded-md border px-3 py-2.5", styles[tone])}>
      <div className="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-[0.14em] opacity-80">
        {icon}
        {label}
      </div>
      <p className="mt-1 text-2xl font-semibold tabular-nums">{value}</p>
    </div>
  );
}

function NewCapaDialog({
  open,
  onOpenChange,
  samples,
  tests,
  users,
  onCreated,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  samples: DeviceSample[];
  tests: LabTest[];
  users: UserBrief[];
  onCreated: () => void;
}) {
  const { user } = useAuth();
  const { push } = useToast();
  const { requestSignature } = useESignature();

  const [title, setTitle] = React.useState("");
  const [sampleId, setSampleId] = React.useState("");
  const [testId, setTestId] = React.useState("");
  const [rootCause, setRootCause] = React.useState("");
  const [actionPlan, setActionPlan] = React.useState("");
  const [ownerId, setOwnerId] = React.useState("");
  const [dueDate, setDueDate] = React.useState(tomorrowIso());
  const [submitting, setSubmitting] = React.useState(false);

  React.useEffect(() => {
    if (!open) return;
    setTitle("");
    setSampleId("");
    setTestId("");
    setRootCause("");
    setActionPlan("");
    setOwnerId(user?.id ?? "");
    setDueDate(tomorrowIso());
    setSubmitting(false);
  }, [open, user?.id]);

  const sample = samples.find((item) => item.id === sampleId) ?? null;
  const sampleTests = tests.filter((test) => test.device_sample_id === sampleId);
  const minimumDueDate = tomorrowIso();
  const ownerOptions = React.useMemo(
    () => users.filter((item) => isCapaOwnerRole(item.role)),
    [users],
  );

  function handleSampleChange(value: string) {
    setSampleId(value);
    setTestId("");
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();

    if (title.trim().length < 5) {
      push({ variant: "warning", title: "Informe um título com ao menos 5 caracteres." });
      return;
    }
    if (!sample) {
      push({ variant: "warning", title: "Selecione a amostra de origem." });
      return;
    }
    if (rootCause.trim().length < 10) {
      push({
        variant: "warning",
        title: "Descreva a causa raiz",
        description: "A análise de causa raiz exige ao menos 10 caracteres.",
      });
      return;
    }
    if (actionPlan.trim().length < 10) {
      push({
        variant: "warning",
        title: "Descreva o plano de ação",
        description: "O plano corretivo exige ao menos 10 caracteres.",
      });
      return;
    }
    if (!ownerId) {
      push({ variant: "warning", title: "Selecione o responsável pela CAPA." });
      return;
    }
    if (!dueDate || dueDate <= todayIso()) {
      push({ variant: "warning", title: "O prazo deve ser uma data futura." });
      return;
    }

    const id = crypto.randomUUID();
    const token = await requestSignature({
      entityType: "CapaAction",
      entityId: id,
      action: "CREATE",
      meaning: "AUTORIA",
      title: "Abrir CAPA manual",
      recordLabel: `${title.trim()} · ${sample.accession_number}`,
      description:
        "A CAPA será numerada automaticamente e vinculada à amostra selecionada.",
      suggestedReason: `Abertura manual de CAPA para a amostra ${sample.accession_number}: ${title.trim()}.`,
    });
    if (!token) return;

    setSubmitting(true);
    try {
      const response = await api.post<CapaCreateResponse>(
        "/capas",
        {
          id,
          device_sample_id: sample.id,
          lab_test_id: testId || null,
          title: title.trim(),
          root_cause: rootCause.trim(),
          action_plan: actionPlan.trim(),
          owner_id: ownerId,
          due_date: dueDate,
        },
        token,
      );
      push({
        variant: "success",
        title: "CAPA aberta",
        description: `${response.capa.code} registrada e assinada · auditoria #${response.audit_log_id}.`,
      });
      onOpenChange(false);
      onCreated();
    } catch (error) {
      push({
        variant: "destructive",
        title: "Não foi possível abrir a CAPA",
        description:
          error instanceof ApiError ? error.message : "Verifique os dados informados.",
      });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] max-w-2xl overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Abrir CAPA manual</DialogTitle>
          <DialogDescription>
            Use quando a não conformidade não for detectada automaticamente por um
            ensaio reprovado.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="grid gap-4">
          <div className="grid gap-1.5">
            <Label htmlFor="capa-title">Título *</Label>
            <Input
              id="capa-title"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="Ex.: Falha no controle de temperatura da sala de ensaios"
              maxLength={200}
              required
            />
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="grid gap-1.5">
              <Label htmlFor="capa-sample">Amostra de origem *</Label>
              <Select value={sampleId} onValueChange={handleSampleChange}>
                <SelectTrigger id="capa-sample">
                  <SelectValue placeholder="Selecione a amostra" />
                </SelectTrigger>
                <SelectContent>
                  {samples.map((item) => (
                    <SelectItem key={item.id} value={item.id}>
                      {item.accession_number} · {item.commercial_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="grid gap-1.5">
              <Label htmlFor="capa-test">Ensaio relacionado</Label>
              <Select
                value={testId}
                onValueChange={setTestId}
                disabled={!sampleId || sampleTests.length === 0}
              >
                <SelectTrigger id="capa-test">
                  <SelectValue
                    placeholder={
                      !sampleId
                        ? "Selecione a amostra primeiro"
                        : sampleTests.length === 0
                          ? "Sem ensaios cadastrados"
                          : "Opcional"
                    }
                  />
                </SelectTrigger>
                <SelectContent>
                  {sampleTests.map((test) => (
                    <SelectItem key={test.id} value={test.id}>
                      {test.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid gap-1.5">
            <Label htmlFor="capa-root-cause">Análise de causa raiz *</Label>
            <Textarea
              id="capa-root-cause"
              rows={3}
              value={rootCause}
              onChange={(event) => setRootCause(event.target.value)}
              placeholder="Descreva a causa identificada, evidências e método de análise."
              maxLength={4000}
              required
            />
          </div>

          <div className="grid gap-1.5">
            <Label htmlFor="capa-action-plan">Plano de ação *</Label>
            <Textarea
              id="capa-action-plan"
              rows={3}
              value={actionPlan}
              onChange={(event) => setActionPlan(event.target.value)}
              placeholder="Ações corretivas, responsáveis e critério de eficácia."
              maxLength={4000}
              required
            />
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="grid gap-1.5">
              <Label htmlFor="capa-owner">Responsável *</Label>
              <Select value={ownerId} onValueChange={setOwnerId}>
                <SelectTrigger id="capa-owner">
                  <SelectValue placeholder="Selecione o responsável" />
                </SelectTrigger>
                <SelectContent>
                  {ownerOptions.map((item) => (
                    <SelectItem key={item.id} value={item.id}>
                      {item.full_name} · {ROLE_LABELS[item.role] ?? item.role}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="grid gap-1.5">
              <Label htmlFor="capa-due">Prazo *</Label>
              <Input
                id="capa-due"
                type="date"
                value={dueDate}
                min={minimumDueDate}
                onChange={(event) => setDueDate(event.target.value)}
                required
              />
            </div>
          </div>

          <div className="flex items-start gap-2 rounded-md border border-dashed border-border px-3 py-2 text-[11px] leading-relaxed text-muted-foreground">
            <ShieldCheck className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary" />
            <span>
              A abertura é definitiva: o código é gerado pelo sistema e a assinatura
              registra autor, data/hora, motivo e hash do registro na trilha de
              auditoria.
            </span>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={submitting}
            >
              Cancelar
            </Button>
            <Button type="submit" disabled={submitting}>
              {submitting ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <ShieldCheck className="h-4 w-4" />
              )}
              Abrir e assinar
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function CapaDialog({
  capa,
  samples,
  tests,
  users,
  onOpenChange,
  onUpdated,
}: {
  capa: Capa | null;
  samples: Map<string, DeviceSample>;
  tests: Map<string, LabTest>;
  users: UserBrief[];
  onOpenChange: (open: boolean) => void;
  onUpdated: () => void;
}) {
  const { user } = useAuth();
  const { push } = useToast();
  const { requestSignature } = useESignature();
  const queryClient = useQueryClient();

  const [status, setStatus] = React.useState<CapaStatus>("ABERTA");
  const [ownerId, setOwnerId] = React.useState("");
  const [dueDate, setDueDate] = React.useState("");
  const [rootCause, setRootCause] = React.useState("");
  const [actionPlan, setActionPlan] = React.useState("");
  const [effectiveness, setEffectiveness] = React.useState("");
  const [submitting, setSubmitting] = React.useState(false);

  React.useEffect(() => {
    if (!capa) return;
    setStatus(capa.status);
    setOwnerId(capa.owner.id);
    setDueDate(capa.due_date);
    setRootCause(capa.root_cause);
    setActionPlan(capa.action_plan);
    setEffectiveness(capa.effectiveness_check ?? "");
    setSubmitting(false);
  }, [capa]);

  const editable = capa ? canManageCapa(capa, user) : false;

  const sample = capa?.device_sample_id ? samples.get(capa.device_sample_id) : null;
  const test = capa?.lab_test_id ? tests.get(capa.lab_test_id) : null;

  // Mantém o responsável atual visível mesmo se o perfil não for mais elegível.
  const ownerOptions = React.useMemo(() => {
    const eligible = users.filter((item) => isCapaOwnerRole(item.role));
    if (capa && !eligible.some((item) => item.id === capa.owner.id)) {
      return [...eligible, capa.owner];
    }
    return eligible;
  }, [users, capa]);

  const dirty = Boolean(
    capa &&
      (status !== capa.status ||
        ownerId !== capa.owner.id ||
        dueDate !== capa.due_date ||
        rootCause.trim() !== capa.root_cause ||
        actionPlan.trim() !== capa.action_plan ||
        effectiveness.trim() !== (capa.effectiveness_check ?? "")),
  );

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!capa) return;

    if (rootCause.trim().length < 10) {
      push({ variant: "warning", title: "A causa raiz exige ao menos 10 caracteres." });
      return;
    }
    if (actionPlan.trim().length < 10) {
      push({ variant: "warning", title: "O plano de ação exige ao menos 10 caracteres." });
      return;
    }
    if (dueDate !== capa.due_date && (!dueDate || dueDate <= todayIso())) {
      push({ variant: "warning", title: "O prazo deve ser uma data futura." });
      return;
    }
    if (status === "CONCLUIDA" && effectiveness.trim().length < 10) {
      push({
        variant: "warning",
        title: "Registre a verificação de eficácia",
        description:
          "A conclusão da CAPA exige evidência de que as ações implementadas foram eficazes.",
      });
      return;
    }
    if (!dirty) {
      push({ variant: "warning", title: "Nenhuma alteração para assinar." });
      return;
    }

    const closing = status === "CONCLUIDA";
    const cancelling = status === "CANCELADA";
    const meaning = closing ? "VERIFICACAO" : cancelling ? "APROVACAO" : "REVISAO";
    const action = closing || cancelling ? "CLOSE" : "UPDATE";

    const token = await requestSignature({
      entityType: "CapaAction",
      entityId: capa.id,
      action,
      meaning,
      title: closing
        ? "Concluir CAPA com verificação de eficácia"
        : cancelling
          ? "Cancelar CAPA"
          : "Assinar atualização da CAPA",
      recordLabel: `${capa.code} · ${capa.title}`,
      description: closing
        ? "A CAPA será encerrada e todos os campos ficarão imutáveis."
        : cancelling
          ? "A CAPA será encerrada como cancelada e ficará imutável."
          : "As alterações de plano, responsável e prazo serão gravadas na trilha de auditoria.",
      suggestedReason: closing
        ? `Conclusão da CAPA ${capa.code} após verificação de eficácia das ações implementadas.`
        : cancelling
          ? `Cancelamento da CAPA ${capa.code} com justificativa registrada.`
          : `Atualização do plano de ação, responsável e prazo da CAPA ${capa.code}.`,
    });
    if (!token) return;

    setSubmitting(true);
    try {
      const updated = await api.patch<Capa>(
        `/capas/${capa.id}`,
        {
          status,
          owner_id: ownerId,
          due_date: dueDate,
          root_cause: rootCause.trim(),
          action_plan: actionPlan.trim(),
          effectiveness_check: effectiveness.trim() || null,
          version: capa.version,
        },
        token,
      );
      push({
        variant: "success",
        title: closing ? "CAPA concluída" : cancelling ? "CAPA cancelada" : "CAPA atualizada",
        description: `${updated.code} · versão ${updated.version} assinada e auditada.`,
      });
      onOpenChange(false);
      onUpdated();
      void queryClient.invalidateQueries({ queryKey: ["audit"] });
    } catch (error) {
      push({
        variant: "destructive",
        title: "Não foi possível atualizar a CAPA",
        description:
          error instanceof ApiError ? error.message : "Verifique os dados e a versão.",
      });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog open={Boolean(capa)} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] max-w-2xl overflow-y-auto">
        {capa ? (
          <>
            <DialogHeader>
              <div className="mb-1 flex flex-wrap items-center gap-2">
                <span className="font-mono text-[11px] font-semibold text-muted-foreground">
                  {capa.code}
                </span>
                <StatusBadge status={capa.status} kind="capa" />
                {capa.auto_opened ? (
                  <Badge variant="destructive" className="gap-1 px-1.5 py-0 text-[9px]">
                    <Sparkles className="h-2.5 w-2.5" />
                    aberta por reprovação
                  </Badge>
                ) : null}
              </div>
              <DialogTitle>{capa.title}</DialogTitle>
              <DialogDescription>
                {sample
                  ? `${sample.accession_number} · ${sample.commercial_name}`
                  : "Origem não vinculada"}
                {test ? ` · ${test.name}` : ""}
              </DialogDescription>
            </DialogHeader>

            <div className="grid gap-2 rounded-md border border-border bg-muted/30 p-3 text-[12px] sm:grid-cols-2">
              <div>
                <p className="data-label">Aberta em</p>
                <p className="mt-0.5 font-medium">{formatDateTime(capa.opened_at)}</p>
              </div>
              <div>
                <p className="data-label">Prazo</p>
                <p
                  className={cn(
                    "mt-0.5 font-medium",
                    isOverdue(capa) && "text-rose-700",
                  )}
                >
                  {formatDate(capa.due_date)}
                  {FINAL_STATUSES.includes(capa.status) ? "" : ` · ${dueLabel(capa.due_date)}`}
                </p>
              </div>
              <div>
                <p className="data-label">Responsável</p>
                <p className="mt-0.5 font-medium">{capa.owner.full_name}</p>
              </div>
              <div>
                <p className="data-label">Encerramento</p>
                <p className="mt-0.5 font-medium">
                  {capa.closed_at ? formatDateTime(capa.closed_at) : "em aberto"}
                </p>
              </div>
            </div>

            {!editable ? (
              <div className="rounded-md border border-dashed border-border px-3 py-2 text-[11px] text-muted-foreground">
                {FINAL_STATUSES.includes(capa.status)
                  ? "CAPA encerrada: os registros são imutáveis e só podem ser consultados."
                  : "Somente o responsável pela CAPA ou a gestão da qualidade pode alterá-la."}
              </div>
            ) : null}

            <form onSubmit={handleSubmit} className="grid gap-4">
              <div className="grid gap-4 sm:grid-cols-3">
                <div className="grid gap-1.5">
                  <Label htmlFor="manage-status">Status</Label>
                  <Select
                    value={status}
                    onValueChange={(value) => setStatus(value as CapaStatus)}
                    disabled={!editable}
                  >
                    <SelectTrigger id="manage-status">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {STATUS_OPTIONS.map((option) => (
                        <SelectItem key={option} value={option}>
                          {CAPA_STATUS_LABELS[option]}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="grid gap-1.5">
                  <Label htmlFor="manage-owner">Responsável</Label>
                  <Select
                    value={ownerId}
                    onValueChange={setOwnerId}
                    disabled={!editable}
                  >
                    <SelectTrigger id="manage-owner">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {ownerOptions.map((item) => (
                        <SelectItem key={item.id} value={item.id}>
                          {item.full_name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="grid gap-1.5">
                  <Label htmlFor="manage-due">Prazo</Label>
                  <Input
                    id="manage-due"
                    type="date"
                    value={dueDate}
                    onChange={(event) => setDueDate(event.target.value)}
                    disabled={!editable}
                  />
                </div>
              </div>

              <div className="grid gap-1.5">
                <Label htmlFor="manage-root-cause">Causa raiz</Label>
                <Textarea
                  id="manage-root-cause"
                  rows={3}
                  value={rootCause}
                  onChange={(event) => setRootCause(event.target.value)}
                  readOnly={!editable}
                  className={cn(!editable && "bg-muted/40")}
                  maxLength={4000}
                />
              </div>

              <div className="grid gap-1.5">
                <Label htmlFor="manage-action-plan">Plano de ação</Label>
                <Textarea
                  id="manage-action-plan"
                  rows={3}
                  value={actionPlan}
                  onChange={(event) => setActionPlan(event.target.value)}
                  readOnly={!editable}
                  className={cn(!editable && "bg-muted/40")}
                  maxLength={4000}
                />
              </div>

              <div className="grid gap-1.5">
                <Label htmlFor="manage-effectiveness">
                  Verificação de eficácia
                  {status === "CONCLUIDA" ? " *" : ""}
                </Label>
                <Textarea
                  id="manage-effectiveness"
                  rows={3}
                  value={effectiveness}
                  onChange={(event) => setEffectiveness(event.target.value)}
                  readOnly={!editable}
                  className={cn(!editable && "bg-muted/40")}
                  placeholder="Evidência objetiva de que a ação eliminou a causa raiz (obrigatória para concluir)."
                  maxLength={4000}
                />
              </div>

              {editable && status === "CONCLUIDA" ? (
                <div className="flex items-start gap-2 rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-[12px] text-emerald-950">
                  <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
                  <span>
                    Ao assinar, a CAPA será encerrada como concluída e o registro ficará
                    imutável.
                  </span>
                </div>
              ) : null}

              {editable && status === "CANCELADA" ? (
                <div className="flex items-start gap-2 rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-[12px] text-rose-950">
                  <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0" />
                  <span>
                    O cancelamento encerra a CAPA sem verificação de eficácia. Use apenas
                    quando a abertura for improcedente, registrando a justificativa.
                  </span>
                </div>
              ) : null}

              {editable ? (
                <DialogFooter>
                  <span className="mr-auto hidden items-center gap-1 text-[11px] text-muted-foreground sm:flex">
                    <CalendarClock className="h-3 w-3" />
                    versão atual v{capa.version}
                  </span>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => onOpenChange(false)}
                    disabled={submitting}
                  >
                    Fechar
                  </Button>
                  <Button type="submit" disabled={submitting || !dirty}>
                    {submitting ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <ShieldCheck className="h-4 w-4" />
                    )}
                    {status === "CONCLUIDA"
                      ? "Concluir e assinar"
                      : status === "CANCELADA"
                        ? "Cancelar e assinar"
                        : "Salvar e assinar"}
                  </Button>
                </DialogFooter>
              ) : (
                <DialogFooter>
                  <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                    Fechar
                  </Button>
                </DialogFooter>
              )}
            </form>
          </>
        ) : null}
      </DialogContent>
    </Dialog>
  );
}
