import * as React from "react";
import {
  ArrowRight,
  FileCheck2,
  Fingerprint,
  FlaskConical,
  Loader2,
  LockKeyhole,
  ScrollText,
  ShieldCheck,
} from "lucide-react";
import { useLocation, useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/hooks/use-auth";
import { ApiError } from "@/lib/api";

const DEMO_ACCOUNTS = [
  { username: "fiscal", password: "Fiscal@Lims2026", role: "Fiscal sanitário" },
  { username: "tecnico", password: "Tecnico@Lims2026", role: "Técnico de laboratório" },
  { username: "auditor", password: "Auditor@Lims2026", role: "Auditor da qualidade" },
];

const COMPLIANCE_POINTS = [
  {
    icon: Fingerprint,
    title: "Assinatura eletrônica em duas etapas",
    description:
      "Reautenticação por senha para cada gravação definitiva, com manifesto imutável por registro.",
  },
  {
    icon: ScrollText,
    title: "Trilha de auditoria inviolável",
    description:
      "Eventos encadeados por SHA-256 + HMAC e protegidos por triggers append-only no PostgreSQL.",
  },
  {
    icon: FileCheck2,
    title: "Rastreabilidade ponta a ponta",
    description:
      "Accession, QR Code assinado, cadeia de custódia, laudos versionados e CAPA automática.",
  },
];

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: string } | null)?.from ?? "/";

  const [username, setUsername] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [error, setError] = React.useState<string | null>(null);
  const [submitting, setSubmitting] = React.useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(username, password);
      navigate(from, { replace: true });
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Falha ao autenticar. Verifique as credenciais.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="grid min-h-screen lg:grid-cols-[1.05fr_1fr]">
      <section className="relative hidden overflow-hidden bg-[#082a3a] px-12 py-14 text-white lg:flex lg:flex-col lg:justify-between">
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 opacity-[0.16]"
          style={{
            backgroundImage:
              "linear-gradient(rgba(255,255,255,.35) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.35) 1px, transparent 1px)",
            backgroundSize: "48px 48px",
            maskImage: "radial-gradient(ellipse at 30% 20%, black, transparent 75%)",
          }}
        />
        <div className="relative">
          <div className="flex items-center gap-3">
            <span className="flex h-11 w-11 items-center justify-center rounded-lg border border-white/20 bg-white/10">
              <ShieldCheck className="h-6 w-6" />
            </span>
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.18em] text-white/70">
                Anvisa · Pós-mercado
              </p>
              <h1 className="text-xl font-semibold">LIMS Fiscalização</h1>
            </div>
          </div>

          <div className="mt-14 max-w-lg">
            <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-teal-300">
              Ambiente regulado
            </p>
            <h2 className="mt-3 text-3xl font-semibold leading-tight">
              Rastreabilidade total para dispositivos médicos recolhidos do mercado.
            </h2>
            <p className="mt-4 text-sm leading-relaxed text-white/70">
              Da apreensão ao laudo assinado: cada movimento guarda quem, quando,
              onde e por quê — com integridade verificável.
            </p>
          </div>

          <ul className="mt-12 space-y-5">
            {COMPLIANCE_POINTS.map((point) => (
              <li key={point.title} className="flex gap-4">
                <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-white/15 bg-white/5">
                  <point.icon className="h-[18px] w-[18px] text-teal-300" />
                </span>
                <div>
                  <p className="text-sm font-medium">{point.title}</p>
                  <p className="mt-1 max-w-md text-[13px] leading-relaxed text-white/60">
                    {point.description}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        </div>

        <div className="relative flex items-center gap-6 border-t border-white/10 pt-6 text-[11px] uppercase tracking-wider text-white/50">
          <span>21 CFR Part 11</span>
          <span className="h-1 w-1 rounded-full bg-white/30" />
          <span>RDC 665/2022</span>
          <span className="h-1 w-1 rounded-full bg-white/30" />
          <span>ALCOA+</span>
        </div>
      </section>

      <section className="flex items-center justify-center px-6 py-12 sm:px-10">
        <div className="w-full max-w-md">
          <div className="mb-8 flex items-center gap-3 lg:hidden">
            <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <ShieldCheck className="h-5 w-5" />
            </span>
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                Anvisa · Pós-mercado
              </p>
              <p className="text-lg font-semibold">LIMS Fiscalização</p>
            </div>
          </div>

          <div className="mb-8">
            <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-primary">
              Acesso restrito
            </p>
            <h2 className="mt-2 text-2xl font-semibold tracking-tight">
              Entrar no sistema
            </h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Credenciais individuais. Todas as tentativas de acesso são auditadas.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-1.5">
              <Label htmlFor="username">Usuário</Label>
              <Input
                id="username"
                autoComplete="username"
                autoFocus
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                placeholder="seu.usuario"
                required
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="password">Senha</Label>
              <div className="relative">
                <LockKeyhole className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  id="password"
                  type="password"
                  autoComplete="current-password"
                  className="pl-9"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="••••••••••••"
                  required
                />
              </div>
            </div>

            {error ? (
              <div
                role="alert"
                className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-[13px] text-rose-900"
              >
                {error}
              </div>
            ) : null}

            <Button type="submit" size="lg" className="w-full" disabled={submitting}>
              {submitting ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Fingerprint className="h-4 w-4" />
              )}
              Autenticar com segurança
              {!submitting ? <ArrowRight className="ml-auto h-4 w-4" /> : null}
            </Button>
          </form>

          <div className="mt-8 rounded-lg border border-border bg-muted/40 p-4">
            <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
              <FlaskConical className="h-3.5 w-3.5" />
              Contas de demonstração
            </div>
            <div className="mt-3 space-y-2">
              {DEMO_ACCOUNTS.map((account) => (
                <button
                  key={account.username}
                  type="button"
                  onClick={() => {
                    setUsername(account.username);
                    setPassword(account.password);
                    setError(null);
                  }}
                  className="flex w-full items-center justify-between rounded-md border border-transparent px-2 py-1.5 text-left transition-colors hover:border-border hover:bg-card"
                >
                  <span className="text-[13px]">
                    <span className="font-medium">{account.username}</span>
                    <span className="text-muted-foreground"> · {account.role}</span>
                  </span>
                  <span className="font-mono text-[11px] text-muted-foreground">
                    {account.password}
                  </span>
                </button>
              ))}
            </div>
            <p className="mt-3 text-[11px] leading-relaxed text-muted-foreground">
              Uso exclusivo em desenvolvimento. Nunca mantenha contas de
              demonstração em produção.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
