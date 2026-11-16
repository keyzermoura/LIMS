import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  AlertOctagon,
  AlertTriangle,
  ArrowRight,
  BarChart3,
  Calendar,
  CheckCircle2,
  Clock,
  ExternalLink,
  Filter,
  Flame,
  Gauge,
  Layers,
  LineChart,
  Loader2,
  RefreshCw,
  Scale,
  ShieldAlert,
  ShieldCheck,
  TrendingDown,
  TrendingUp,
  UserCheck,
  Users,
} from "lucide-react";
import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { analyticsApi, methodsApi } from "@/lib/api";
import type {
  OperationalAnalytics,
  QualityControlAnalytics,
  TestMethod,
} from "@/lib/types";
import { cn } from "@/lib/utils";

export function AnalyticsPage() {
  const [activeTab, setActiveTab] = React.useState<"operational" | "metrological">(
    "operational"
  );
  const [selectedMethodId, setSelectedMethodId] = React.useState<string>("all");

  // Query de Métricas Operacionais
  const operationalQuery = useQuery<OperationalAnalytics>({
    queryKey: ["analytics", "operational"],
    queryFn: analyticsApi.getOperational,
    refetchInterval: 60000,
  });

  // Query de Métodos Analíticos para o filtro
  const methodsQuery = useQuery<TestMethod[]>({
    queryKey: ["methods", "catalog"],
    queryFn: () => methodsApi.list({ activeOnly: true }),
  });

  // Query de Controle de Qualidade Metrológico
  const qcQuery = useQuery<QualityControlAnalytics>({
    queryKey: ["analytics", "qc", selectedMethodId],
    queryFn: () =>
      analyticsApi.getQualityControl(
        selectedMethodId !== "all" ? selectedMethodId : undefined
      ),
    refetchInterval: 60000,
  });

  const isLoading = operationalQuery.isLoading || qcQuery.isLoading;
  const isRefetching = operationalQuery.isRefetching || qcQuery.isRefetching;

  const opData = operationalQuery.data;
  const qcData = qcQuery.data;

  return (
    <div className="space-y-6">
      {/* Header com Navegação e Ações */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between border-b pb-4">
        <div>
          <div className="flex items-center gap-2">
            <BarChart3 className="h-6 w-6 text-primary" />
            <h1 className="text-2xl font-bold tracking-tight text-foreground">
              Painéis & Indicadores Analíticos (BI & Metrologia)
            </h1>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Monitoramento de tempos de ciclo (TAT), controle estatístico de processos (ISO/IEC 17025 §7.7/§8.8) e integridade ALCOA+.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex rounded-lg border bg-muted p-1 text-muted-foreground">
            <button
              type="button"
              onClick={() => setActiveTab("operational")}
              className={cn(
                "flex items-center gap-2 rounded-md px-3 py-1.5 text-xs font-semibold transition-all",
                activeTab === "operational"
                  ? "bg-background text-foreground shadow-sm"
                  : "hover:text-foreground"
              )}
            >
              <Clock className="h-4 w-4" />
              Operacional & TAT
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("metrological")}
              className={cn(
                "flex items-center gap-2 rounded-md px-3 py-1.5 text-xs font-semibold transition-all",
                activeTab === "metrological"
                  ? "bg-background text-foreground shadow-sm"
                  : "hover:text-foreground"
              )}
            >
              <LineChart className="h-4 w-4" />
              Controle Metrológico (Shewhart)
            </button>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              operationalQuery.refetch();
              qcQuery.refetch();
            }}
            disabled={isRefetching}
            className="flex items-center gap-1.5 text-xs"
          >
            <RefreshCw className={cn("h-3.5 w-3.5", isRefetching && "animate-spin")} />
            Atualizar
          </Button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex min-h-[300px] flex-col items-center justify-center gap-3 text-muted-foreground">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-sm font-medium">Consolidando dados analíticos e séries temporais…</p>
        </div>
      ) : activeTab === "operational" && opData ? (
        /* ========================================================================= */
        /* ABA 1: OPERACIONAL, TAT E BACKLOG                                         */
        /* ========================================================================= */
        <div className="space-y-6">
          {/* Cartões Executivos de Resumo */}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {/* Card 1: Turnaround Time */}
            <Card className="border-l-4 border-l-blue-500 shadow-sm">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    TAT Global Médio
                  </span>
                  <div className="rounded-full bg-blue-100 p-2 text-blue-700 dark:bg-blue-950 dark:text-blue-300">
                    <Clock className="h-4 w-4" />
                  </div>
                </div>
                <CardTitle className="text-3xl font-extrabold text-foreground">
                  {opData.turnaround_time.global_avg_hours != null ? (
                    <>
                      {opData.turnaround_time.global_avg_hours.toFixed(1)}{" "}
                      <span className="text-sm font-normal text-muted-foreground">horas</span>
                    </>
                  ) : (
                    <span className="text-2xl font-semibold text-muted-foreground">—</span>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-xs text-muted-foreground">
                  {opData.turnaround_time.samples_measured_count > 0
                    ? `Tempo médio calculado sobre ${opData.turnaround_time.samples_measured_count} laudos concluídos.`
                    : "Dados insuficientes para cálculo de TAT."}
                </div>
              </CardContent>
            </Card>

            {/* Card 2: Conformidade Analítica */}
            <Card className="border-l-4 border-l-emerald-500 shadow-sm">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    Taxa de Conformidade
                  </span>
                  <div className="rounded-full bg-emerald-100 p-2 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300">
                    <CheckCircle2 className="h-4 w-4" />
                  </div>
                </div>
                <CardTitle className="text-3xl font-extrabold text-emerald-600 dark:text-emerald-400">
                  {opData.test_conformity.conformity_rate_pct != null ? (
                    `${opData.test_conformity.conformity_rate_pct.toFixed(1)}%`
                  ) : (
                    <span className="text-2xl font-semibold text-muted-foreground">—</span>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-xs text-muted-foreground">
                  {opData.test_conformity.total_tests > 0 ? (
                    <>
                      <span className="font-semibold text-foreground">
                        {opData.test_conformity.conforming_count}
                      </span>{" "}
                      ensaios conformes de {opData.test_conformity.total_tests} avaliados.
                    </>
                  ) : (
                    "Nenhum ensaio concluído para cálculo de conformidade."
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Card 3: Backlog de Amostras */}
            <Card className="border-l-4 border-l-amber-500 shadow-sm">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    Amostras em Processamento
                  </span>
                  <div className="rounded-full bg-amber-100 p-2 text-amber-700 dark:bg-amber-950 dark:text-amber-300">
                    <Layers className="h-4 w-4" />
                  </div>
                </div>
                <CardTitle className="text-3xl font-extrabold text-amber-600 dark:text-amber-400">
                  {opData.sample_backlog.total_active}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                  {opData.sample_backlog.age_above_15_days > 0 ? (
                    <span className="font-semibold text-rose-600 dark:text-rose-400">
                      ⚠ {opData.sample_backlog.age_above_15_days} em risco (&gt;15d)
                    </span>
                  ) : (
                    <span>Nenhuma amostra em atraso crítico.</span>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Card 4: Eficácia CAPA */}
            <Card className="border-l-4 border-l-purple-500 shadow-sm">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    Eficácia de Planos CAPA
                  </span>
                  <div className="rounded-full bg-purple-100 p-2 text-purple-700 dark:bg-purple-950 dark:text-purple-300">
                    <ShieldCheck className="h-4 w-4" />
                  </div>
                </div>
                <CardTitle className="text-3xl font-extrabold text-purple-600 dark:text-purple-400">
                  {opData.capa_metrics.effectiveness_rate_pct != null ? (
                    `${opData.capa_metrics.effectiveness_rate_pct.toFixed(1)}%`
                  ) : (
                    <span className="text-2xl font-semibold text-muted-foreground">—</span>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-xs text-muted-foreground">
                  {opData.capa_metrics.effective_capas + opData.capa_metrics.ineffective_capas > 0 ? (
                    <>
                      <span className="font-semibold text-foreground">
                        {opData.capa_metrics.effective_capas}
                      </span>{" "}
                      ações eficazes avaliadas temporalmente.
                    </>
                  ) : (
                    "Nenhuma ação CAPA avaliada quanto à eficácia até o momento."
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Seção 2: Composição Detalhada do TAT & Estratificação de Backlog */}
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Box 1: Composição do TAT */}
            <Card className="shadow-sm">
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Clock className="h-4 w-4 text-blue-600" />
                  Distribuição do Tempo de Ciclo por Etapa (Horas)
                </CardTitle>
                <CardDescription>
                  Identificação visual de gargalos entre recebimento, execução analítica, revisão e emissão pericial.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {opData.turnaround_time.global_avg_hours != null ? (
                  <>
                    <div className="space-y-3">
                      {/* Etapa 1 */}
                      <div>
                        <div className="flex justify-between text-xs font-medium mb-1">
                          <span className="text-muted-foreground">1. Recebimento $\rightarrow$ Execução do Ensaio</span>
                          <span className="font-semibold text-foreground">
                            {opData.turnaround_time.receipt_to_testing_avg_hours != null
                              ? `${opData.turnaround_time.receipt_to_testing_avg_hours.toFixed(1)}h`
                              : "—"}
                          </span>
                        </div>
                        <div className="h-3 w-full bg-muted rounded-full overflow-hidden">
                          <div
                            className="h-full bg-blue-500 rounded-full transition-all"
                            style={{
                              width: `${Math.min(
                                100,
                                ((opData.turnaround_time.receipt_to_testing_avg_hours ?? 0) /
                                  (opData.turnaround_time.global_avg_hours || 1)) *
                                  100
                              )}%`,
                            }}
                          />
                        </div>
                      </div>

                      {/* Etapa 2 */}
                      <div>
                        <div className="flex justify-between text-xs font-medium mb-1">
                          <span className="text-muted-foreground">2. Execução $\rightarrow$ Revisão Técnica</span>
                          <span className="font-semibold text-foreground">
                            {opData.turnaround_time.testing_to_review_avg_hours != null
                              ? `${opData.turnaround_time.testing_to_review_avg_hours.toFixed(1)}h`
                              : "—"}
                          </span>
                        </div>
                        <div className="h-3 w-full bg-muted rounded-full overflow-hidden">
                          <div
                            className="h-full bg-indigo-500 rounded-full transition-all"
                            style={{
                              width: `${Math.min(
                                100,
                                ((opData.turnaround_time.testing_to_review_avg_hours ?? 0) /
                                  (opData.turnaround_time.global_avg_hours || 1)) *
                                  100
                              )}%`,
                            }}
                          />
                        </div>
                      </div>

                      {/* Etapa 3 */}
                      <div>
                        <div className="flex justify-between text-xs font-medium mb-1">
                          <span className="text-muted-foreground">3. Revisão $\rightarrow$ Emissão do Laudo</span>
                          <span className="font-semibold text-foreground">
                            {opData.turnaround_time.review_to_report_avg_hours != null
                              ? `${opData.turnaround_time.review_to_report_avg_hours.toFixed(1)}h`
                              : "—"}
                          </span>
                        </div>
                        <div className="h-3 w-full bg-muted rounded-full overflow-hidden">
                          <div
                            className="h-full bg-emerald-500 rounded-full transition-all"
                            style={{
                              width: `${Math.min(
                                100,
                                ((opData.turnaround_time.review_to_report_avg_hours ?? 0) /
                                  (opData.turnaround_time.global_avg_hours || 1)) *
                                  100
                              )}%`,
                            }}
                          />
                        </div>
                      </div>
                    </div>

                    <div className="rounded-lg border bg-muted/40 p-3 text-xs text-muted-foreground mt-4">
                      💡 <strong>Análise de Eficiência:</strong> A etapa de conferência e recebimento até início de ensaio consome{" "}
                      <strong>
                        {(
                          ((opData.turnaround_time.receipt_to_testing_avg_hours ?? 0) /
                            (opData.turnaround_time.global_avg_hours || 1)) *
                          100
                        ).toFixed(0)}
                        %
                      </strong>{" "}
                      do tempo total do ciclo analítico.
                    </div>
                  </>
                ) : (
                  <div className="p-8 text-center text-xs text-muted-foreground">
                    Dados insuficientes de ciclo (TAT). São necessários laudos concluídos para estratificação por etapa.
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Box 2: Estratificação Etária do Backlog */}
            <Card className="shadow-sm">
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Layers className="h-4 w-4 text-amber-600" />
                  Estratificação do Backlog de Amostras
                </CardTitle>
                <CardDescription>
                  Monitoramento preventivo do tempo de retenção em bancada antes do laudo final.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-3 gap-3">
                  <div className="rounded-lg border border-emerald-200 bg-emerald-50/50 p-3 dark:border-emerald-900 dark:bg-emerald-950/20 text-center">
                    <span className="text-xs font-medium text-emerald-700 dark:text-emerald-300">0 a 5 dias</span>
                    <p className="text-2xl font-bold text-emerald-800 dark:text-emerald-200 mt-1">
                      {opData.sample_backlog.age_0_to_5_days}
                    </p>
                    <span className="text-[10px] text-muted-foreground">Dentro do prazo</span>
                  </div>

                  <div className="rounded-lg border border-amber-200 bg-amber-50/50 p-3 dark:border-amber-900 dark:bg-amber-950/20 text-center">
                    <span className="text-xs font-medium text-amber-700 dark:text-amber-300">6 a 15 dias</span>
                    <p className="text-2xl font-bold text-amber-800 dark:text-amber-200 mt-1">
                      {opData.sample_backlog.age_6_to_15_days}
                    </p>
                    <span className="text-[10px] text-muted-foreground">Atenção</span>
                  </div>

                  <div className="rounded-lg border border-rose-200 bg-rose-50/50 p-3 dark:border-rose-900 dark:bg-rose-950/20 text-center">
                    <span className="text-xs font-medium text-rose-700 dark:text-rose-300">&gt; 15 dias</span>
                    <p className="text-2xl font-bold text-rose-800 dark:text-rose-200 mt-1">
                      {opData.sample_backlog.age_above_15_days}
                    </p>
                    <span className="text-[10px] text-rose-600 dark:text-rose-400 font-semibold">Crítico</span>
                  </div>
                </div>

                {/* Status de Equipamentos */}
                <div className="rounded-lg border p-3 mt-4">
                  <span className="text-xs font-semibold text-foreground flex items-center gap-1.5 mb-2">
                    <Gauge className="h-3.5 w-3.5 text-primary" />
                    Parque Metrológico de Equipamentos
                  </span>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="flex justify-between py-1 border-b">
                      <span className="text-muted-foreground">Calibrados & Vigentes:</span>
                      <span className="font-semibold text-emerald-600">
                        {opData.equipment_status_summary["CALIBRADO"] ?? 0}
                      </span>
                    </div>
                    <div className="flex justify-between py-1 border-b">
                      <span className="text-muted-foreground">Calibração Vencida:</span>
                      <span className="font-semibold text-rose-600">
                        {opData.equipment_status_summary["VENCIDO"] ?? 0}
                      </span>
                    </div>
                    <div className="flex justify-between py-1 border-b">
                      <span className="text-muted-foreground">Em Manutenção:</span>
                      <span className="font-semibold text-amber-600">
                        {opData.equipment_status_summary["EM_MANUTENCAO"] ?? 0}
                      </span>
                    </div>
                    <div className="flex justify-between py-1 border-b">
                      <span className="text-muted-foreground">Não Aplicável:</span>
                      <span className="font-semibold text-muted-foreground">
                        {opData.equipment_status_summary["NAO_APLICAVEL"] ?? 0}
                      </span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Seção 3: Produtividade e Carga da Equipe Técnica */}
          <Card className="shadow-sm">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Users className="h-4 w-4 text-purple-600" />
                Carga de Trabalho da Equipe Técnica e Analistas
              </CardTitle>
              <CardDescription>
                Acompanhamento em tempo real da distribuição de ensaios e produtividade analítica.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b text-muted-foreground text-left">
                      <th className="py-2 font-medium">Analista / Técnico</th>
                      <th className="py-2 font-medium text-center">Ensaios em Andamento</th>
                      <th className="py-2 font-medium text-center">Ensaios Concluídos</th>
                      <th className="py-2 font-medium text-center">Volume Total</th>
                      <th className="py-2 font-medium text-right">Ação</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {opData.analysts_workload.map((a) => (
                      <tr key={a.user_id} className="hover:bg-muted/30">
                        <td className="py-2.5 font-semibold text-foreground flex items-center gap-2">
                          <UserCheck className="h-3.5 w-3.5 text-muted-foreground" />
                          {a.full_name}
                        </td>
                        <td className="py-2.5 text-center">
                          <span className="inline-flex items-center rounded-full bg-amber-50 px-2 py-0.5 text-xs font-semibold text-amber-700 dark:bg-amber-950 dark:text-amber-300">
                            {a.active_tests_count}
                          </span>
                        </td>
                        <td className="py-2.5 text-center">
                          <span className="inline-flex items-center rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-semibold text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300">
                            {a.completed_tests_count}
                          </span>
                        </td>
                        <td className="py-2.5 text-center font-bold text-foreground">
                          {a.active_tests_count + a.completed_tests_count}
                        </td>
                        <td className="py-2.5 text-right">
                          <Link
                            to="/tests"
                            className="text-primary hover:underline font-medium inline-flex items-center gap-1"
                          >
                            Ver ensaios <ArrowRight className="h-3 w-3" />
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </div>
      ) : activeTab === "metrological" && qcData ? (
        /* ========================================================================= */
        /* ABA 2: CONTROLE METROLÓGICO (SHEWHART / LEVEY-JENNINGS & WESTGARD)       */
        /* ========================================================================= */
        <div className="space-y-6">
          {/* Seletor de Método e Filtros */}
          <Card className="shadow-sm">
            <CardContent className="p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="flex items-center gap-3 w-full sm:w-auto">
                <Filter className="h-4 w-4 text-muted-foreground" />
                <span className="text-xs font-medium text-foreground whitespace-nowrap">
                  Filtrar Método Analítico:
                </span>
                <Select
                  value={selectedMethodId}
                  onValueChange={(val) => setSelectedMethodId(val)}
                >
                  <SelectTrigger className="h-8 text-xs w-[280px]">
                    <SelectValue placeholder="Selecione um método..." />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Todos os métodos (Geral)</SelectItem>
                    {methodsQuery.data?.map((m) => (
                      <SelectItem key={m.id} value={m.id}>
                        {m.code} — {m.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="flex items-center gap-2">
                {qcData.mean == null ? (
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-100 px-3 py-1 text-xs font-bold text-amber-800 dark:bg-amber-950 dark:text-amber-300">
                    <AlertCircle className="h-3.5 w-3.5" />
                    DADOS INSUFICIENTES
                  </span>
                ) : qcData.violations.length === 0 ? (
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-100 px-3 py-1 text-xs font-bold text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
                    <ShieldCheck className="h-3.5 w-3.5" />
                    PROCESSO SOB CONTROLE ESTATÍSTICO
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-rose-100 px-3 py-1 text-xs font-bold text-rose-800 dark:bg-rose-950 dark:text-rose-300">
                    <ShieldAlert className="h-3.5 w-3.5" />
                    {qcData.violations.length} VIOLAÇÃO(ÕES) DE WESTGARD DETECTADA(S)
                  </span>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Parâmetros Estatísticos da Carta de Controle */}
          {qcData.mean != null && qcData.standard_deviation != null ? (
            <>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="rounded-lg border bg-card p-3 shadow-sm">
                  <span className="text-[11px] font-semibold text-muted-foreground uppercase">Média ($\mu$)</span>
                  <p className="text-xl font-bold text-foreground mt-0.5">
                    {qcData.mean.toFixed(3)} <span className="text-xs font-normal text-muted-foreground">{qcData.unit}</span>
                  </p>
                </div>
                <div className="rounded-lg border bg-card p-3 shadow-sm">
                  <span className="text-[11px] font-semibold text-muted-foreground uppercase">Desvio-Padrão ($\sigma$)</span>
                  <p className="text-xl font-bold text-foreground mt-0.5">
                    {qcData.standard_deviation.toFixed(3)}
                  </p>
                </div>
                <div className="rounded-lg border bg-card p-3 shadow-sm border-l-4 border-l-amber-500">
                  <span className="text-[11px] font-semibold text-amber-700 dark:text-amber-300 uppercase">Faixa de Alerta (±2$\sigma$)</span>
                  <p className="text-sm font-semibold text-foreground mt-1">
                    [{qcData.warning_limit_lower?.toFixed(2) ?? "—"} ; {qcData.warning_limit_upper?.toFixed(2) ?? "—"}]
                  </p>
                </div>
                <div className="rounded-lg border bg-card p-3 shadow-sm border-l-4 border-l-rose-500">
                  <span className="text-[11px] font-semibold text-rose-700 dark:text-rose-300 uppercase">Faixa de Ação (±3$\sigma$)</span>
                  <p className="text-sm font-semibold text-foreground mt-1">
                    [{qcData.action_limit_lower?.toFixed(2) ?? "—"} ; {qcData.action_limit_upper?.toFixed(2) ?? "—"}]
                  </p>
                </div>
              </div>

              {/* Gráfico Visual da Carta de Controle de Shewhart / Levey-Jennings em SVG */}
              <Card className="shadow-sm">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="text-base flex items-center gap-2">
                        <LineChart className="h-4 w-4 text-primary" />
                        Carta de Controle de Levey-Jennings ({qcData.method_name})
                      </CardTitle>
                      <CardDescription>
                        Série temporal das corridas de controle com limites $\pm 1\sigma, \pm 2\sigma, \pm 3\sigma$ (ISO 17025 §7.7).
                      </CardDescription>
                    </div>
                    <div className="flex items-center gap-4 text-[11px] font-medium text-muted-foreground">
                      <span className="flex items-center gap-1.5">
                        <span className="inline-block h-2 w-2 rounded-full bg-blue-600" />
                        Média ($\mu$)
                      </span>
                      <span className="flex items-center gap-1.5">
                        <span className="inline-block h-2 w-2 rounded-full bg-amber-500" />
                        Alerta ($\pm 2\sigma$)
                      </span>
                      <span className="flex items-center gap-1.5">
                        <span className="inline-block h-2 w-2 rounded-full bg-rose-600" />
                        Ação / Rejeição ($\pm 3\sigma$)
                      </span>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  {/* SVG Gráfico */}
                  <div className="relative w-full h-[280px] bg-slate-950/5 dark:bg-slate-950/40 rounded-lg p-2 border">
                    {(() => {
                      const pts = qcData.data_points;
                      if (!pts || pts.length === 0 || qcData.action_limit_lower == null || qcData.action_limit_upper == null || qcData.standard_deviation == null) return null;

                      const minVal = qcData.action_limit_lower - 0.5 * qcData.standard_deviation;
                      const maxVal = qcData.action_limit_upper + 0.5 * qcData.standard_deviation;
                      const range = maxVal - minVal || 1;

                      const getY = (val: number) => {
                        const norm = (val - minVal) / range;
                        return 240 - norm * 200; // Inverte Y para SVG (20px top, 240px bottom)
                      };

                      const getX = (idx: number) => {
                        const step = 700 / (pts.length + 1);
                        return 50 + (idx + 1) * step;
                      };

                      return (
                        <svg viewBox="0 0 800 260" className="w-full h-full">
                          {/* Linhas de Grade e Limites */}
                          {/* +3s Ação Superior */}
                          <line
                            x1="40"
                            y1={getY(qcData.action_limit_upper)}
                            x2="780"
                            y2={getY(qcData.action_limit_upper)}
                            stroke="#e11d48"
                            strokeDasharray="4 4"
                            strokeWidth="1.5"
                          />
                          <text
                            x="785"
                            y={getY(qcData.action_limit_upper) + 3}
                            fill="#e11d48"
                            fontSize="9"
                            fontWeight="bold"
                          >
                            +3σ ({qcData.action_limit_upper.toFixed(1)})
                          </text>

                          {/* +2s Alerta Superior */}
                          {qcData.warning_limit_upper != null && (
                            <>
                              <line
                                x1="40"
                                y1={getY(qcData.warning_limit_upper)}
                                x2="780"
                                y2={getY(qcData.warning_limit_upper)}
                                stroke="#f59e0b"
                                strokeDasharray="3 3"
                                strokeWidth="1.2"
                              />
                              <text
                                x="785"
                                y={getY(qcData.warning_limit_upper) + 3}
                                fill="#f59e0b"
                                fontSize="9"
                              >
                                +2σ ({qcData.warning_limit_upper.toFixed(1)})
                              </text>
                            </>
                          )}

                          {/* Linha Central (Média) */}
                          {qcData.mean != null && (
                            <>
                              <line
                                x1="40"
                                y1={getY(qcData.mean)}
                                x2="780"
                                y2={getY(qcData.mean)}
                                stroke="#2563eb"
                                strokeWidth="2"
                              />
                              <text
                                x="785"
                                y={getY(qcData.mean) + 3}
                                fill="#2563eb"
                                fontSize="9"
                                fontWeight="bold"
                              >
                                μ ({qcData.mean.toFixed(1)})
                              </text>
                            </>
                          )}

                          {/* -2s Alerta Inferior */}
                          {qcData.warning_limit_lower != null && (
                            <>
                              <line
                                x1="40"
                                y1={getY(qcData.warning_limit_lower)}
                                x2="780"
                                y2={getY(qcData.warning_limit_lower)}
                                stroke="#f59e0b"
                                strokeDasharray="3 3"
                                strokeWidth="1.2"
                              />
                              <text
                                x="785"
                                y={getY(qcData.warning_limit_lower) + 3}
                                fill="#f59e0b"
                                fontSize="9"
                              >
                                -2σ ({qcData.warning_limit_lower.toFixed(1)})
                              </text>
                            </>
                          )}

                          {/* -3s Ação Inferior */}
                          {qcData.action_limit_lower != null && (
                            <>
                              <line
                                x1="40"
                                y1={getY(qcData.action_limit_lower)}
                                x2="780"
                                y2={getY(qcData.action_limit_lower)}
                                stroke="#e11d48"
                                strokeDasharray="4 4"
                                strokeWidth="1.5"
                              />
                              <text
                                x="785"
                                y={getY(qcData.action_limit_lower) + 3}
                                fill="#e11d48"
                                fontSize="9"
                                fontWeight="bold"
                              >
                                -3σ ({qcData.action_limit_lower.toFixed(1)})
                              </text>
                            </>
                          )}

                          {/* Linha conectando os pontos */}
                          <polyline
                            fill="none"
                            stroke="#64748b"
                            strokeWidth="1.5"
                            points={pts.map((p, i) => `${getX(i)},${getY(p.value)}`).join(" ")}
                          />

                          {/* Pontos plotados */}
                          {pts.map((p, i) => {
                            const isViolated = Boolean(p.violation);
                            return (
                              <g key={p.run_number}>
                                <circle
                                  cx={getX(i)}
                                  cy={getY(p.value)}
                                  r={isViolated ? 6 : 4}
                                  fill={isViolated ? "#e11d48" : "#2563eb"}
                                  stroke="#ffffff"
                                  strokeWidth="1.5"
                                  className="transition-all hover:scale-125 cursor-pointer"
                                />
                                {isViolated && (
                                  <text
                                    x={getX(i)}
                                    y={getY(p.value) - 10}
                                    fill="#e11d48"
                                    fontSize="8"
                                    fontWeight="bold"
                                    textAnchor="middle"
                                  >
                                    {p.violation}
                                  </text>
                                )}
                              </g>
                            );
                          })}
                        </svg>
                      );
                    })()}
                  </div>
                </CardContent>
              </Card>
            </>
          ) : (
            <div className="rounded-xl border border-dashed p-8 text-center bg-card shadow-sm">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-amber-100 text-amber-600 dark:bg-amber-950 dark:text-amber-400 mb-3">
                <AlertCircle className="h-6 w-6" />
              </div>
              <h3 className="text-base font-bold text-foreground">Dados Insuficientes para Carta de Controle (ISO/IEC 17025 §7.7)</h3>
              <p className="text-xs text-muted-foreground mt-1 max-w-lg mx-auto">
                São necessárias corridas analíticas reais cadastradas para este método para calcular a média histórica ($\mu$) e desvio padrão ($\sigma$). {qcData.data_points.length} ponto(s) registrado(s) no momento.
              </p>
            </div>
          )}

          {/* Violações de Westgard Detectadas */}
          {qcData.violations.length > 0 && (
            <Card className="border-rose-200 bg-rose-50/30 dark:border-rose-900/40 dark:bg-rose-950/10 shadow-sm">
              <CardHeader className="pb-2">
                <CardTitle className="text-base font-bold text-rose-800 dark:text-rose-300 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <AlertOctagon className="h-5 w-5 text-rose-600" />
                    Regras de Westgard Violadas (ISO 17025 §7.7)
                  </div>
                  <Link to="/capas">
                    <Button size="sm" variant="destructive" className="text-xs h-7">
                      Abrir CAPA Imediata
                    </Button>
                  </Link>
                </CardTitle>
                <CardDescription className="text-xs text-rose-700/80 dark:text-rose-300/70">
                  Desvios estatísticos exigem investigação de causa raiz para evitar laudos com erros sistemáticos.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                {qcData.violations.map((v, i) => (
                  <div
                    key={i}
                    className="flex items-start gap-3 rounded-md border border-rose-200 bg-background/80 p-3 text-xs dark:border-rose-900/50"
                  >
                    <span className="rounded bg-rose-600 px-2 py-0.5 font-mono text-[11px] font-bold text-white">
                      Regra {v.rule_code}
                    </span>
                    <div className="flex-1">
                      <p className="font-semibold text-foreground">{v.description}</p>
                      <p className="text-[11px] text-muted-foreground mt-0.5">
                        Corridas afetadas: #{v.run_numbers.join(", #")} | Severidade:{" "}
                        <span className="font-bold text-rose-600">{v.severity}</span>
                      </p>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {/* Tabela de Pontos Amostrais */}
          <Card className="shadow-sm">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold flex items-center gap-2">
                <Layers className="h-4 w-4 text-muted-foreground" />
                Histórico Detalhado das Corridas de Controle Metrológico
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto max-h-[260px]">
                <table className="w-full text-xs">
                  <thead className="sticky top-0 bg-background border-b">
                    <tr className="text-muted-foreground text-left">
                      <th className="py-2 font-medium">Corrida #</th>
                      <th className="py-2 font-medium">Data / Hora</th>
                      <th className="py-2 font-medium">Operador</th>
                      <th className="py-2 font-medium text-right">Valor Medido ({qcData.unit})</th>
                      <th className="py-2 font-medium text-center">Desvio da Média</th>
                      <th className="py-2 font-medium text-center">Status / Violação</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {qcData.data_points.map((p) => {
                      const diff = qcData.mean != null ? p.value - qcData.mean : 0;
                      const sigmas =
                        qcData.standard_deviation != null && qcData.standard_deviation > 0
                          ? diff / qcData.standard_deviation
                          : 0;
                      return (
                        <tr key={p.run_number} className="hover:bg-muted/30">
                          <td className="py-2 font-bold font-mono">#{p.run_number}</td>
                          <td className="py-2 text-muted-foreground">{p.measured_at}</td>
                          <td className="py-2 text-foreground font-medium">{p.operator_name}</td>
                          <td className="py-2 text-right font-mono font-bold text-foreground">
                            {p.value.toFixed(3)}
                          </td>
                          <td className="py-2 text-center font-mono text-[11px]">
                            {qcData.mean != null && qcData.standard_deviation != null
                              ? sigmas >= 0
                                ? `+${sigmas.toFixed(2)}σ`
                                : `${sigmas.toFixed(2)}σ`
                              : "—"}
                          </td>
                          <td className="py-2 text-center">
                            {p.violation ? (
                              <span className="inline-flex items-center rounded bg-rose-100 px-1.5 py-0.5 text-[10px] font-bold text-rose-800 dark:bg-rose-950 dark:text-rose-300">
                                {p.violation}
                              </span>
                            ) : (
                              <span className="inline-flex items-center rounded bg-emerald-100 px-1.5 py-0.5 text-[10px] font-semibold text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
                                Normal
                              </span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </div>
      ) : null}
    </div>
  );
}
