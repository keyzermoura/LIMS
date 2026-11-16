import * as React from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Activity,
  AlertOctagon,
  CalendarClock,
  CheckCircle2,
  ClipboardCheck,
  ClipboardList,
  ExternalLink,
  HelpCircle,
  History,
  Loader2,
  Plus,
  Search,
  ShieldCheck,
  Sigma,
  Sparkles,
  Target,
  Timer,
  Trash2,
  TriangleAlert,
  Workflow,
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
import { api, ApiError, capasApi } from "@/lib/api";
import type {
  Capa,
  CapaActionItem,
  CapaActionType,
  CapaEffectivenessStatus,
  CapaItemStatus,
  CapaSourceType,
  CapaStatus,
  DeviceSample,
  FiveWhysItem,
  IshikawaCauses,
  LabTest,
  Page,
  UserBrief,
  UserRole,
} from "@/lib/types";
import {
  CAPA_ACTION_TYPE_LABELS,
  CAPA_EFFECTIVENESS_STATUS_LABELS,
  CAPA_ITEM_STATUS_LABELS,
  CAPA_SOURCE_LABELS,
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

const SOURCE_OPTIONS: CapaSourceType[] = [
  "ENSAIO_REPROVADO",
  "INCERTEZA_METROLOGICA",
  "EQUIPAMENTO_DESVIO",
  "AUDITORIA_INTERNA",
  "RECLAMACAO_CLIENTE",
  "CONTROLE_QUALIDADE",
  "OUTRO",
];

const FINAL_STATUSES: CapaStatus[] = ["CONCLUIDA", "CANCELADA"];
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

function futureIso(days: number): string {
  const date = new Date();
  date.setDate(date.getDate() + days);
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
  const [selectedId, setSelectedId] = React.useState<string | null>(null);

  const statusFilter = (searchParams.get("status") ?? ALL) as CapaStatus | typeof ALL;
  const sourceFilter = (searchParams.get("source") ?? ALL) as CapaSourceType | typeof ALL;
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

  const selectedQuery = useQuery({
    queryKey: ["capas", selectedId],
    queryFn: () => (selectedId ? capasApi.get(selectedId) : null),
    enabled: Boolean(selectedId),
  });

  const capas = capasQuery.data?.items ?? [];
  const samples = samplesQuery.data?.items ?? [];
  const tests = testsQuery.data?.items ?? [];
  const users = usersQuery.data ?? [];
  const selectedCapa = selectedQuery.data ?? null;

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
    const metrology = capas.filter((capa) => capa.source_type === "INCERTEZA_METROLOGICA").length;
    const awaitingEff = capas.filter((capa) => capa.effectiveness_status === "PENDENTE" && capa.status !== "CANCELADA").length;
    return { open, inProgress, overdue, closed, metrology, awaitingEff };
  }, [capas]);

  const filtered = React.useMemo(() => {
    const term = search.trim().toLowerCase();
    return capas.filter((capa) => {
      if (statusFilter !== ALL && capa.status !== statusFilter) return false;
      if (sourceFilter !== ALL && capa.source_type !== sourceFilter) return false;
      if (sampleFilter !== ALL && capa.device_sample_id !== sampleFilter) return false;
      if (!term) return true;
      return [capa.code, capa.title, capa.root_cause, capa.action_plan, capa.owner.full_name]
        .join(" ")
        .toLowerCase()
        .includes(term);
    });
  }, [capas, statusFilter, sourceFilter, sampleFilter, search]);

  const filtersActive =
    statusFilter !== ALL || sourceFilter !== ALL || sampleFilter !== ALL || search.trim() !== "";

  function updateFilter(key: "status" | "source" | "sample", value: string) {
    const next = new URLSearchParams(searchParams);
    if (value === ALL) next.delete(key);
    else next.set(key, value);
    setSearchParams(next, { replace: true });
  }

  function clearFilters() {
    setSearch("");
    setSearchParams(new URLSearchParams(), { replace: true });
  }

  function handleCapaCreated(created: Capa) {
    void queryClient.invalidateQueries({ queryKey: ["capas"] });
    setSelectedId(created.id);
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight">Gestão de Não Conformidades & CAPA</h1>
            <Badge variant="outline" className="border-indigo-300 bg-indigo-50 text-indigo-700">
              ISO/IEC 17025 §8.7
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground">
            Investigação estruturada de causa raiz (Ishikawa 6Ms / 5 Porquês), ações 5W2H e verificação formal de eficácia temporal.
          </p>
        </div>
        {canCreate ? (
          <Button onClick={() => setNewOpen(true)} className="gap-2 shrink-0">
            <Plus className="h-4 w-4" />
            Nova Não Conformidade
          </Button>
        ) : null}
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-6">
        <Card className="border-blue-200/70 bg-blue-50/20">
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center justify-between text-xs font-medium text-blue-700">
              <span>Abertas</span>
              <AlertOctagon className="h-4 w-4" />
            </CardDescription>
            <CardTitle className="text-2xl font-bold text-blue-900">{stats.open}</CardTitle>
          </CardHeader>
          <CardContent className="text-[11px] text-muted-foreground">Aguardando investigação</CardContent>
        </Card>

        <Card className="border-amber-200/70 bg-amber-50/20">
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center justify-between text-xs font-medium text-amber-700">
              <span>Em Andamento</span>
              <Timer className="h-4 w-4" />
            </CardDescription>
            <CardTitle className="text-2xl font-bold text-amber-900">{stats.inProgress}</CardTitle>
          </CardHeader>
          <CardContent className="text-[11px] text-muted-foreground">Ações em execução</CardContent>
        </Card>

        <Card className="border-purple-200/70 bg-purple-50/20">
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center justify-between text-xs font-medium text-purple-700">
              <span>Desvios GUM</span>
              <Sigma className="h-4 w-4" />
            </CardDescription>
            <CardTitle className="text-2xl font-bold text-purple-900">{stats.metrology}</CardTitle>
          </CardHeader>
          <CardContent className="text-[11px] text-muted-foreground">Incerteza não conforme</CardContent>
        </Card>

        <Card className="border-indigo-200/70 bg-indigo-50/20">
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center justify-between text-xs font-medium text-indigo-700">
              <span>Aval. Eficácia</span>
              <Target className="h-4 w-4" />
            </CardDescription>
            <CardTitle className="text-2xl font-bold text-indigo-900">{stats.awaitingEff}</CardTitle>
          </CardHeader>
          <CardContent className="text-[11px] text-muted-foreground">ISO 17025 §8.7.3</CardContent>
        </Card>

        <Card className="border-rose-200/70 bg-rose-50/20">
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center justify-between text-xs font-medium text-rose-700">
              <span>Em Atraso</span>
              <CalendarClock className="h-4 w-4" />
            </CardDescription>
            <CardTitle className="text-2xl font-bold text-rose-900">{stats.overdue}</CardTitle>
          </CardHeader>
          <CardContent className="text-[11px] text-muted-foreground">Prazo expirado</CardContent>
        </Card>

        <Card className="border-emerald-200/70 bg-emerald-50/20">
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center justify-between text-xs font-medium text-emerald-700">
              <span>Concluídas</span>
              <CheckCircle2 className="h-4 w-4" />
            </CardDescription>
            <CardTitle className="text-2xl font-bold text-emerald-900">{stats.closed}</CardTitle>
          </CardHeader>
          <CardContent className="text-[11px] text-muted-foreground">Eficazes e encerradas</CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="relative flex-1">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Buscar por código, título, causa raiz, plano ou responsável..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-8 text-sm"
              />
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Select
                value={statusFilter}
                onValueChange={(val) => updateFilter("status", val)}
              >
                <SelectTrigger className="w-[160px] text-xs">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Todos os status</SelectItem>
                  {STATUS_OPTIONS.map((st) => (
                    <SelectItem key={st} value={st}>
                      {CAPA_STATUS_LABELS[st]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select
                value={sourceFilter}
                onValueChange={(val) => updateFilter("source", val)}
              >
                <SelectTrigger className="w-[180px] text-xs">
                  <SelectValue placeholder="Origem" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Todas as origens</SelectItem>
                  {SOURCE_OPTIONS.map((src) => (
                    <SelectItem key={src} value={src}>
                      {CAPA_SOURCE_LABELS[src]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {filtersActive ? (
                <Button variant="ghost" size="sm" onClick={clearFilters} className="text-xs">
                  Limpar
                </Button>
              ) : null}
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[130px]">Código</TableHead>
                  <TableHead>Título & Detalhes</TableHead>
                  <TableHead>Origem</TableHead>
                  <TableHead>Responsável</TableHead>
                  <TableHead>Prazo</TableHead>
                  <TableHead>Ações</TableHead>
                  <TableHead>Eficácia</TableHead>
                  <TableHead className="text-right">Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {capasQuery.isLoading ? (
                  <TableRow>
                    <TableCell colSpan={8} className="py-8 text-center text-muted-foreground">
                      <Loader2 className="mx-auto h-5 w-5 animate-spin" />
                      Carregando não conformidades...
                    </TableCell>
                  </TableRow>
                ) : filtered.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8} className="py-10 text-center text-muted-foreground">
                      Nenhuma não conformidade encontrada com os filtros atuais.
                    </TableCell>
                  </TableRow>
                ) : (
                  filtered.map((capa) => {
                    const sample = capa.device_sample_id ? sampleById.get(capa.device_sample_id) : null;
                    const test = capa.lab_test_id ? testById.get(capa.lab_test_id) : null;
                    const completedActions = capa.action_items?.filter((i) => i.status === "CONCLUIDA").length ?? 0;
                    const totalActions = capa.action_items?.length ?? 0;

                    return (
                      <TableRow
                        key={capa.id}
                        onClick={() => setSelectedId(capa.id)}
                        className="cursor-pointer hover:bg-muted/50"
                      >
                        <TableCell className="font-mono text-xs font-semibold text-primary">
                          {capa.code}
                        </TableCell>
                        <TableCell>
                          <div className="font-medium text-sm text-foreground">{capa.title}</div>
                          <div className="flex flex-wrap items-center gap-1.5 text-[11px] text-muted-foreground">
                            {sample ? (
                              <span>{sample.commercial_name} ({sample.accession_number})</span>
                            ) : null}
                            {test ? <span>· Ensaio: {test.name}</span> : null}
                            {capa.auto_opened ? (
                              <Badge variant="secondary" className="px-1 py-0 text-[10px]">
                                Automática
                              </Badge>
                            ) : null}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline" className="text-[11px] font-normal">
                            {CAPA_SOURCE_LABELS[capa.source_type] ?? capa.source_type}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-xs">{capa.owner.full_name}</TableCell>
                        <TableCell className="text-xs">
                          <span className={cn(isOverdue(capa) && "font-semibold text-rose-600")}>
                            {formatDate(capa.due_date)}
                          </span>
                        </TableCell>
                        <TableCell className="text-xs">
                          {totalActions > 0 ? (
                            <span className="font-mono text-[11px]">
                              {completedActions}/{totalActions} concluídas
                            </span>
                          ) : (
                            <span className="text-muted-foreground text-[11px]">Sem itens</span>
                          )}
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant="secondary"
                            className={cn(
                              "text-[10px]",
                              capa.effectiveness_status === "EFICAZ" && "bg-emerald-100 text-emerald-800",
                              capa.effectiveness_status === "INEFICAZ" && "bg-rose-100 text-rose-800",
                              capa.effectiveness_status === "PENDENTE" && "bg-amber-100 text-amber-800",
                            )}
                          >
                            {CAPA_EFFECTIVENESS_STATUS_LABELS[capa.effectiveness_status] ?? capa.effectiveness_status}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          <StatusBadge status={capa.status} kind="capa" />
                        </TableCell>
                      </TableRow>
                    );
                  })
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      <CapaCreateDialog
        open={newOpen}
        onOpenChange={setNewOpen}
        samples={samples}
        tests={tests}
        users={users}
        onCreated={handleCapaCreated}
      />

      {selectedCapa ? (
        <CapaDetailDialog
          capa={selectedCapa}
          open={Boolean(selectedId)}
          onOpenChange={(open) => {
            if (!open) setSelectedId(null);
          }}
          samples={samples}
          tests={tests}
          users={users}
          onUpdated={() => {
            void queryClient.invalidateQueries({ queryKey: ["capas"] });
            if (selectedId) {
              void queryClient.invalidateQueries({ queryKey: ["capas", selectedId] });
            }
          }}
        />
      ) : null}
    </div>
  );
}

// -------------------------------------------------------------------------------------
// Componente de Criação de CAPA com RCA estruturada
// -------------------------------------------------------------------------------------
interface CapaCreateDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  samples: DeviceSample[];
  tests: LabTest[];
  users: UserBrief[];
  onCreated: (capa: Capa) => void;
}

function CapaCreateDialog({
  open,
  onOpenChange,
  samples,
  tests,
  users,
  onCreated,
}: CapaCreateDialogProps) {
  const { push } = useToast();
  const { user } = useAuth();
  const { requestSignature } = useESignature();

  const [sourceType, setSourceType] = React.useState<CapaSourceType>("AUDITORIA_INTERNA");
  const [title, setTitle] = React.useState("");
  const [sampleId, setSampleId] = React.useState<string>("");
  const [testId, setTestId] = React.useState<string>("");
  const [containment, setContainment] = React.useState("");
  const [rootCause, setRootCause] = React.useState("");
  const [actionPlan, setActionPlan] = React.useState("");
  const [ownerId, setOwnerId] = React.useState<string>(user?.id ?? "");
  const [dueDate, setDueDate] = React.useState<string>(futureIso(30));
  const [effDate, setEffDate] = React.useState<string>(futureIso(60));
  const [submitting, setSubmitting] = React.useState(false);

  // 5 Porquês estruturados no cadastro
  const [why1, setWhy1] = React.useState("");
  const [why2, setWhy2] = React.useState("");
  const [why3, setWhy3] = React.useState("");
  const [why4, setWhy4] = React.useState("");
  const [why5, setWhy5] = React.useState("");

  const sampleTests = React.useMemo(() => {
    if (!sampleId) return [];
    return tests.filter((t) => t.device_sample_id === sampleId);
  }, [sampleId, tests]);

  const ownerOptions = React.useMemo(
    () => users.filter((u) => isCapaOwnerRole(u.role)),
    [users],
  );

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!sampleId && !testId) {
      push({ variant: "warning", title: "Selecione a amostra de origem." });
      return;
    }
    if (title.trim().length < 5) {
      push({ variant: "warning", title: "O título deve ter no mínimo 5 caracteres." });
      return;
    }
    if (rootCause.trim().length < 10) {
      push({ variant: "warning", title: "A análise de causa raiz exige ao menos 10 caracteres." });
      return;
    }
    if (actionPlan.trim().length < 10) {
      push({ variant: "warning", title: "O plano de ação exige ao menos 10 caracteres." });
      return;
    }
    if (!dueDate || dueDate <= todayIso()) {
      push({ variant: "warning", title: "O prazo deve ser uma data futura." });
      return;
    }

    const fiveWhysList: FiveWhysItem[] = [];
    if (why1.trim()) fiveWhysList.push({ why_number: 1, question: "Por que ocorreu o desvio inicial?", answer: why1.trim() });
    if (why2.trim()) fiveWhysList.push({ why_number: 2, question: "Por que a condição do desvio existia?", answer: why2.trim() });
    if (why3.trim()) fiveWhysList.push({ why_number: 3, question: "Por que o controle não detectou?", answer: why3.trim() });
    if (why4.trim()) fiveWhysList.push({ why_number: 4, question: "Por que o procedimento falhou?", answer: why4.trim() });
    if (why5.trim()) fiveWhysList.push({ why_number: 5, question: "Causa fundamental do sistema?", answer: why5.trim() });

    const capaId = crypto.randomUUID();

    const sigToken = await requestSignature({
      entityType: "CapaAction",
      entityId: capaId,
      action: "CREATE",
      meaning: "APROVACAO",
      title: "Assinar Abertura de Não Conformidade (CAPA)",
      recordLabel: title.trim(),
      description: "Abertura formal de CAPA e análise de causa raiz com assinatura 21 CFR Part 11.",
      suggestedReason: `Abertura formal de CAPA (${CAPA_SOURCE_LABELS[sourceType]}): ${title.trim()}`,
    });

    if (!sigToken) return;

    setSubmitting(true);
    try {
      const res = await capasApi.create(
        {
          id: capaId,
          device_sample_id: sampleId || null,
          lab_test_id: testId || null,
          source_type: sourceType,
          title: title.trim(),
          containment_action: containment.trim() || null,
          five_whys: fiveWhysList.length > 0 ? fiveWhysList : null,
          root_cause: rootCause.trim(),
          action_plan: actionPlan.trim(),
          owner_id: ownerId,
          due_date: dueDate,
          target_effectiveness_date: effDate || null,
        },
        sigToken,
      );

      push({
        variant: "success",
        title: "Não conformidade aberta com sucesso",
        description: `Código gerado: ${res.capa.code}.`,
      });
      onOpenChange(false);
      onCreated(res.capa);
    } catch (err) {
      push({
        variant: "destructive",
        title: "Falha ao registrar CAPA",
        description: err instanceof ApiError ? err.message : "Verifique os dados preenchidos.",
      });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[92vh] max-w-3xl overflow-y-auto">
        <form onSubmit={handleSubmit} className="space-y-4">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <ClipboardCheck className="h-5 w-5 text-primary" />
              Abertura de Não Conformidade & CAPA
            </DialogTitle>
            <DialogDescription>
              Registro regulatório formal de desvio, contenção de risco e análise causal estruturada (ISO 17025 §8.7).
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <Label htmlFor="source-type">Origem da Não Conformidade *</Label>
              <Select
                value={sourceType}
                onValueChange={(val) => setSourceType(val as CapaSourceType)}
              >
                <SelectTrigger id="source-type" className="mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {SOURCE_OPTIONS.map((src) => (
                    <SelectItem key={src} value={src}>
                      {CAPA_SOURCE_LABELS[src]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="owner-id">Responsável pela CAPA *</Label>
              <Select value={ownerId} onValueChange={setOwnerId}>
                <SelectTrigger id="owner-id" className="mt-1">
                  <SelectValue placeholder="Selecione o responsável" />
                </SelectTrigger>
                <SelectContent>
                  {ownerOptions.map((u) => (
                    <SelectItem key={u.id} value={u.id}>
                      {u.full_name} ({ROLE_LABELS[u.role] ?? u.role})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div>
            <Label htmlFor="capa-title">Título Resumido do Desvio *</Label>
            <Input
              id="capa-title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Ex: Deriva no sensor térmico da estufa de secagem durante ensaio de umidade"
              required
              className="mt-1"
            />
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <Label htmlFor="capa-sample">Amostra Vinculada *</Label>
              <Select value={sampleId} onValueChange={(val) => { setSampleId(val); setTestId(""); }}>
                <SelectTrigger id="capa-sample" className="mt-1">
                  <SelectValue placeholder="Selecione a amostra" />
                </SelectTrigger>
                <SelectContent>
                  {samples.map((s) => (
                    <SelectItem key={s.id} value={s.id}>
                      {s.accession_number} · {s.commercial_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="capa-test">Ensaio Relacionado (Opcional)</Label>
              <Select value={testId} onValueChange={setTestId} disabled={!sampleId}>
                <SelectTrigger id="capa-test" className="mt-1">
                  <SelectValue placeholder={!sampleId ? "Selecione a amostra primeiro" : "Ensaio opcional"} />
                </SelectTrigger>
                <SelectContent>
                  {sampleTests.map((t) => (
                    <SelectItem key={t.id} value={t.id}>
                      {t.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="rounded-md border border-amber-200 bg-amber-50/50 p-3">
            <Label htmlFor="containment" className="font-semibold text-amber-900">
              Ação de Contenção Imediata (Segregação de Risco)
            </Label>
            <Textarea
              id="containment"
              value={containment}
              onChange={(e) => setContainment(e.target.value)}
              placeholder="Ex: Amostra segregada em quarentena; equipamento fora de serviço até calibração."
              rows={2}
              className="mt-1 text-sm bg-white"
            />
          </div>

          <div className="rounded-md border p-3 bg-muted/20">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2 flex items-center gap-1.5">
              <Workflow className="h-3.5 w-3.5" /> Metodologia dos 5 Porquês (Análise Causal Guiada)
            </h4>
            <div className="space-y-2">
              <Input
                placeholder="1º Porquê: Por que ocorreu o sintoma inicial?"
                value={why1}
                onChange={(e) => setWhy1(e.target.value)}
                className="text-xs bg-white"
              />
              <Input
                placeholder="2º Porquê: Por que essa condição ocorreu?"
                value={why2}
                onChange={(e) => setWhy2(e.target.value)}
                className="text-xs bg-white"
              />
              <Input
                placeholder="3º Porquê: Por que não foi evitado preventivamente?"
                value={why3}
                onChange={(e) => setWhy3(e.target.value)}
                className="text-xs bg-white"
              />
              <Input
                placeholder="4º Porquê: Por que o procedimento permitiu?"
                value={why4}
                onChange={(e) => setWhy4(e.target.value)}
                className="text-xs bg-white"
              />
              <Input
                placeholder="5º Porquê: Causa raiz fundamental do sistema de qualidade?"
                value={why5}
                onChange={(e) => setWhy5(e.target.value)}
                className="text-xs bg-white font-medium text-primary"
              />
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <Label htmlFor="root-cause">Causa Raiz Formal *</Label>
              <Textarea
                id="root-cause"
                value={rootCause}
                onChange={(e) => setRootCause(e.target.value)}
                placeholder="Conclusão formal da causa raiz identificada..."
                rows={3}
                required
                className="mt-1 text-sm"
              />
            </div>
            <div>
              <Label htmlFor="action-plan">Plano de Ação Corretiva Macro *</Label>
              <Textarea
                id="action-plan"
                value={actionPlan}
                onChange={(e) => setActionPlan(e.target.value)}
                placeholder="Estratégia de eliminação definitiva da causa raiz..."
                rows={3}
                required
                className="mt-1 text-sm"
              />
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <Label htmlFor="due-date">Prazo para Conclusão do Plano *</Label>
              <Input
                id="due-date"
                type="date"
                value={dueDate}
                min={todayIso()}
                onChange={(e) => setDueDate(e.target.value)}
                required
                className="mt-1"
              />
            </div>
            <div>
              <Label htmlFor="eff-date">Data Alvo de Avaliação de Eficácia</Label>
              <Input
                id="eff-date"
                type="date"
                value={effDate}
                min={dueDate}
                onChange={(e) => setEffDate(e.target.value)}
                className="mt-1"
              />
            </div>
          </div>

          <DialogFooter className="pt-2">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={submitting} className="gap-2">
              {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <ShieldCheck className="h-4 w-4" />}
              Assinar & Abrir Não Conformidade
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// -------------------------------------------------------------------------------------
// Componente de Detalhes, Investigação Ishikawa, Ações e Eficácia Temporal
// -------------------------------------------------------------------------------------
interface CapaDetailDialogProps {
  capa: Capa;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  samples: DeviceSample[];
  tests: LabTest[];
  users: UserBrief[];
  onUpdated: () => void;
}

type TabKey = "overview" | "ishikawa" | "five_whys" | "actions" | "effectiveness";

function CapaDetailDialog({
  capa,
  open,
  onOpenChange,
  samples,
  tests,
  users,
  onUpdated,
}: CapaDetailDialogProps) {
  const { user } = useAuth();
  const { push } = useToast();
  const { requestSignature } = useESignature();

  const [activeTab, setActiveTab] = React.useState<TabKey>("overview");

  // Formulário de novo item de ação
  const [newActionTitle, setNewActionTitle] = React.useState("");
  const [newActionDesc, setNewActionDesc] = React.useState("");
  const [newActionType, setNewActionType] = React.useState<CapaActionType>("CORRETIVA");
  const [newActionAssignee, setNewActionAssignee] = React.useState(user?.id ?? "");
  const [newActionDue, setNewActionDue] = React.useState(futureIso(15));
  const [addingAction, setAddingAction] = React.useState(false);

  // Conclusão de item de ação
  const [completingItemId, setCompletingItemId] = React.useState<string | null>(null);
  const [completionEvidence, setCompletionEvidence] = React.useState("");

  // Avaliação de Eficácia Temporal
  const [effStatus, setEffStatus] = React.useState<CapaEffectivenessStatus>("EFICAZ");
  const [recurrence, setRecurrence] = React.useState(false);
  const [effJustification, setEffJustification] = React.useState("");
  const [evaluatingEff, setEvaluatingEff] = React.useState(false);

  const sample = capa.device_sample_id ? samples.find((s) => s.id === capa.device_sample_id) : null;
  const test = capa.lab_test_id ? tests.find((t) => t.id === capa.lab_test_id) : null;
  const isFinal = FINAL_STATUSES.includes(capa.status);
  const canManage = canManageCapa(capa, user);

  // Adicionar ação
  async function handleAddActionItem(e: React.FormEvent) {
    e.preventDefault();
    if (!newActionTitle.trim() || !newActionDesc.trim()) {
      push({ variant: "warning", title: "Informe o título e descrição da ação." });
      return;
    }
    setAddingAction(true);
    try {
      await capasApi.addActionItem(capa.id, {
        title: newActionTitle.trim(),
        description: newActionDesc.trim(),
        action_type: newActionType,
        assigned_to_id: newActionAssignee,
        due_date: newActionDue,
      });
      push({ variant: "success", title: "Ação adicionada ao plano com sucesso." });
      setNewActionTitle("");
      setNewActionDesc("");
      onUpdated();
    } catch (err) {
      push({
        variant: "destructive",
        title: "Erro ao incluir ação",
        description: err instanceof ApiError ? err.message : "Erro desconhecido.",
      });
    } finally {
      setAddingAction(false);
    }
  }

  // Concluir ação com evidência
  async function handleCompleteAction(itemId: string) {
    if (!completionEvidence.trim()) {
      push({ variant: "warning", title: "Informe a evidência de conclusão da ação." });
      return;
    }
    try {
      await capasApi.updateActionItem(capa.id, itemId, {
        status: "CONCLUIDA",
        completion_evidence: completionEvidence.trim(),
      });
      push({ variant: "success", title: "Ação marcada como concluída." });
      setCompletingItemId(null);
      setCompletionEvidence("");
      onUpdated();
    } catch (err) {
      push({
        variant: "destructive",
        title: "Erro ao concluir ação",
        description: err instanceof ApiError ? err.message : "Erro desconhecido.",
      });
    }
  }

  // Avaliar Eficácia Temporal com assinatura
  async function handleEvaluateEffectiveness(e: React.FormEvent) {
    e.preventDefault();
    if (effJustification.trim().length < 10) {
      push({ variant: "warning", title: "A justificativa exige no mínimo 10 caracteres." });
      return;
    }

    const sigToken = await requestSignature({
      entityType: "CapaAction",
      entityId: capa.id,
      action: "UPDATE",
      meaning: "VERIFICACAO",
      title: "Assinar Avaliação Formal de Eficácia (ISO 17025 §8.7.3)",
      recordLabel: `${capa.code} · ${capa.title}`,
      description: `Registro formal de verificação temporal de eficácia: ${CAPA_EFFECTIVENESS_STATUS_LABELS[effStatus]}.`,
      suggestedReason: `Avaliação de eficácia da CAPA ${capa.code} (${CAPA_EFFECTIVENESS_STATUS_LABELS[effStatus]}).`,
    });

    if (!sigToken) return;

    setEvaluatingEff(true);
    try {
      await capasApi.evaluateEffectiveness(
        capa.id,
        {
          effectiveness_status: effStatus,
          recurrence_detected: recurrence,
          justification: effJustification.trim(),
        },
        sigToken,
      );

      push({
        variant: "success",
        title: "Eficácia temporal avaliada e assinada",
        description:
          effStatus === "EFICAZ"
            ? "A CAPA foi encerrada como eficaz com sucesso."
            : "Ineficácia registrada: uma nova CAPA de reincidência foi disparada automaticamente.",
      });
      onUpdated();
    } catch (err) {
      push({
        variant: "destructive",
        title: "Erro ao avaliar eficácia",
        description: err instanceof ApiError ? err.message : "Verifique as pendências.",
      });
    } finally {
      setEvaluatingEff(false);
    }
  }

  const pendingActionsCount = capa.action_items?.filter(
    (i) => i.status === "PENDENTE" || i.status === "EM_ANDAMENTO",
  ).length ?? 0;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[92vh] max-w-4xl overflow-y-auto">
        <DialogHeader>
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-mono text-xs font-semibold text-muted-foreground">{capa.code}</span>
            <StatusBadge status={capa.status} kind="capa" />
            <Badge variant="outline">{CAPA_SOURCE_LABELS[capa.source_type] ?? capa.source_type}</Badge>
            {capa.recurrence_detected ? (
              <Badge variant="destructive" className="text-[10px]">Reincidência</Badge>
            ) : null}
          </div>
          <DialogTitle className="text-xl">{capa.title}</DialogTitle>
          <DialogDescription>
            {sample ? `${sample.accession_number} · ${sample.commercial_name}` : "Sem amostra vinculada"}
            {test ? ` · Ensaio: ${test.name}` : ""}
          </DialogDescription>
        </DialogHeader>

        {/* Barra de Abas */}
        <div className="flex flex-wrap gap-1 border-b pb-2">
          <Button
            type="button"
            size="sm"
            variant={activeTab === "overview" ? "default" : "outline"}
            onClick={() => setActiveTab("overview")}
            className="text-xs gap-1.5"
          >
            <ClipboardList className="h-3.5 w-3.5" /> Visão Geral & Contenção
          </Button>
          <Button
            type="button"
            size="sm"
            variant={activeTab === "ishikawa" ? "default" : "outline"}
            onClick={() => setActiveTab("ishikawa")}
            className="text-xs gap-1.5"
          >
            <Activity className="h-3.5 w-3.5" /> Ishikawa (6Ms)
          </Button>
          <Button
            type="button"
            size="sm"
            variant={activeTab === "five_whys" ? "default" : "outline"}
            onClick={() => setActiveTab("five_whys")}
            className="text-xs gap-1.5"
          >
            <HelpCircle className="h-3.5 w-3.5" /> 5 Porquês (RCA)
          </Button>
          <Button
            type="button"
            size="sm"
            variant={activeTab === "actions" ? "default" : "outline"}
            onClick={() => setActiveTab("actions")}
            className="text-xs gap-1.5"
          >
            <Target className="h-3.5 w-3.5" /> Itens de Ação ({capa.action_items?.length ?? 0})
          </Button>
          <Button
            type="button"
            size="sm"
            variant={activeTab === "effectiveness" ? "default" : "outline"}
            onClick={() => setActiveTab("effectiveness")}
            className="text-xs gap-1.5"
          >
            <ShieldCheck className="h-3.5 w-3.5" /> Avaliação de Eficácia
          </Button>
        </div>

        {/* Conteúdo das Abas */}
        {activeTab === "overview" ? (
          <div className="space-y-4 pt-2">
            <div className="grid gap-3 sm:grid-cols-4 rounded-md border bg-muted/20 p-3 text-xs">
              <div>
                <p className="text-muted-foreground font-medium">Aberta em</p>
                <p className="mt-0.5 font-semibold">{formatDateTime(capa.opened_at)}</p>
              </div>
              <div>
                <p className="text-muted-foreground font-medium">Prazo do Plano</p>
                <p className={cn("mt-0.5 font-semibold", isOverdue(capa) && "text-rose-600")}>
                  {formatDate(capa.due_date)} ({dueLabel(capa.due_date)})
                </p>
              </div>
              <div>
                <p className="text-muted-foreground font-medium">Responsável</p>
                <p className="mt-0.5 font-semibold">{capa.owner.full_name}</p>
              </div>
              <div>
                <p className="text-muted-foreground font-medium">Encerramento</p>
                <p className="mt-0.5 font-semibold">{capa.closed_at ? formatDateTime(capa.closed_at) : "Em aberto"}</p>
              </div>
            </div>

            {capa.containment_action ? (
              <div className="rounded-md border border-amber-300 bg-amber-50/60 p-3.5">
                <h4 className="text-xs font-bold text-amber-900 uppercase tracking-wider flex items-center gap-1.5">
                  <TriangleAlert className="h-4 w-4" /> Ação de Contenção Imediata (Segregação de Risco)
                </h4>
                <p className="mt-1 text-xs text-amber-800 leading-relaxed">{capa.containment_action}</p>
              </div>
            ) : null}

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="rounded-md border p-3">
                <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">
                  Causa Raiz Identificada
                </h4>
                <p className="text-xs leading-relaxed text-foreground whitespace-pre-wrap">{capa.root_cause}</p>
              </div>
              <div className="rounded-md border p-3">
                <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">
                  Plano de Ação Corretiva
                </h4>
                <p className="text-xs leading-relaxed text-foreground whitespace-pre-wrap">{capa.action_plan}</p>
              </div>
            </div>
          </div>
        ) : null}

        {activeTab === "ishikawa" ? (
          <div className="space-y-4 pt-2">
            <div className="rounded-md border bg-indigo-50/30 p-3 text-xs text-indigo-900">
              <p className="font-semibold">Diagrama de Causa e Efeito (Ishikawa 6Ms — ISO/IEC 17025 §8.7)</p>
              <p className="mt-0.5 text-muted-foreground">
                Mapeamento das causas primárias agrupadas nas dimensões laboratoriais.
              </p>
            </div>

            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {[
                { key: "metodo", label: "Método", desc: "Procedimentos e normas analíticas", color: "blue" },
                { key: "maquina", label: "Máquina", desc: "Equipamentos, instrumentos e calibração", color: "amber" },
                { key: "material", label: "Material", desc: "Amostras, reagentes e consumíveis", color: "emerald" },
                { key: "mao_de_obra", label: "Mão de Obra", desc: "Competência, capacitação e analistas", color: "purple" },
                { key: "meio_ambiente", label: "Meio Ambiente", desc: "Temperatura, umidade e infraestrutura", color: "cyan" },
                { key: "medicao", label: "Medição", desc: "Incerteza, repetibilidade e metrologia", color: "rose" },
              ].map(({ key, label, desc }) => {
                const causes = capa.ishikawa_causes?.[key as keyof IshikawaCauses] ?? [];
                return (
                  <Card key={key} className="border-border">
                    <CardHeader className="p-3 pb-2">
                      <CardTitle className="text-xs font-bold flex items-center justify-between">
                        <span>{label}</span>
                        <Badge variant="outline" className="text-[10px]">{causes.length}</Badge>
                      </CardTitle>
                      <CardDescription className="text-[10px]">{desc}</CardDescription>
                    </CardHeader>
                    <CardContent className="p-3 pt-0">
                      {causes.length === 0 ? (
                        <p className="text-[11px] text-muted-foreground italic">Nenhuma causa identificada</p>
                      ) : (
                        <div className="flex flex-wrap gap-1 mt-1">
                          {causes.map((cause, idx) => (
                            <Badge key={idx} variant="secondary" className="text-[10px] py-0.5 px-1.5 font-normal">
                              {cause}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </div>
        ) : null}

        {activeTab === "five_whys" ? (
          <div className="space-y-4 pt-2">
            <div className="rounded-md border bg-muted/20 p-3 text-xs">
              <p className="font-semibold text-foreground">Metodologia dos 5 Porquês (Root Cause Analysis - RCA)</p>
              <p className="text-muted-foreground mt-0.5">
                Encadeamento causal sistemático até a identificação da causa raiz fundamental.
              </p>
            </div>

            {(!capa.five_whys || capa.five_whys.length === 0) ? (
              <p className="text-xs text-muted-foreground italic py-6 text-center">
                Nenhum encadeamento de 5 Porquês registrado nesta CAPA.
              </p>
            ) : (
              <div className="space-y-2.5">
                {capa.five_whys.map((item, index) => (
                  <div
                    key={index}
                    className={cn(
                      "rounded-md border p-3 text-xs transition-colors",
                      item.why_number === 5 ? "border-primary bg-primary/5" : "bg-card",
                    )}
                  >
                    <div className="flex items-center justify-between font-semibold">
                      <span className="text-primary font-mono">{item.why_number}º Porquê: {item.question}</span>
                      {item.why_number === 5 ? (
                        <Badge variant="default" className="text-[9px]">Causa Fundamental</Badge>
                      ) : null}
                    </div>
                    <p className="mt-1 text-muted-foreground leading-relaxed">{item.answer}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : null}

        {activeTab === "actions" ? (
          <div className="space-y-4 pt-2">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Plano de Ações 5W2H ({capa.action_items?.length ?? 0} ações)
              </h4>
            </div>

            <div className="overflow-x-auto rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[100px]">Tipo</TableHead>
                    <TableHead>Ação & Evidência</TableHead>
                    <TableHead>Responsável</TableHead>
                    <TableHead>Prazo</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Operação</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(!capa.action_items || capa.action_items.length === 0) ? (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center text-xs text-muted-foreground py-6">
                        Nenhuma ação cadastrada no plano desta CAPA.
                      </TableCell>
                    </TableRow>
                  ) : (
                    capa.action_items.map((item) => (
                      <TableRow key={item.id} className="text-xs">
                        <TableCell>
                          <Badge
                            variant="outline"
                            className={cn(
                              "text-[10px]",
                              item.action_type === "CONTENCAO" && "border-blue-300 bg-blue-50 text-blue-800",
                              item.action_type === "CORRETIVA" && "border-amber-300 bg-amber-50 text-amber-800",
                              item.action_type === "PREVENTIVA" && "border-purple-300 bg-purple-50 text-purple-800",
                            )}
                          >
                            {CAPA_ACTION_TYPE_LABELS[item.action_type] ?? item.action_type}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <p className="font-semibold text-foreground">{item.title}</p>
                          <p className="text-muted-foreground mt-0.5">{item.description}</p>
                          {item.completion_evidence ? (
                            <p className="mt-1 text-[11px] text-emerald-800 bg-emerald-50 rounded p-1 border border-emerald-200">
                              Evidência: {item.completion_evidence}
                            </p>
                          ) : null}
                        </TableCell>
                        <TableCell>{item.assigned_to.full_name}</TableCell>
                        <TableCell>{formatDate(item.due_date)}</TableCell>
                        <TableCell>
                          <Badge
                            variant="secondary"
                            className={cn(
                              "text-[10px]",
                              item.status === "CONCLUIDA" && "bg-emerald-100 text-emerald-800",
                              item.status === "EM_ANDAMENTO" && "bg-amber-100 text-amber-800",
                              item.status === "PENDENTE" && "bg-muted text-muted-foreground",
                            )}
                          >
                            {CAPA_ITEM_STATUS_LABELS[item.status] ?? item.status}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          {item.status !== "CONCLUIDA" && item.status !== "CANCELADA" && !isFinal ? (
                            <Button
                              type="button"
                              size="sm"
                              variant="outline"
                              onClick={() => setCompletingItemId(item.id)}
                              className="text-[11px] h-7"
                            >
                              Concluir Ação
                            </Button>
                          ) : (
                            <span className="text-[10px] text-muted-foreground font-mono">
                              {item.completed_at ? formatDate(item.completed_at) : "—"}
                            </span>
                          )}
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>

            {/* Modal/Formulário rápido de conclusão de ação */}
            {completingItemId ? (
              <div className="rounded-md border border-emerald-300 bg-emerald-50/50 p-3 space-y-2">
                <Label htmlFor="evidence" className="text-xs font-bold text-emerald-900">
                  Evidência Objetiva de Conclusão da Ação *
                </Label>
                <Textarea
                  id="evidence"
                  value={completionEvidence}
                  onChange={(e) => setCompletionEvidence(e.target.value)}
                  placeholder="Ex: Calibração executada em 15/11 com certificado #4402 arquivado e verificado dentro dos erros máximos tolerados."
                  rows={2}
                  className="text-xs bg-white"
                />
                <div className="flex gap-2 justify-end">
                  <Button
                    type="button"
                    size="sm"
                    variant="ghost"
                    onClick={() => { setCompletingItemId(null); setCompletionEvidence(""); }}
                    className="text-xs h-7"
                  >
                    Cancelar
                  </Button>
                  <Button
                    type="button"
                    size="sm"
                    onClick={() => handleCompleteAction(completingItemId)}
                    className="text-xs h-7 gap-1"
                  >
                    Confirmar Conclusão
                  </Button>
                </div>
              </div>
            ) : null}

            {/* Adicionar nova ação ao plano */}
            {canManage && !isFinal ? (
              <form onSubmit={handleAddActionItem} className="rounded-md border p-3.5 bg-muted/20 space-y-3">
                <h5 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                  <Plus className="h-3.5 w-3.5" /> Adicionar Ação ao Plano
                </h5>
                <div className="grid gap-2 sm:grid-cols-3">
                  <div className="sm:col-span-2">
                    <Label className="text-[11px]">Título da Ação *</Label>
                    <Input
                      placeholder="Ex: Treinamento operacional dos analistas no método atualizado"
                      value={newActionTitle}
                      onChange={(e) => setNewActionTitle(e.target.value)}
                      required
                      className="mt-0.5 text-xs bg-white"
                    />
                  </div>
                  <div>
                    <Label className="text-[11px]">Tipo de Ação *</Label>
                    <Select
                      value={newActionType}
                      onValueChange={(val) => setNewActionType(val as CapaActionType)}
                    >
                      <SelectTrigger className="mt-0.5 text-xs bg-white">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="CONTENCAO">Contenção Imediata</SelectItem>
                        <SelectItem value="CORRETIVA">Ação Corretiva</SelectItem>
                        <SelectItem value="PREVENTIVA">Ação Preventiva</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div>
                  <Label className="text-[11px]">Descrição Detalhada & Critério de Execução *</Label>
                  <Textarea
                    placeholder="Detalhamento operacional da ação, recursos necessários e evidência esperada."
                    value={newActionDesc}
                    onChange={(e) => setNewActionDesc(e.target.value)}
                    rows={2}
                    required
                    className="mt-0.5 text-xs bg-white"
                  />
                </div>

                <div className="grid gap-2 sm:grid-cols-2">
                  <div>
                    <Label className="text-[11px]">Responsável *</Label>
                    <Select value={newActionAssignee} onValueChange={setNewActionAssignee}>
                      <SelectTrigger className="mt-0.5 text-xs bg-white">
                        <SelectValue placeholder="Selecione" />
                      </SelectTrigger>
                      <SelectContent>
                        {users.map((u) => (
                          <SelectItem key={u.id} value={u.id}>
                            {u.full_name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label className="text-[11px]">Prazo Limite *</Label>
                    <Input
                      type="date"
                      value={newActionDue}
                      min={todayIso()}
                      onChange={(e) => setNewActionDue(e.target.value)}
                      required
                      className="mt-0.5 text-xs bg-white"
                    />
                  </div>
                </div>

                <div className="flex justify-end pt-1">
                  <Button type="submit" size="sm" disabled={addingAction} className="text-xs gap-1.5">
                    {addingAction ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Plus className="h-3.5 w-3.5" />}
                    Incluir Ação
                  </Button>
                </div>
              </form>
            ) : null}
          </div>
        ) : null}

        {activeTab === "effectiveness" ? (
          <div className="space-y-4 pt-2">
            <div className="rounded-md border bg-indigo-50/40 border-indigo-200 p-3.5 text-xs">
              <h4 className="font-bold text-indigo-900 flex items-center gap-1.5">
                <ShieldCheck className="h-4 w-4" /> Verificação Formal de Eficácia Temporal (ISO/IEC 17025 §8.7.3)
              </h4>
              <p className="mt-1 text-indigo-800 leading-relaxed">
                O laboratório deve analisar criticamente a eficácia de qualquer ação corretiva implementada,
                atestando com dados objetivos que o desvio foi mitigado e que não houve reincidências no período amostrado.
              </p>
            </div>

            <div className="grid gap-3 sm:grid-cols-3 rounded-md border p-3 text-xs bg-muted/20">
              <div>
                <p className="text-muted-foreground font-medium">Data Alvo de Avaliação</p>
                <p className="font-semibold text-foreground mt-0.5">
                  {capa.target_effectiveness_date ? formatDate(capa.target_effectiveness_date) : "Não especificada"}
                </p>
              </div>
              <div>
                <p className="text-muted-foreground font-medium">Status da Eficácia</p>
                <Badge
                  variant="secondary"
                  className={cn(
                    "text-[10px] mt-0.5",
                    capa.effectiveness_status === "EFICAZ" && "bg-emerald-100 text-emerald-800",
                    capa.effectiveness_status === "INEFICAZ" && "bg-rose-100 text-rose-800",
                    capa.effectiveness_status === "PENDENTE" && "bg-amber-100 text-amber-800",
                  )}
                >
                  {CAPA_EFFECTIVENESS_STATUS_LABELS[capa.effectiveness_status] ?? capa.effectiveness_status}
                </Badge>
              </div>
              <div>
                <p className="text-muted-foreground font-medium">Avaliador Responsável</p>
                <p className="font-semibold text-foreground mt-0.5">
                  {capa.effectiveness_evaluator ? capa.effectiveness_evaluator.full_name : "Pendente"}
                </p>
              </div>
            </div>

            {capa.effectiveness_check ? (
              <div className="rounded-md border p-3 text-xs space-y-1">
                <p className="text-muted-foreground font-medium">Parecer de Eficácia Registrado:</p>
                <p className="text-foreground leading-relaxed whitespace-pre-wrap">{capa.effectiveness_check}</p>
                {capa.effectiveness_evaluated_at ? (
                  <p className="text-[10px] text-muted-foreground pt-1">
                    Avaliado em: {formatDateTime(capa.effectiveness_evaluated_at)}
                  </p>
                ) : null}
              </div>
            ) : null}

            {/* Avaliação formal se pendente */}
            {canManage && capa.status !== "CANCELADA" && capa.effectiveness_status === "PENDENTE" ? (
              <form onSubmit={handleEvaluateEffectiveness} className="rounded-md border p-4 bg-card space-y-3">
                <h5 className="text-xs font-bold uppercase tracking-wider text-primary flex items-center gap-1.5">
                  <Target className="h-4 w-4" /> Realizar Avaliação Formal de Eficácia
                </h5>

                {pendingActionsCount > 0 ? (
                  <div className="rounded-md border border-amber-300 bg-amber-50 p-2.5 text-xs text-amber-900 flex items-center gap-2">
                    <TriangleAlert className="h-4 w-4 shrink-0" />
                    <span>
                      Existem <strong>{pendingActionsCount} ações</strong> pendentes ou em andamento. Conclua todas as ações antes de avaliar a eficácia.
                    </span>
                  </div>
                ) : null}

                <div className="grid gap-3 sm:grid-cols-2">
                  <div>
                    <Label className="text-xs">Desfecho da Eficácia *</Label>
                    <Select
                      value={effStatus}
                      onValueChange={(val) => setEffStatus(val as CapaEffectivenessStatus)}
                    >
                      <SelectTrigger className="mt-1 text-xs">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="EFICAZ">Eficaz (Causa Raiz Eliminada / Encerrar)</SelectItem>
                        <SelectItem value="INEFICAZ">Ineficaz (Reabrir Nova CAPA Derivada)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="flex items-center pt-6">
                    <label className="flex items-center gap-2 text-xs cursor-pointer">
                      <input
                        type="checkbox"
                        checked={recurrence}
                        onChange={(e) => setRecurrence(e.target.checked)}
                        className="rounded border-gray-300"
                      />
                      <span className="font-medium text-rose-700">Houve reincidência do desvio no período</span>
                    </label>
                  </div>
                </div>

                <div>
                  <Label htmlFor="eff-just" className="text-xs">
                    Justificativa Técnica e Evidências Objetivas da Avaliação *
                  </Label>
                  <Textarea
                    id="eff-just"
                    value={effJustification}
                    onChange={(e) => setEffJustification(e.target.value)}
                    placeholder="Ex: Durante 60 dias de operação contínua após substituição da vedação e calibração, foram executados 42 ensaios com 100% de conformidade metrológica e ausência de desvios."
                    rows={3}
                    required
                    className="mt-1 text-xs"
                  />
                </div>

                <div className="flex justify-end pt-2">
                  <Button
                    type="submit"
                    disabled={evaluatingEff || pendingActionsCount > 0}
                    className="gap-2 text-xs"
                  >
                    {evaluatingEff ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <ShieldCheck className="h-4 w-4" />
                    )}
                    Assinar Avaliação de Eficácia (Part 11)
                  </Button>
                </div>
              </form>
            ) : null}
          </div>
        ) : null}

        <DialogFooter className="pt-2 border-t">
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            Fechar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
