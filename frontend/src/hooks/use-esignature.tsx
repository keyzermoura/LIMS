import * as React from "react";
import { KeyRound, Loader2, ShieldCheck } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
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
import { Textarea } from "@/components/ui/input";
import { useAuth } from "@/hooks/use-auth";
import { api, ApiError } from "@/lib/api";
import type {
  ESignatureGrant,
  SignatureAction,
  SignatureMeaning,
} from "@/lib/types";
import { MEANING_LABELS, cn } from "@/lib/utils";

export interface SignatureIntent {
  entityType: string;
  entityId: string;
  action: SignatureAction;
  meaning: SignatureMeaning;
  suggestedReason?: string;
  title?: string;
  description?: string;
  recordLabel?: string;
}

interface ESignatureContextValue {
  requestSignature: (intent: SignatureIntent) => Promise<string | null>;
}

const ESignatureContext = React.createContext<ESignatureContextValue | null>(null);

const ENTITY_LABELS: Record<string, string> = {
  DeviceSample: "Amostra",
  LabTest: "Ensaio",
  CapaAction: "CAPA",
  User: "Usuário",
  ElectronicSignature: "Assinatura",
};

const ACTION_LABELS: Record<string, string> = {
  CREATE: "Criação de registro",
  UPDATE: "Alteração de registro",
  TRANSFER: "Transferência de custódia",
  CLOSE: "Encerramento",
};

const MEANING_OPTIONS: SignatureMeaning[] = [
  "AUTORIA",
  "REVISAO",
  "RESPONSABILIDADE_TECNICA",
  "APROVACAO",
  "TRANSFERENCIA_DE_CUSTODIA",
  "VERIFICACAO",
];

export function ESignatureProvider({ children }: { children: React.ReactNode }) {
  const [intent, setIntent] = React.useState<SignatureIntent | null>(null);
  const resolver = React.useRef<((token: string | null) => void) | null>(null);

  const requestSignature = React.useCallback((next: SignatureIntent) => {
    return new Promise<string | null>((resolve) => {
      // Se uma assinatura anterior ficou pendente, ela é cancelada.
      resolver.current?.(null);
      resolver.current = resolve;
      setIntent(next);
    });
  }, []);

  const finish = React.useCallback((token: string | null) => {
    resolver.current?.(token);
    resolver.current = null;
    setIntent(null);
  }, []);

  return (
    <ESignatureContext.Provider value={{ requestSignature }}>
      {children}
      <ESignatureDialog
        intent={intent}
        onCancel={() => finish(null)}
        onSigned={(token) => finish(token)}
      />
    </ESignatureContext.Provider>
  );
}

export function useESignature(): ESignatureContextValue {
  const context = React.useContext(ESignatureContext);
  if (!context) {
    throw new Error("useESignature deve ser usado dentro de ESignatureProvider.");
  }
  return context;
}

function ESignatureDialog({
  intent,
  onCancel,
  onSigned,
}: {
  intent: SignatureIntent | null;
  onCancel: () => void;
  onSigned: (token: string) => void;
}) {
  const { user } = useAuth();
  const [password, setPassword] = React.useState("");
  const [reason, setReason] = React.useState("");
  const [meaning, setMeaning] = React.useState<SignatureMeaning>(
    "RESPONSABILIDADE_TECNICA",
  );
  const [error, setError] = React.useState<string | null>(null);
  const [submitting, setSubmitting] = React.useState(false);

  React.useEffect(() => {
    if (!intent) return;
    setPassword("");
    setReason(intent.suggestedReason ?? "");
    setMeaning(intent.meaning);
    setError(null);
    setSubmitting(false);
  }, [intent]);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!intent) return;
    setError(null);

    if (reason.trim().length < 10) {
      setError("Descreva o motivo da assinatura com ao menos 10 caracteres.");
      return;
    }
    if (!password) {
      setError("Informe sua senha para reautenticar.");
      return;
    }

    setSubmitting(true);
    try {
      const grant = await api.post<ESignatureGrant>("/auth/sign", {
        password,
        meaning,
        reason: reason.trim(),
        entity_type: intent.entityType,
        entity_id: intent.entityId,
        action: intent.action,
      });
      onSigned(grant.token);
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.message
          : "Não foi possível emitir a assinatura eletrônica.";
      setError(message);
      setPassword("");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog
      open={Boolean(intent)}
      onOpenChange={(open) => {
        if (!open) onCancel();
      }}
    >
      <DialogContent className="max-w-xl">
        <DialogHeader>
          <div className="mb-1 flex items-center gap-2 text-primary">
            <span className="flex h-9 w-9 items-center justify-center rounded-full bg-primary/10">
              <ShieldCheck className="h-5 w-5" />
            </span>
            <span className="text-[11px] font-semibold uppercase tracking-[0.16em]">
              Assinatura eletrônica
            </span>
          </div>
          <DialogTitle>{intent?.title ?? "Confirmar assinatura"}</DialogTitle>
          <DialogDescription>
            {intent?.description ??
              "Esta ação grava um registro definitivo e será registrada na trilha de auditoria."}
          </DialogDescription>
        </DialogHeader>

        {intent ? (
          <div className="grid gap-3 rounded-md border border-border bg-muted/40 p-3 text-sm">
            <div className="grid grid-cols-[110px_1fr] gap-1.5">
              <span className="text-muted-foreground">Registro</span>
              <span className="font-medium">
                {intent.recordLabel ?? ENTITY_LABELS[intent.entityType] ?? intent.entityType}
              </span>
              <span className="text-muted-foreground">Identificador</span>
              <span className="truncate font-mono text-xs">{intent.entityId}</span>
              <span className="text-muted-foreground">Operação</span>
              <span>{ACTION_LABELS[intent.action] ?? intent.action}</span>
              <span className="text-muted-foreground">Signatário</span>
              <span>
                {user?.full_name}{" "}
                <span className="text-muted-foreground">
                  ({user?.registration_number ?? user?.role})
                </span>
              </span>
            </div>
          </div>
        ) : null}

        <form onSubmit={handleSubmit} className="grid gap-4">
          <div className="grid gap-1.5">
            <Label htmlFor="esign-meaning">Significado da assinatura</Label>
            <Select
              value={meaning}
              onValueChange={(value) => setMeaning(value as SignatureMeaning)}
            >
              <SelectTrigger id="esign-meaning">
                <SelectValue placeholder="Selecione" />
              </SelectTrigger>
              <SelectContent>
                {MEANING_OPTIONS.map((option) => (
                  <SelectItem key={option} value={option}>
                    {MEANING_LABELS[option]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="grid gap-1.5">
            <Label htmlFor="esign-reason">Motivo da assinatura</Label>
            <Textarea
              id="esign-reason"
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              placeholder="Ex.: Lançamento do resultado do ensaio conforme protocolo XYZ."
              maxLength={1000}
              rows={3}
              required
            />
            <p className="text-[11px] text-muted-foreground">
              O motivo é gravado no manifesto da assinatura e não pode ser alterado.
            </p>
          </div>

          <div className="grid gap-1.5">
            <Label htmlFor="esign-password">Senha do usuário</Label>
            <div className="relative">
              <KeyRound className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                id="esign-password"
                type="password"
                autoComplete="current-password"
                autoFocus
                className="pl-9"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="Reautentique para assinar"
                required
              />
            </div>
          </div>

          {error ? (
            <div
              role="alert"
              className={cn(
                "rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-[13px] text-rose-900",
              )}
            >
              {error}
            </div>
          ) : null}

          <div className="rounded-md border border-dashed border-border px-3 py-2 text-[11px] leading-relaxed text-muted-foreground">
            A senha é verificada novamente e o token de assinatura é de uso único,
            válido por poucos minutos. A assinatura fica vinculada ao registro, com
            data/hora UTC, IP, significado e hash do conteúdo (21 CFR Part 11 §11.70).
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={onCancel} disabled={submitting}>
              Cancelar
            </Button>
            <Button type="submit" disabled={submitting}>
              {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <ShieldCheck />}
              Assinar e concluir
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
