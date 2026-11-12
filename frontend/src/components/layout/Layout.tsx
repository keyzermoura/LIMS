import * as React from "react";
import {
  BookOpen,
  Boxes,
  ClipboardCheck,
  ClipboardList,
  FlaskConical,
  Gauge,
  LayoutDashboard,
  LogOut,
  Menu,
  Scale,
  ScrollText,
  ShieldCheck,
  Timer,
  UserRound,
  X,
} from "lucide-react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/use-auth";
import { ROLE_LABELS, cn, initials } from "@/lib/utils";

interface NavItem {
  to: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  roles?: string[];
  end?: boolean;
}

const NAV_ITEMS: NavItem[] = [
  { to: "/solicitations", label: "Solicitações SEFI", icon: ClipboardList },
  { to: "/receipts", label: "Recebimento & Custódia", icon: Boxes },
  {
    to: "/coordination-reviews",
    label: "Revisão da Coordenação",
    icon: Scale,
    roles: ["ADMIN", "FISCAL"],
  },
  { to: "/", label: "Amostras Operacionais", icon: LayoutDashboard, end: true },
  { to: "/tests", label: "Ensaios e laudos", icon: FlaskConical },
  { to: "/equipment", label: "Controle de Equipamentos", icon: Gauge },
  { to: "/methods", label: "Catálogo de Métodos", icon: BookOpen },
  { to: "/capas", label: "CAPA", icon: ClipboardCheck },
  {
    to: "/audit",
    label: "Trilha de auditoria",
    icon: ScrollText,
    roles: ["ADMIN", "AUDITOR"],
  },
];

export function Layout() {
  const { user, logout, idleSecondsLeft } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = React.useState(false);

  React.useEffect(() => {
    setMobileOpen(false);
  }, [location.pathname]);

  if (!user) return null;

  const visibleItems = NAV_ITEMS.filter(
    (item) => !item.roles || item.roles.includes(user.role),
  );
  const current = [...NAV_ITEMS]
    .sort((a, b) => b.to.length - a.to.length)
    .find((item) =>
      item.to === "/" ? location.pathname === "/" : location.pathname.startsWith(item.to),
    );
  const title = current?.label ?? "Painel de entrada";

  const minutes = Math.floor(idleSecondsLeft / 60);
  const seconds = idleSecondsLeft % 60;
  const critical = idleSecondsLeft <= 120;

  async function handleLogout() {
    await logout("manual");
    navigate("/login", { replace: true });
  }

  return (
    <div className="min-h-screen bg-background">
      {mobileOpen ? (
        <button
          type="button"
          aria-label="Fechar menu"
          className="fixed inset-0 z-30 bg-slate-950/40 lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      ) : null}

      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-border bg-card transition-transform duration-200 lg:translate-x-0",
          mobileOpen ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="flex h-16 items-center gap-3 border-b border-border px-5">
          <span className="flex h-9 w-9 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <ShieldCheck className="h-5 w-5" />
          </span>
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold leading-tight">
              LIMS Fiscalização
            </p>
            <p className="text-[10px] font-medium uppercase tracking-[0.16em] text-muted-foreground">
              Pós-mercado · Anvisa
            </p>
          </div>
          <button
            type="button"
            className="ml-auto rounded p-1 text-muted-foreground hover:bg-muted lg:hidden"
            onClick={() => setMobileOpen(false)}
            aria-label="Fechar menu lateral"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4 scrollbar-thin">
          <p className="px-2 pb-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
            Operação
          </p>
          {visibleItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                cn(
                  "group flex items-center gap-3 rounded-md px-3 py-2 text-[13px] font-medium transition-colors",
                  isActive
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground",
                )
              }
            >
              {({ isActive }) => (
                <>
                  <item.icon
                    className={cn(
                      "h-4 w-4",
                      isActive ? "text-primary" : "text-muted-foreground/70",
                    )}
                  />
                  <span>{item.label}</span>
                  {item.to === "/audit" ? (
                    <span className="ml-auto rounded-full border border-border px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wider text-muted-foreground">
                      R/O
                    </span>
                  ) : null}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-border p-3">
          <div className="rounded-md border border-border bg-muted/40 p-3">
            <div className="flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-success" />
              <p className="text-[11px] font-semibold uppercase tracking-wider">
                Ambiente regulado
              </p>
            </div>
            <p className="mt-1.5 text-[11px] leading-relaxed text-muted-foreground">
              Assinatura eletrônica obrigatória em toda gravação definitiva.
              21 CFR Part 11 · RDC 665.
            </p>
          </div>
        </div>
      </aside>

      <div className="lg:pl-64">
        <header className="sticky top-0 z-20 flex h-16 items-center gap-3 border-b border-border bg-background/90 px-4 backdrop-blur lg:px-8">
          <button
            type="button"
            className="rounded-md p-2 text-muted-foreground hover:bg-muted lg:hidden"
            onClick={() => setMobileOpen(true)}
            aria-label="Abrir menu"
          >
            <Menu className="h-5 w-5" />
          </button>

          <div className="min-w-0">
            <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
              Fiscalização de dispositivos médicos
            </p>
            <h1 className="truncate text-[17px] font-semibold leading-tight">{title}</h1>
          </div>

          <div className="ml-auto flex items-center gap-2 sm:gap-3">
            <div
              className={cn(
                "hidden items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-medium sm:flex",
                critical
                  ? "border-rose-200 bg-rose-50 text-rose-800"
                  : "border-border bg-muted/50 text-muted-foreground",
              )}
              title="Tempo restante antes do encerramento automático por inatividade"
            >
              <Timer className="h-3.5 w-3.5" />
              <span className="tabular-nums">
                {minutes}:{String(seconds).padStart(2, "0")}
              </span>
            </div>

            <div className="hidden h-8 w-px bg-border sm:block" />

            <div className="flex items-center gap-2.5">
              <span className="flex h-9 w-9 items-center justify-center rounded-full bg-primary/10 text-[11px] font-semibold text-primary">
                {initials(user.full_name)}
              </span>
              <div className="hidden min-w-0 leading-tight sm:block">
                <p className="truncate text-[13px] font-medium">{user.full_name}</p>
                <p className="truncate text-[11px] text-muted-foreground">
                  {ROLE_LABELS[user.role] ?? user.role}
                  {user.registration_number ? ` · ${user.registration_number}` : ""}
                </p>
              </div>
            </div>

            <Button
              variant="ghost"
              size="icon"
              onClick={handleLogout}
              title="Encerrar sessão"
              aria-label="Encerrar sessão"
            >
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </header>

        <main className="mx-auto w-full max-w-[1500px] px-4 py-6 lg:px-8 lg:py-8">
          <Outlet />
        </main>

        <footer className="mx-auto flex w-full max-w-[1500px] flex-wrap items-center gap-x-4 gap-y-1 px-4 pb-8 text-[11px] text-muted-foreground lg:px-8">
          <span className="inline-flex items-center gap-1.5">
            <UserRound className="h-3 w-3" />
            Sessão auditada
          </span>
          <span className="text-border">|</span>
          <span>Dados regulados — retenção conforme RDC 665/2022</span>
          <span className="text-border">|</span>
          <span className="font-mono">v0.1.0</span>
        </footer>
      </div>
    </div>
  );
}
