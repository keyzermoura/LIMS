import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertOctagon,
  AlertTriangle,
  Bell,
  Check,
  CheckCheck,
  ExternalLink,
  Info,
  Loader2,
} from "lucide-react";
import { Link, useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { notificationsApi } from "@/lib/api";
import type { NotificationItem, NotificationSummary } from "@/lib/types";
import { cn, relativeTime } from "@/lib/utils";

export function NotificationBell() {
  const [isOpen, setIsOpen] = React.useState(false);
  const containerRef = React.useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // Fecha o dropdown ao clicar fora
  React.useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    }
    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [isOpen]);

  // Consulta sumário a cada 30 segundos
  const summaryQuery = useQuery<NotificationSummary>({
    queryKey: ["notifications", "summary"],
    queryFn: notificationsApi.getSummary,
    refetchInterval: 30000,
  });

  // Consulta lista das 5 mais recentes não lidas
  const listQuery = useQuery<NotificationItem[]>({
    queryKey: ["notifications", "recent"],
    queryFn: () => notificationsApi.list({ unread_only: true, limit: 5 }),
    enabled: isOpen,
  });

  const markReadMutation = useMutation({
    mutationFn: notificationsApi.markAsRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });

  const markAllMutation = useMutation({
    mutationFn: notificationsApi.markAllAsRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });

  const summary = summaryQuery.data ?? {
    unread_count: 0,
    critical_count: 0,
    warning_count: 0,
    info_count: 0,
  };

  const hasUnread = summary.unread_count > 0;
  const hasCritical = summary.critical_count > 0;

  function handleItemClick(item: NotificationItem) {
    markReadMutation.mutate(item.id);
    setIsOpen(false);
    if (item.link_url) {
      navigate(item.link_url);
    }
  }

  return (
    <div className="relative" ref={containerRef}>
      {/* Botão de Sino com Badge */}
      <button
        type="button"
        aria-label="Notificações"
        onClick={() => setIsOpen((prev) => !prev)}
        className={cn(
          "relative flex h-9 w-9 items-center justify-center rounded-lg border border-border/80 bg-background text-foreground transition-all hover:bg-muted focus:outline-none focus:ring-2 focus:ring-primary/40",
          isOpen && "bg-muted text-primary"
        )}
      >
        <Bell className="h-4 w-4" />
        {hasUnread && (
          <span
            className={cn(
              "absolute -top-1 -right-1 flex h-4 min-w-[16px] items-center justify-center rounded-full px-1 text-[10px] font-bold text-white shadow-sm",
              hasCritical ? "bg-rose-600 animate-pulse" : "bg-primary"
            )}
          >
            {summary.unread_count > 99 ? "99+" : summary.unread_count}
          </span>
        )}
      </button>

      {/* Popover de Notificações */}
      {isOpen && (
        <div className="absolute right-0 z-50 mt-2 w-80 sm:w-96 rounded-xl border border-border bg-card p-0 shadow-xl">
          {/* Header */}
          <div className="flex items-center justify-between border-b px-4 py-3 bg-muted/30">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-foreground uppercase tracking-wider">
                Notificações
              </span>
              {hasUnread && (
                <span className="rounded-full bg-primary/10 px-2 py-0.5 text-[11px] font-semibold text-primary">
                  {summary.unread_count} nova(s)
                </span>
              )}
            </div>
            {hasUnread && (
              <button
                type="button"
                onClick={() => markAllMutation.mutate()}
                disabled={markAllMutation.isPending}
                className="text-[11px] font-medium text-muted-foreground hover:text-foreground flex items-center gap-1 transition-colors"
              >
                <CheckCheck className="h-3.5 w-3.5" />
                Marcar lidas
              </button>
            )}
          </div>

          {/* Lista de Alertas */}
          <div className="max-h-80 overflow-y-auto divide-y divide-border/60">
            {listQuery.isLoading ? (
              <div className="flex items-center justify-center py-8 text-xs text-muted-foreground gap-2">
                <Loader2 className="h-4 w-4 animate-spin text-primary" />
                Carregando alertas…
              </div>
            ) : !listQuery.data || listQuery.data.length === 0 ? (
              <div className="py-8 text-center text-xs text-muted-foreground space-y-1">
                <Check className="h-6 w-6 text-emerald-500 mx-auto opacity-80" />
                <p className="font-semibold text-foreground">Nenhuma notificação pendente</p>
                <p className="text-[11px]">Seu laboratório está sem desvios ativos.</p>
              </div>
            ) : (
              listQuery.data.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => handleItemClick(item)}
                  className="w-full text-left p-3.5 hover:bg-muted/40 transition-colors flex items-start gap-3 group"
                >
                  <div className="mt-0.5 shrink-0">
                    {item.severity === "CRITICAL" ? (
                      <div className="rounded-full bg-rose-100 p-1.5 text-rose-600 dark:bg-rose-950/60 dark:text-rose-400">
                        <AlertOctagon className="h-3.5 w-3.5" />
                      </div>
                    ) : item.severity === "WARNING" ? (
                      <div className="rounded-full bg-amber-100 p-1.5 text-amber-600 dark:bg-amber-950/60 dark:text-amber-400">
                        <AlertTriangle className="h-3.5 w-3.5" />
                      </div>
                    ) : (
                      <div className="rounded-full bg-sky-100 p-1.5 text-sky-600 dark:bg-sky-950/60 dark:text-sky-400">
                        <Info className="h-3.5 w-3.5" />
                      </div>
                    )}
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-xs font-bold text-foreground truncate group-hover:text-primary transition-colors">
                        {item.title}
                      </p>
                      <span className="text-[10px] text-muted-foreground whitespace-nowrap">
                        {relativeTime(item.created_at)}
                      </span>
                    </div>
                    <p className="text-[11px] text-muted-foreground line-clamp-2 mt-0.5">
                      {item.message}
                    </p>
                    {item.link_url && (
                      <span className="inline-flex items-center gap-1 text-[10px] text-primary font-medium mt-1">
                        Acessar recurso <ExternalLink className="h-2.5 w-2.5" />
                      </span>
                    )}
                  </div>
                </button>
              ))
            )}
          </div>

          {/* Footer com link para Central Completa */}
          <div className="border-t p-2 bg-muted/20 text-center">
            <Link
              to="/notifications"
              onClick={() => setIsOpen(false)}
              className="text-xs font-semibold text-primary hover:underline block py-1"
            >
              Ver todas as notificações →
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
