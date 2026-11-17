import * as React from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  ChevronRight,
  ClipboardCheck,
  FileSearch,
  Filter,
  Flame,
  HelpCircle,
  Link as LinkIcon,
  Plus,
  RefreshCw,
  Search,
  ShieldAlert,
  ShieldCheck,
  XCircle,
} from "lucide-react";

import { StatusBadge } from "@/components/StatusBadge";
import { Button } from "@/components/ui/button";
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
import { useToast } from "@/components/ui/toast";
import { useAuth } from "@/hooks/use-auth";
import { oosApi, api, ApiError } from "@/lib/api";
import type {
  DeviationType,
  LabTest,
  OOSInvestigation,
  OOSInvestigationStatus,
  OOSRootCauseCategory,
  Page,
  RetestResultItem,
} from "@/lib/types";
import { formatDateTime } from "@/lib/utils";

const ROOT_CAUSE_LABELS: Record<OOSRootCauseCategory, string> = {
  EQUIPMENT_MALFUNCTION: "Falha de Equipamento / Instrumento",
  REAGENT_CONTAMINATION: "Contaminação de Reagente / Solvente",
  OPERATOR_ERROR: "Erro Operacional / Execução Técnica",
  CALCULATION_ERROR: "Erro de Cálculo / Diluição",
  ENVIRONMENTAL_FLUCTUATION: "Flutuação Ambiental (Temp/Umidade)",
  SAMPLE_ANOMALY: "Anomalia Intrínseca do Produto / Amostra",
  METHOD_LIMITATION: "Limitação Metodológica Validada",
  OTHER: "Outra Causa Raiz",
};

export function OOSInvestigationsPage() {
  const { user } = useAuth();
  const { push } = useToast();
  const queryClient = useQueryClient();

  const [search, setSearch] = React.useState("");
  const [typeFilter, setTypeFilter] = React.useState<string>("all");
  const [statusFilter, setStatusFilter] = React.useState<string>("all");

  const [createModalOpen, setCreateModalOpen] = React.useState(false);
  const [selectedInvestigation, setSelectedInvestigation] = React.useState<OOSInvestigation | null>(null);

  // Queries
  const investigationsQuery = useQuery({
    queryKey: ["oos-investigations", typeFilter, statusFilter, search],
    queryFn: () =>
      oosApi.list({
        deviation_type: typeFilter !== "all" ? typeFilter : undefined,
        status: statusFilter !== "all" ? statusFilter : undefined,
        search: search.trim() || undefined,
      }),
  });

  const investigations = investigationsQuery.data ?? [];

  // KPIs
  const totalCount = investigations.length;
  const phase1Count = investigations.filter((i) => i.status === "PHASE_I_PENDING").length;
  const phase2Count = investigations.filter((i) => i.status === "PHASE_II_REQUIRED").length;
  const productFailures = investigations.filter((i) => i.status === "CONFIRMED_PRODUCT_FAILURE").length;
  const capasLinked = investigations.filter((i) => i.capa_action_id).length;

  return (
    <div className="space-y-6">
      {/* HEADER */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <ShieldAlert className="h-6 w-6 text-rose-600" />
            Desvios Analíticos OOS & OOT
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Motor de investigação em duas fases (FDA Guidance) e trabalho não conforme (ISO/IEC 17025 §7.10).
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => investigationsQuery.refetch()}
            disabled={investigationsQuery.isFetching}
          >
            <RefreshCw className={`h-4 w-4 mr-1.5 ${investigationsQuery.isFetching ? "animate-spin" : ""}`} />
            Atualizar
          </Button>
          <Button
            size="sm"
            className="bg-rose-600 hover:bg-rose-700 text-white"
            onClick={() => setCreateModalOpen(true)}
          >
            <Plus className="h-4 w-4 mr-1.5" />
            Abrir Investigação OOS
          </Button>
        </div>
      </div>

      {/* KPIS */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-5">
        <div className="rounded-lg border border-border bg-card p-4">
          <span className="text-xs text-muted-foreground font-medium">Total de Desvios</span>
          <p className="mt-1 text-2xl font-bold font-mono">{totalCount}</p>
        </div>
        <div className="rounded-lg border border-amber-200 bg-amber-500/5 p-4">
          <span className="text-xs text-amber-700 font-medium">Fase I (Laboratorial)</span>
          <p className="mt-1 text-2xl font-bold font-mono text-amber-800">{phase1Count}</p>
        </div>
        <div className="rounded-lg border border-blue-200 bg-blue-500/5 p-4">
          <span className="text-xs text-blue-700 font-medium">Fase II (Re-ensaio)</span>
          <p className="mt-1 text-2xl font-bold font-mono text-blue-800">{phase2Count}</p>
        </div>
        <div className="rounded-lg border border-rose-200 bg-rose-500/5 p-4">
          <span className="text-xs text-rose-700 font-medium">Falha de Produto</span>
          <p className="mt-1 text-2xl font-bold font-mono text-rose-800">{productFailures}</p>
        </div>
        <div className="rounded-lg border border-purple-200 bg-purple-500/5 p-4">
          <span className="text-xs text-purple-700 font-medium">Ações CAPA</span>
          <p className="mt-1 text-2xl font-bold font-mono text-purple-800">{capasLinked}</p>
        </div>
      </div>

      {/* FILTROS */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[240px]">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Buscar por número OOS (ex.: OOS-2026-0001)..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 h-9 text-xs"
          />
        </div>
        <div className="w-[160px]">
          <Select value={typeFilter} onValueChange={setTypeFilter}>
            <SelectTrigger className="h-9 text-xs">
              <SelectValue placeholder="Tipo de Desvio" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos os tipos</SelectItem>
              <SelectItem value="OOS">OOS (Fora de Espec.)</SelectItem>
              <SelectItem value="OOT">OOT (Fora de Tendência)</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="w-[180px]">
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="h-9 text-xs">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos os status</SelectItem>
              <SelectItem value="PHASE_I_PENDING">Fase I Pendente</SelectItem>
              <SelectItem value="PHASE_II_REQUIRED">Fase II Requerida</SelectItem>
              <SelectItem value="CONFIRMED_LAB_ERROR">Erro Lab. Confirmado</SelectItem>
              <SelectItem value="CONFIRMED_PRODUCT_FAILURE">Falha Produto Confirmada</SelectItem>
              <SelectItem value="CLOSED">Encerradas</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* LISTA DE DESVIOS */}
      {investigations.length === 0 ? (
        <div className="rounded-lg border border-dashed border-border p-12 text-center text-muted-foreground">
          <FileSearch className="mx-auto h-10 w-10 opacity-30 mb-3" />
          <p className="text-base font-semibold">Nenhuma investigação de desvio analítico encontrada</p>
          <p className="text-xs mt-1">
            Abra uma nova investigação ou ajuste os filtros acima.
          </p>
        </div>
      ) : (
        <div className="rounded-lg border border-border bg-card overflow-hidden shadow-sm">
          <table className="w-full text-left text-xs">
            <thead className="bg-muted/40 font-semibold text-muted-foreground border-b border-border">
              <tr>
                <th className="p-3">Número / Tipo</th>
                <th className="p-3">Ensaio Analítico</th>
                <th className="p-3">Resultado vs Limite</th>
                <th className="p-3">Status da Investigação</th>
                <th className="p-3">Vínculo CAPA</th>
                <th className="p-3">Abertura</th>
                <th className="p-3 text-right">Ação</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/50">
              {investigations.map((inv) => (
                <tr key={inv.id} className="hover:bg-muted/15 transition-colors">
                  <td className="p-3 font-medium">
                    <div className="flex items-center gap-1.5">
                      <span
                        className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                          inv.deviation_type === "OOS"
                            ? "bg-rose-100 text-rose-800"
                            : "bg-amber-100 text-amber-800"
                        }`}
                      >
                        {inv.deviation_type}
                      </span>
                      <span className="font-mono">{inv.investigation_number}</span>
                    </div>
                  </td>
                  <td className="p-3">
                    <div className="font-medium">{inv.lab_test?.name ?? "Ensaio"}</div>
                    <div className="text-[11px] text-muted-foreground font-mono">
                      {inv.lab_test?.code ?? "ID: " + inv.lab_test_id.slice(0, 8)}
                    </div>
                  </td>
                  <td className="p-3">
                    <div className="font-mono font-semibold text-rose-700">
                      {inv.initial_result !== null ? `${inv.initial_result} ${inv.lab_test?.unit ?? ""}` : inv.initial_result_text ?? "—"}
                    </div>
                    <div className="text-[10px] text-muted-foreground">
                      Esp.: {inv.specification_min ?? "—"} a {inv.specification_max ?? "—"} {inv.lab_test?.unit ?? ""}
                    </div>
                  </td>
                  <td className="p-3">
                    <span
                      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium ${
                        inv.status === "CLOSED"
                          ? "bg-emerald-100 text-emerald-800"
                          : inv.status === "CONFIRMED_PRODUCT_FAILURE"
                            ? "bg-rose-100 text-rose-800 font-semibold"
                            : inv.status === "CONFIRMED_LAB_ERROR"
                              ? "bg-blue-100 text-blue-800"
                              : inv.status === "PHASE_II_REQUIRED"
                                ? "bg-purple-100 text-purple-800"
                                : "bg-amber-100 text-amber-800"
                      }`}
                    >
                      {inv.status}
                    </span>
                  </td>
                  <td className="p-3">
                    {inv.capa_action_id ? (
                      <span className="inline-flex items-center gap-1 text-[11px] font-mono font-medium text-purple-700 bg-purple-50 px-2 py-0.5 rounded border border-purple-200">
                        <LinkIcon className="h-3 w-3" />
                        CAPA Ativa
                      </span>
                    ) : (
                      <span className="text-muted-foreground text-[11px]">—</span>
                    )}
                  </td>
                  <td className="p-3 text-muted-foreground text-[11px]">
                    {formatDateTime(inv.detected_at)}
                  </td>
                  <td className="p-3 text-right">
                    <Button
                      variant="outline"
                      size="sm"
                      className="h-7 text-xs"
                      onClick={() => setSelectedInvestigation(inv)}
                    >
                      Conduzir <ChevronRight className="ml-1 h-3 w-3" />
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* MODAL: DETALHES E CONDUÇÃO DA INVESTIGAÇÃO */}
      {selectedInvestigation ? (
        <InvestigationDetailModal
          investigation={selectedInvestigation}
          open={!!selectedInvestigation}
          onOpenChange={(open) => !open && setSelectedInvestigation(null)}
          onSuccess={() => {
            investigationsQuery.refetch();
            setSelectedInvestigation(null);
          }}
        />
      ) : null}

      {/* MODAL: ABERTURA DE NOVA INVESTIGAÇÃO */}
      <CreateInvestigationModal
        open={createModalOpen}
        onOpenChange={setCreateModalOpen}
        onSuccess={() => {
          investigationsQuery.refetch();
          setCreateModalOpen(false);
          push({
            title: "Investigação Instaurada",
            description: "Desvio analítico registrado com status Fase I Pendente.",
            variant: "success",
          });
        }}
      />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Modal de Condução e Detalhes da Investigação OOS
// ---------------------------------------------------------------------------

function InvestigationDetailModal({
  investigation,
  open,
  onOpenChange,
  onSuccess,
}: {
  investigation: OOSInvestigation;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => void;
}) {
  const { push } = useToast();
  const [tab, setTab] = React.useState<"summary" | "phase1" | "phase2" | "close">("summary");

  // Fase 1 Form
  const [calcVerified, setCalcVerified] = React.useState(investigation.phase_1_checklist?.calculation_verified ?? false);
  const [instVerified, setInstVerified] = React.useState(investigation.phase_1_checklist?.instrument_verified ?? false);
  const [reagVerified, setReagVerified] = React.useState(investigation.phase_1_checklist?.reagent_verified ?? false);
  const [analystInterviewed, setAnalystInterviewed] = React.useState(investigation.phase_1_checklist?.analyst_interviewed ?? false);
  const [sampleVerified, setSampleVerified] = React.useState(investigation.phase_1_checklist?.sample_integrity_verified ?? false);
  const [phase1Notes, setPhase1Notes] = React.useState(investigation.phase_1_checklist?.checklist_notes ?? "");
  const [phase1Conclusion, setPhase1Conclusion] = React.useState(investigation.phase_1_conclusion ?? "");
  const [phase2Required, setPhase2Required] = React.useState(investigation.phase_2_required ?? true);
  const [isSavingPhase1, setIsSavingPhase1] = React.useState(false);

  // Fase 2 Form
  const [phase2Plan, setPhase2Plan] = React.useState(investigation.phase_2_plan ?? "");
  const [rootCauseCategory, setRootCauseCategory] = React.useState<OOSRootCauseCategory>(
    investigation.root_cause_category ?? "SAMPLE_ANOMALY",
  );
  const [rootCauseDescription, setRootCauseDescription] = React.useState(investigation.root_cause_description ?? "");
  const [confirmedStatus, setConfirmedStatus] = React.useState<"CONFIRMED_LAB_ERROR" | "CONFIRMED_PRODUCT_FAILURE">(
    investigation.status === "CONFIRMED_LAB_ERROR" ? "CONFIRMED_LAB_ERROR" : "CONFIRMED_PRODUCT_FAILURE",
  );
  const [autoCreateCapa, setAutoCreateCapa] = React.useState(true);
  const [retestPoints, setRetestPoints] = React.useState<RetestResultItem[]>(
    investigation.phase_2_retest_results?.length > 0
      ? investigation.phase_2_retest_results
      : [
          { retest_number: 1, analyst_name: "Analista Sênior", result_value: null, outcome: "PENDENTE", retest_date: new Date().toISOString().slice(0, 10) },
          { retest_number: 2, analyst_name: "Analista Sênior", result_value: null, outcome: "PENDENTE", retest_date: new Date().toISOString().slice(0, 10) },
        ],
  );
  const [isSavingPhase2, setIsSavingPhase2] = React.useState(false);

  // Close Form
  const [finalDisposition, setFinalDisposition] = React.useState(investigation.final_disposition ?? "");
  const [isClosing, setIsClosing] = React.useState(false);

  async function handleSavePhase1() {
    if (!phase1Conclusion.trim()) {
      push({ title: "Parecer obrigatório", description: "Descreva a conclusão da Fase I.", variant: "warning" });
      return;
    }
    setIsSavingPhase1(true);
    try {
      await oosApi.updatePhase1(investigation.id, {
        calculation_verified: calcVerified,
        instrument_verified: instVerified,
        reagent_verified: reagVerified,
        analyst_interviewed: analystInterviewed,
        sample_integrity_verified: sampleVerified,
        checklist_notes: phase1Notes.trim() || undefined,
        phase_1_conclusion: phase1Conclusion.trim(),
        phase_2_required: phase2Required,
      });
      push({ title: "Fase I Registrada", description: "Investigação laboratorial imediata concluída com sucesso.", variant: "success" });
      onSuccess();
    } catch (err) {
      push({ title: "Erro na Fase I", description: err instanceof ApiError ? err.message : "Falha na comunicação.", variant: "destructive" });
    } finally {
      setIsSavingPhase1(false);
    }
  }

  async function handleSavePhase2() {
    if (!phase2Plan.trim() || !rootCauseDescription.trim()) {
      push({ title: "Dados obrigatórios", description: "Preencha o plano de re-ensaio e a causa raiz.", variant: "warning" });
      return;
    }
    setIsSavingPhase2(true);
    try {
      await oosApi.updatePhase2(investigation.id, {
        phase_2_plan: phase2Plan.trim(),
        retest_results: retestPoints,
        root_cause_category: rootCauseCategory,
        root_cause_description: rootCauseDescription.trim(),
        confirmed_status: confirmedStatus,
        auto_create_capa: autoCreateCapa,
      });
      push({ title: "Fase II Concluída", description: "Causa raiz homologada e vínculo CAPA atualizado.", variant: "success" });
      onSuccess();
    } catch (err) {
      push({ title: "Erro na Fase II", description: err instanceof ApiError ? err.message : "Falha na operação.", variant: "destructive" });
    } finally {
      setIsSavingPhase2(false);
    }
  }

  async function handleClose() {
    if (!finalDisposition.trim()) {
      push({ title: "Disposição obrigatória", description: "Informe a disposição técnica e sanitária final.", variant: "warning" });
      return;
    }
    setIsClosing(true);
    try {
      await oosApi.close(investigation.id, { final_disposition: finalDisposition.trim() });
      push({ title: "Investigação Encerrada", description: "Desvio analítico fechado com conformidade regulamentar.", variant: "success" });
      onSuccess();
    } catch (err) {
      push({ title: "Erro ao encerrar", description: err instanceof ApiError ? err.message : "Falha na operação.", variant: "destructive" });
    } finally {
      setIsClosing(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <span
              className={`px-2 py-0.5 rounded text-xs font-bold ${
                investigation.deviation_type === "OOS"
                  ? "bg-rose-100 text-rose-800"
                  : "bg-amber-100 text-amber-800"
              }`}
            >
              {investigation.deviation_type}
            </span>
            <DialogTitle className="font-mono text-lg">
              {investigation.investigation_number}
            </DialogTitle>
          </div>
          <DialogDescription className="text-xs">
            {investigation.lab_test?.name} — Detectado em {formatDateTime(investigation.detected_at)}
          </DialogDescription>
        </DialogHeader>

        {/* NAVEGAÇÃO DE ABAS */}
        <div className="flex border-b border-border text-xs gap-4 pb-2 mt-2">
          <button
            type="button"
            className={`pb-1 font-medium transition-colors ${
              tab === "summary" ? "border-b-2 border-primary text-primary" : "text-muted-foreground hover:text-foreground"
            }`}
            onClick={() => setTab("summary")}
          >
            1. Resumo & Dados
          </button>
          <button
            type="button"
            className={`pb-1 font-medium transition-colors ${
              tab === "phase1" ? "border-b-2 border-primary text-primary" : "text-muted-foreground hover:text-foreground"
            }`}
            onClick={() => setTab("phase1")}
          >
            2. Fase I (Laboratorial)
          </button>
          <button
            type="button"
            className={`pb-1 font-medium transition-colors ${
              tab === "phase2" ? "border-b-2 border-primary text-primary" : "text-muted-foreground hover:text-foreground"
            }`}
            onClick={() => setTab("phase2")}
          >
            3. Fase II (Causa Raiz & CAPA)
          </button>
          <button
            type="button"
            className={`pb-1 font-medium transition-colors ${
              tab === "close" ? "border-b-2 border-primary text-primary" : "text-muted-foreground hover:text-foreground"
            }`}
            onClick={() => setTab("close")}
          >
            4. Encerramento
          </button>
        </div>

        {/* CONTEÚDO DAS ABAS */}
        {tab === "summary" ? (
          <div className="space-y-4 py-2 text-xs">
            <div className="grid grid-cols-2 gap-4 rounded-lg bg-muted/20 p-4 border border-border">
              <div>
                <span className="text-muted-foreground">Ensaio Analítico:</span>
                <p className="font-semibold text-sm mt-0.5">{investigation.lab_test?.name}</p>
              </div>
              <div>
                <span className="text-muted-foreground">Resultado Anômalo:</span>
                <p className="font-mono font-bold text-sm text-rose-700 mt-0.5">
                  {investigation.initial_result !== null ? `${investigation.initial_result} ${investigation.lab_test?.unit ?? ""}` : "—"}
                </p>
              </div>
              <div>
                <span className="text-muted-foreground">Especificação de Aceite:</span>
                <p className="font-mono text-muted-foreground mt-0.5">
                  Min: {investigation.specification_min ?? "N/A"} | Max: {investigation.specification_max ?? "N/A"} {investigation.lab_test?.unit ?? ""}
                </p>
              </div>
              <div>
                <span className="text-muted-foreground">Responsável pela Detecção:</span>
                <p className="font-medium mt-0.5">{investigation.detected_by?.full_name ?? "Analista"}</p>
              </div>
            </div>

            {/* Alerta Regulamentar de Intertravamento */}
            <div className="rounded-lg border border-amber-300 bg-amber-50 p-3 text-amber-900 flex items-start gap-2.5">
              <AlertTriangle className="h-4 w-4 shrink-0 text-amber-700 mt-0.5" />
              <div>
                <p className="font-semibold">Intertravamento Regulamentar Ativo (ISO/IEC 17025 §7.10)</p>
                <p className="text-amber-800/90 mt-0.5 leading-relaxed">
                  Enquanto esta investigação estiver aberta, nenhum laudo oficial poderá ser emitido contendo este ensaio.
                </p>
              </div>
            </div>
          </div>
        ) : tab === "phase1" ? (
          <div className="space-y-4 py-2 text-xs">
            <div className="rounded-md bg-muted/10 p-3 border border-border space-y-2.5">
              <h4 className="font-semibold text-foreground flex items-center gap-1.5">
                <ClipboardCheck className="h-4 w-4 text-primary" />
                Checklist de Investigação Laboratorial Imediata (FDA Guidance)
              </h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={calcVerified}
                    onChange={(e) => setCalcVerified(e.target.checked)}
                    className="rounded border-border text-primary"
                  />
                  <span>1. Cálculos e diluições verificados</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={instVerified}
                    onChange={(e) => setInstVerified(e.target.checked)}
                    className="rounded border-border text-primary"
                  />
                  <span>2. Instrumento e calibração checados</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={reagVerified}
                    onChange={(e) => setReagVerified(e.target.checked)}
                    className="rounded border-border text-primary"
                  />
                  <span>3. Reagentes e padrões CRM válidos</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={analystInterviewed}
                    onChange={(e) => setAnalystInterviewed(e.target.checked)}
                    className="rounded border-border text-primary"
                  />
                  <span>4. Analista executante entrevistado</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer sm:col-span-2">
                  <input
                    type="checkbox"
                    checked={sampleVerified}
                    onChange={(e) => setSampleVerified(e.target.checked)}
                    className="rounded border-border text-primary"
                  />
                  <span>5. Integridade física e homogeneidade da amostra confirmada</span>
                </label>
              </div>
            </div>

            <div>
              <Label className="text-xs">Notas Técnicas do Checklist</Label>
              <Input
                value={phase1Notes}
                onChange={(e) => setPhase1Notes(e.target.value)}
                placeholder="Ex.: Pipeta calibrada sob certificado CAL-2026-90, solvente HPLC Merck lote válido..."
                className="mt-1 text-xs"
              />
            </div>

            <div>
              <Label className="text-xs">Conclusão da Fase I *</Label>
              <Textarea
                rows={3}
                value={phase1Conclusion}
                onChange={(e) => setPhase1Conclusion(e.target.value)}
                placeholder="Descreva se foi constatado erro operacional de laboratório ou se a hipótese de falha de produto permanece..."
                className="mt-1 text-xs"
              />
            </div>

            <div className="flex items-center gap-2 pt-1">
              <input
                type="checkbox"
                id="reqPhase2"
                checked={phase2Required}
                onChange={(e) => setPhase2Required(e.target.checked)}
                className="rounded border-border text-primary"
              />
              <Label htmlFor="reqPhase2" className="cursor-pointer text-xs font-semibold text-foreground">
                Requer investigação de Fase II (Re-ensaio / Análise de Causa Raiz)?
              </Label>
            </div>

            <Button onClick={handleSavePhase1} disabled={isSavingPhase1} className="w-full mt-2">
              Salvar e Atualizar Fase I
            </Button>
          </div>
        ) : tab === "phase2" ? (
          <div className="space-y-4 py-2 text-xs">
            <div>
              <Label className="text-xs">Plano de Re-ensaio e Amostragem *</Label>
              <Textarea
                rows={2}
                value={phase2Plan}
                onChange={(e) => setPhase2Plan(e.target.value)}
                placeholder="Procedimento detalhado para re-testar a amostra com analista sênior independente..."
                className="mt-1 text-xs"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <Label className="text-xs">Categoria de Causa Raiz *</Label>
                <Select
                  value={rootCauseCategory}
                  onValueChange={(val) => setRootCauseCategory(val as OOSRootCauseCategory)}
                >
                  <SelectTrigger className="mt-1 text-xs">
                    <SelectValue placeholder="Selecione categoria" />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(ROOT_CAUSE_LABELS).map(([k, label]) => (
                      <SelectItem key={k} value={k}>
                        {label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label className="text-xs">Classificação Final do Desvio *</Label>
                <Select
                  value={confirmedStatus}
                  onValueChange={(val) => setConfirmedStatus(val as any)}
                >
                  <SelectTrigger className="mt-1 text-xs">
                    <SelectValue placeholder="Selecione desfecho" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="CONFIRMED_LAB_ERROR">Erro de Laboratório Comprovado</SelectItem>
                    <SelectItem value="CONFIRMED_PRODUCT_FAILURE">Falha de Produto Confirmada (Não Conforme)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div>
              <Label className="text-xs">Descrição Técnica da Causa Raiz *</Label>
              <Textarea
                rows={2}
                value={rootCauseDescription}
                onChange={(e) => setRootCauseDescription(e.target.value)}
                placeholder="Detalhes da investigação que comprovam a causa raiz identificada..."
                className="mt-1 text-xs"
              />
            </div>

            <div className="flex items-center gap-2 rounded-md bg-purple-500/10 p-3 border border-purple-200">
              <input
                type="checkbox"
                id="autoCapa"
                checked={autoCreateCapa}
                onChange={(e) => setAutoCreateCapa(e.target.checked)}
                className="rounded border-border text-purple-600"
              />
              <Label htmlFor="autoCapa" className="cursor-pointer text-xs font-semibold text-purple-900">
                Gerar automaticamente Ação Corretiva no Módulo CAPA (ISO 17025 §8.7)
              </Label>
            </div>

            <Button onClick={handleSavePhase2} disabled={isSavingPhase2} className="w-full mt-2">
              Concluir Fase II e Atualizar Investigação
            </Button>
          </div>
        ) : (
          <div className="space-y-4 py-2 text-xs">
            <div>
              <Label className="text-xs">Disposição Final Sanitária e Metrológica *</Label>
              <Textarea
                rows={4}
                value={finalDisposition}
                onChange={(e) => setFinalDisposition(e.target.value)}
                placeholder="Parecer final da coordenação/fiscalização: interdição de lote, descarte ou aceite condicionado com base na resolução do CAPA..."
                className="mt-1 text-xs"
              />
            </div>

            <Button
              onClick={handleClose}
              disabled={isClosing || investigation.status === "CLOSED"}
              className="w-full bg-emerald-600 hover:bg-emerald-700 text-white mt-2"
            >
              <CheckCircle2 className="mr-1.5 h-4 w-4" />
              {investigation.status === "CLOSED" ? "Investigação já Encerrada" : "Encerrar Formalmente a Investigação"}
            </Button>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

// ---------------------------------------------------------------------------
// Modal de Criação de Investigação OOS
// ---------------------------------------------------------------------------

function CreateInvestigationModal({
  open,
  onOpenChange,
  onSuccess,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => void;
}) {
  const { push } = useToast();
  const [testId, setTestId] = React.useState("");
  const [devType, setDevType] = React.useState<DeviationType>("OOS");
  const [initialResult, setInitialResult] = React.useState("");
  const [specMin, setSpecMin] = React.useState("");
  const [specMax, setSpecMax] = React.useState("");
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  // Busca ensaios
  const testsQuery = useQuery({
    queryKey: ["tests-for-oos"],
    queryFn: () => api.get<Page<LabTest>>("/tests?size=100"),
    enabled: open,
  });

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!testId) {
      push({ title: "Ensaio obrigatório", description: "Selecione o ensaio que apresentou o desvio.", variant: "warning" });
      return;
    }
    setIsSubmitting(true);
    try {
      await oosApi.create({
        lab_test_id: testId,
        deviation_type: devType,
        initial_result: initialResult ? parseFloat(initialResult.replace(",", ".")) : undefined,
        specification_min: specMin ? parseFloat(specMin.replace(",", ".")) : undefined,
        specification_max: specMax ? parseFloat(specMax.replace(",", ".")) : undefined,
      });
      onSuccess();
    } catch (err) {
      push({ title: "Falha na abertura", description: err instanceof ApiError ? err.message : "Erro na operação.", variant: "destructive" });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-base">
            <AlertCircle className="h-5 w-5 text-rose-600" />
            Abertura de Investigação de Desvio Analítico
          </DialogTitle>
          <DialogDescription className="text-xs">
            Formalize resultados OOS/OOT para acionar o protocolo ISO 17025 §7.10.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-3 pt-2 text-xs">
          <div>
            <Label className="text-xs">Ensaio Analítico *</Label>
            <Select value={testId} onValueChange={setTestId}>
              <SelectTrigger className="mt-1 text-xs">
                <SelectValue placeholder="Selecione o ensaio com resultado anômalo" />
              </SelectTrigger>
              <SelectContent>
                {testsQuery.data?.items?.map((t: LabTest) => (
                  <SelectItem key={t.id} value={t.id}>
                    {t.name} ({t.unit ?? "s/u"})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label className="text-xs">Tipologia do Desvio *</Label>
            <Select value={devType} onValueChange={(val) => setDevType(val as DeviationType)}>
              <SelectTrigger className="mt-1 text-xs">
                <SelectValue placeholder="Selecione tipologia" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="OOS">OOS — Fora de Especificação</SelectItem>
                <SelectItem value="OOT">OOT — Fora de Tendência (Trend)</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label className="text-xs">Resultado Obtido</Label>
            <Input
              value={initialResult}
              onChange={(e) => setInitialResult(e.target.value)}
              placeholder="Ex.: 91.4"
              className="mt-1 text-xs font-mono"
            />
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div>
              <Label className="text-xs">Limite Mínimo</Label>
              <Input
                value={specMin}
                onChange={(e) => setSpecMin(e.target.value)}
                placeholder="Ex.: 95.0"
                className="mt-1 text-xs font-mono"
              />
            </div>
            <div>
              <Label className="text-xs">Limite Máximo</Label>
              <Input
                value={specMax}
                onChange={(e) => setSpecMax(e.target.value)}
                placeholder="Ex.: 105.0"
                className="mt-1 text-xs font-mono"
              />
            </div>
          </div>

          <DialogFooter className="pt-2">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={isSubmitting} className="bg-rose-600 hover:bg-rose-700 text-white">
              Abrir Investigação
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
