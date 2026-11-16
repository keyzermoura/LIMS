import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertOctagon,
  AlertTriangle,
  Bell,
  Check,
  CheckCheck,
  Clock,
  ExternalLink,
  Filter,
  Info,
  Layers,
  Loader2,
  RefreshCw,
  Search,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { Link, useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useToast } from "@/components/ui/toast";
import { notificationsApi } from "@/lib/api";
import type {
  AlertCheckResult,
  NotificationCategory,
  NotificationItem,
  NotificationSeverity,
  NotificationSummary,
} from "@/lib/types";
import { cn, formatDateTime, relativeTime } from "@/lib/utils";

const CATEGORY_LABELS: Record<NotificationCategory, string> = {
  CALIBRATION: "Equipamentos / Calibração",
  COMPETENCE: "Qualificação de Analistas",
  CAPA: "Ações Corretivas (CAPA)",
  TAT: "Tempos de Ciclo (TAT)",
  SAMPLE_ISSUE: "Integridade de Amostras",
  SYSTEM: "Sistema / Geral",
};

export function NotificationsPage() {
  const [selectedSeverity, setSelectedSeverity] = React.useState<string>("ALL");
  const [unreadOnly, setUnreadOnly] = React.useState<boolean>(false);
  const [searchFilter, setSearchFilter] = React.useState<string>("");

  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { toast } = useToast();

  // Queries
  const summaryQuery = useQuery<NotificationSummary>({
    queryKey: ["notifications", "summary"],
    queryFn: notificationsApi.getSummary,
    refetchInterval: 30000,
  });

  const listQuery = useQuery<NotificationItem[]>({
    queryKey: ["notifications", "list", unreadOnly, selectedSeverity],
    queryFn: () =>
      notificationsApi.list({
        unread_only: unreadOnly,
        severity: selectedSeverity !== "ALL" ? selectedSeverity : undefined,
        limit: 100,
      }),
    refetchInterval: 30000,
  });

  // Mutations
  const markReadMutation = useMutation({
    mutationFn: notificationsApi.markAsRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      toast({
        title: "Notificação lida",
        description: "Status da notificação atualizado com sucesso.",
      });
    },
  });

  const markAllMutation = useMutation({
    mutationFn: notificationsApi.markAllAsRead,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      toast({
        title: "Notificações marcadas",
        description: `${data.marked_count} notificação(ões) marcada(s) como lida(s).`,
      });
    },
  });

  const checkAlertsMutation = useMutation({
    mutationFn: notificationsApi.checkAlerts,
    onSuccess: (data: AlertCheckResult) => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      toast({
        title: "Varredura do Laboratório Concluída",
        description:
          data.alerts_generated > 0
            ? `${data.alerts_generated} novo(s) alerta(s) emitido(s) com sucesso.`
            : "Nenhum novo desvio identificado. Laboratório sob controle.",
      });
    },
  });

  const summary = summaryQuery.data ?? {
    unread_count: 0,
    critical_count: 0,
    warning_count: 0,
    info_count: 0,
  };

  const notifications = (listQuery.data ?? []).filter((item) => {
    if (!searchFilter.trim()) return true;
    const q = searchFilter.toLowerCase();
    return (
      item.title.toLowerCase().includes(q) ||
      item.message.toLowerCase().includes(q)
    );
  });

  function handleActionClick(item: NotificationItem) {
    if (!item.is_read) {
      markReadMutation.mutate(item.id);
    }
    if (item.link_url) {
      navigate(item.link_url);
    }
  }

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between border-b pb-4">
        <div>
          <div className="flex items-center gap-2">
            <Bell className="h-6 w-6 text-primary" />
            <h1 className="text-2xl font-bold tracking-tight text-foreground">
              Central de Notificações e Alertas em Tempo Real
            </h1>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Monitoramento contínuo de desvios metrológicos, calibrações a vencer, competências de bancada e ações corretivas.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => checkAlertsMutation.mutate()}
            disabled={checkAlertsMutation.isPending}
            className="flex items-center gap-1.5 text-xs"
          >
            <Sparkles className={cn("h-3.5 w-3.5 text-primary", checkAlertsMutation.isPending && "animate-spin")} />
            Verificar Desvios do Sistema
          </Button>

          {summary.unread_count > 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => markAllMutation.mutate()}
              disabled={markAllMutation.isPending}
              className="flex items-center gap-1.5 text-xs"
            >
              <CheckCheck className="h-3.5 w-3.5 text-emerald-600" />
              Marcar Todas como Lidas
            </Button>
          )}

          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              summaryQuery.refetch();
              listQuery.refetch();
            }}
            disabled={listQuery.isRefetching}
            className="flex items-center gap-1 text-xs"
          >
            <RefreshCw className={cn("h-3.5 w-3.5", listQuery.isRefetching && "animate-spin")} />
          </Button>
        </div>
      </div>

      {/* Cards de Resumo */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card className="border-l-4 border-l-slate-500 shadow-sm">
          <CardHeader className="pb-2">
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Total Não Lidas
            </span>
            <CardTitle className="text-3xl font-extrabold text-foreground">
              {summary.unread_count}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-xs text-muted-foreground">
              Alertas ativos aguardando ciência do operador.
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-rose-500 shadow-sm">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-rose-700 dark:text-rose-300 uppercase tracking-wider">
                Alertas Críticos
              </span>
              <AlertOctagon className="h-4 w-4 text-rose-600" />
            </div>
            <CardTitle className="text-3xl font-extrabold text-rose-600 dark:text-rose-400">
              {summary.critical_count}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-xs text-muted-foreground">
              Intertravamentos ou desvios regulatórios graves.
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-amber-500 shadow-sm">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-amber-700 dark:text-amber-300 uppercase tracking-wider">
                Avisos / Atenção
              </span>
              <AlertTriangle className="h-4 w-4 text-amber-600" />
            </div>
            <CardTitle className="text-3xl font-extrabold text-amber-600 dark:text-amber-400">
              {summary.warning_count}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-xs text-muted-foreground">
              Prazos a vencer ou tendências estatísticas.
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-blue-500 shadow-sm">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-blue-700 dark:text-blue-300 uppercase tracking-wider">
                Informativos
              </span>
              <Info className="h-4 w-4 text-blue-600" />
            </div>
            <CardTitle className="text-3xl font-extrabold text-blue-600 dark:text-blue-400">
              {summary.info_count}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-xs text-muted-foreground">
              Comunicações e eventos de rotina do laboratório.
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Barra de Filtros e Busca */}
      <Card className="shadow-sm">
        <CardContent className="p-4 flex flex-col md:flex-row items-center justify-between gap-4">
          {/* Tabs de Severidade */}
          <div className="flex rounded-lg border bg-muted p-1 text-muted-foreground w-full md:w-auto">
            <button
              type="button"
              onClick={() => setSelectedSeverity("ALL")}
              className={cn(
                "rounded-md px-3 py-1.5 text-xs font-semibold transition-all",
                selectedSeverity === "ALL"
                  ? "bg-background text-foreground shadow-sm"
                  : "hover:text-foreground"
              )}
            >
              Todas
            </button>
            <button
              type="button"
              onClick={() => setSelectedSeverity("CRITICAL")}
              className={cn(
                "rounded-md px-3 py-1.5 text-xs font-semibold transition-all flex items-center gap-1.5",
                selectedSeverity === "CRITICAL"
                  ? "bg-background text-rose-600 shadow-sm"
                  : "hover:text-foreground"
              )}
            >
              <AlertOctagon className="h-3 w-3 text-rose-600" />
              Críticas
            </button>
            <button
              type="button"
              onClick={() => setSelectedSeverity("WARNING")}
              className={cn(
                "rounded-md px-3 py-1.5 text-xs font-semibold transition-all flex items-center gap-1.5",
                selectedSeverity === "WARNING"
                  ? "bg-background text-amber-600 shadow-sm"
                  : "hover:text-foreground"
              )}
            >
              <AlertTriangle className="h-3 w-3 text-amber-600" />
              Atenção
            </button>
            <button
              type="button"
              onClick={() => setSelectedSeverity("INFO")}
              className={cn(
                "rounded-md px-3 py-1.5 text-xs font-semibold transition-all flex items-center gap-1.5",
                selectedSeverity === "INFO"
                  ? "bg-background text-blue-600 shadow-sm"
                  : "hover:text-foreground"
              )}
            >
              <Info className="h-3 w-3 text-blue-600" />
              Informativas
            </button>
          </div>

          {/* Filtro de Leitura e Campo de Busca */}
          <div className="flex items-center gap-3 w-full md:w-auto">
            <label className="flex items-center gap-2 text-xs font-medium text-foreground cursor-pointer whitespace-nowrap">
              <input
                type="checkbox"
                checked={unreadOnly}
                onChange={(e) => setUnreadOnly(e.target.checked)}
                className="rounded border-border text-primary focus:ring-primary h-4 w-4"
              />
              Apenas não lidas
            </label>

            <div className="relative w-full md:w-64">
              <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
              <Input
                placeholder="Buscar por texto..."
                value={searchFilter}
                onChange={(e) => setSearchFilter(e.target.value)}
                className="h-8 pl-8 text-xs"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Lista de Notificações */}
      <div className="space-y-3">
        {listQuery.isLoading ? (
          <div className="flex min-h-[200px] flex-col items-center justify-center gap-3 text-muted-foreground">
            <Loader2 className="h-6 w-6 animate-spin text-primary" />
            <p className="text-xs">Carregando histórico de notificações…</p>
          </div>
        ) : notifications.length === 0 ? (
          <Card className="py-12 text-center shadow-sm">
            <Check className="h-10 w-10 text-emerald-500 mx-auto mb-2 opacity-80" />
            <p className="text-sm font-semibold text-foreground">Nenhuma notificação encontrada</p>
            <p className="text-xs text-muted-foreground mt-0.5">
              Não há alertas pendentes para os filtros selecionados.
            </p>
          </Card>
        ) : (
          notifications.map((item) => {
            const isCritical = item.severity === "CRITICAL";
            const isWarning = item.severity === "WARNING";

            return (
              <Card
                key={item.id}
                className={cn(
                  "border-l-4 transition-all shadow-sm",
                  isCritical
                    ? "border-l-rose-500 bg-rose-50/20 dark:bg-rose-950/10"
                    : isWarning
                    ? "border-l-amber-500 bg-amber-50/20 dark:bg-amber-950/10"
                    : "border-l-blue-500 bg-card",
                  !item.is_read && "ring-1 ring-primary/20"
                )}
              >
                <CardContent className="p-4">
                  <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                    <div className="flex items-start gap-3">
                      <div className="mt-0.5 shrink-0">
                        {isCritical ? (
                          <div className="rounded-full bg-rose-100 p-2 text-rose-600 dark:bg-rose-950 dark:text-rose-400">
                            <AlertOctagon className="h-4 w-4" />
                          </div>
                        ) : isWarning ? (
                          <div className="rounded-full bg-amber-100 p-2 text-amber-600 dark:bg-amber-950 dark:text-amber-400">
                            <AlertTriangle className="h-4 w-4" />
                          </div>
                        ) : (
                          <div className="rounded-full bg-sky-100 p-2 text-sky-600 dark:bg-sky-950 dark:text-sky-400">
                            <Info className="h-4 w-4" />
                          </div>
                        )}
                      </div>

                      <div className="space-y-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <h3 className="text-sm font-bold text-foreground">
                            {item.title}
                          </h3>
                          <span className="rounded bg-muted px-2 py-0.5 text-[10px] font-semibold text-muted-foreground uppercase">
                            {CATEGORY_LABELS[item.category] ?? item.category}
                          </span>
                          {!item.is_read ? (
                            <span className="inline-flex items-center rounded-full bg-primary/10 px-2 py-0.5 text-[10px] font-bold text-primary">
                              Nova
                            </span>
                          ) : (
                            <span className="text-[10px] text-muted-foreground">
                              Lida
                            </span>
                          )}
                        </div>

                        <p className="text-xs text-muted-foreground leading-relaxed">
                          {item.message}
                        </p>

                        <div className="flex items-center gap-3 text-[11px] text-muted-foreground pt-1">
                          <span className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {formatDateTime(item.created_at)} ({relativeTime(item.created_at)})
                          </span>
                          {item.target_role && (
                            <span>Perfil: <strong>{item.target_role}</strong></span>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 shrink-0 self-end sm:self-start">
                      {!item.is_read && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => markReadMutation.mutate(item.id)}
                          disabled={markReadMutation.isPending}
                          className="h-8 text-xs text-muted-foreground hover:text-foreground"
                        >
                          <Check className="h-3.5 w-3.5 mr-1" />
                          Marcar lida
                        </Button>
                      )}

                      {item.link_url && (
                        <Button
                          size="sm"
                          variant={isCritical ? "destructive" : "default"}
                          onClick={() => handleActionClick(item)}
                          className="h-8 text-xs font-semibold flex items-center gap-1.5"
                        >
                          Acessar <ExternalLink className="h-3 w-3" />
                        </Button>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })
        )}
      </div>
    </div>
  );
}
