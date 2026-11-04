import * as React from "react";

import { useToast } from "@/components/ui/toast";
import {
  api,
  clearSession,
  getRefreshToken,
  hasStoredSession,
  persistSession,
} from "@/lib/api";
import type { AppMetadata, Me, TokenPair } from "@/lib/types";

type AuthStatus = "loading" | "authenticated" | "anonymous";

interface AuthContextValue {
  user: Me | null;
  status: AuthStatus;
  idleSecondsLeft: number;
  idleTimeoutMinutes: number;
  login: (username: string, password: string) => Promise<void>;
  logout: (reason?: "manual" | "idle") => Promise<void>;
  refreshProfile: () => Promise<void>;
}

const AuthContext = React.createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const { push } = useToast();
  const [user, setUser] = React.useState<Me | null>(null);
  const [status, setStatus] = React.useState<AuthStatus>("loading");
  const [idleTimeoutMinutes, setIdleTimeoutMinutes] = React.useState(15);
  const [idleSecondsLeft, setIdleSecondsLeft] = React.useState(15 * 60);

  const lastActivity = React.useRef(Date.now());
  const warned = React.useRef(false);

  // Parâmetros de conformidade (timeout de inatividade, TTL da assinatura).
  React.useEffect(() => {
    let active = true;
    api
      .get<AppMetadata>("/meta")
      .then((meta) => {
        if (!active) return;
        if (meta.session_idle_timeout_minutes > 0) {
          setIdleTimeoutMinutes(meta.session_idle_timeout_minutes);
          setIdleSecondsLeft(meta.session_idle_timeout_minutes * 60);
        }
      })
      .catch(() => {
        /* mantém padrão local */
      });
    return () => {
      active = false;
    };
  }, []);

  // Restauração de sessão (sessionStorage + refresh rotativo).
  React.useEffect(() => {
    let cancelled = false;
    async function bootstrap() {
      if (!hasStoredSession()) {
        if (!cancelled) setStatus("anonymous");
        return;
      }
      try {
        const me = await api.get<Me>("/auth/me");
        if (!cancelled) {
          setUser(me);
          setStatus("authenticated");
          lastActivity.current = Date.now();
        }
      } catch {
        clearSession();
        if (!cancelled) {
          setUser(null);
          setStatus("anonymous");
        }
      }
    }
    void bootstrap();
    return () => {
      cancelled = true;
    };
  }, []);

  // Rotação de token atualiza o usuário exibido.
  React.useEffect(() => {
    function onSession(event: Event) {
      const detail = (event as CustomEvent<Me>).detail;
      if (detail) {
        setUser(detail);
        setStatus("authenticated");
      }
    }
    function onForcedLogout() {
      setUser(null);
      setStatus("anonymous");
    }
    window.addEventListener("lims:session", onSession);
    window.addEventListener("lims:logout", onForcedLogout);
    return () => {
      window.removeEventListener("lims:session", onSession);
      window.removeEventListener("lims:logout", onForcedLogout);
    };
  }, []);

  const logout = React.useCallback(
    async (reason: "manual" | "idle" = "manual") => {
      const refreshToken = getRefreshToken();
      if (refreshToken) {
        try {
          await api.post<void>("/auth/logout", { refresh_token: refreshToken });
        } catch {
          /* logout é best-effort; a sessão local é sempre encerrada */
        }
      }
      clearSession();
      setUser(null);
      setStatus("anonymous");
      setIdleSecondsLeft(idleTimeoutMinutes * 60);
      if (reason === "idle") {
        push({
          variant: "warning",
          title: "Sessão encerrada por inatividade",
          description:
            "Por conformidade (21 CFR Part 11), a sessão expira após " +
            `${idleTimeoutMinutes} minutos sem atividade.`,
        });
      }
    },
    [idleTimeoutMinutes, push],
  );

  // Timer de inatividade — conta apenas com a aba ativa e autenticada.
  React.useEffect(() => {
    if (status !== "authenticated") return;

    const timeoutMs = idleTimeoutMinutes * 60 * 1000;
    let loggingOut = false;
    const markActivity = () => {
      lastActivity.current = Date.now();
      warned.current = false;
    };
    const events: Array<keyof WindowEventMap> = [
      "mousemove",
      "keydown",
      "click",
      "scroll",
      "touchstart",
    ];
    events.forEach((name) =>
      window.addEventListener(name, markActivity, { passive: true }),
    );

    const interval = window.setInterval(() => {
      const remaining = Math.max(
        0,
        Math.round((lastActivity.current + timeoutMs - Date.now()) / 1000),
      );
      setIdleSecondsLeft(remaining);

      if (remaining <= 120 && remaining > 0 && !warned.current) {
        warned.current = true;
        push({
          variant: "warning",
          title: "Sessão prestes a expirar",
          description: "Interaja com o sistema para manter a sessão ativa.",
        });
      }
      if (remaining <= 0 && !loggingOut) {
        loggingOut = true;
        void logout("idle");
      }
    }, 1000);

    return () => {
      events.forEach((name) => window.removeEventListener(name, markActivity));
      window.clearInterval(interval);
    };
  }, [status, idleTimeoutMinutes, logout, push]);

  const login = React.useCallback(
    async (username: string, password: string) => {
      const pair = await api.login<TokenPair>(username.trim(), password);
      persistSession(pair.access_token, pair.refresh_token);
      setUser(pair.user);
      setStatus("authenticated");
      lastActivity.current = Date.now();
      warned.current = false;
      setIdleSecondsLeft(idleTimeoutMinutes * 60);
    },
    [idleTimeoutMinutes],
  );

  const refreshProfile = React.useCallback(async () => {
    const me = await api.get<Me>("/auth/me");
    setUser(me);
  }, []);

  const value = React.useMemo<AuthContextValue>(
    () => ({
      user,
      status,
      idleSecondsLeft,
      idleTimeoutMinutes,
      login,
      logout,
      refreshProfile,
    }),
    [user, status, idleSecondsLeft, idleTimeoutMinutes, login, logout, refreshProfile],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = React.useContext(AuthContext);
  if (!context) throw new Error("useAuth deve ser usado dentro de AuthProvider.");
  return context;
}
