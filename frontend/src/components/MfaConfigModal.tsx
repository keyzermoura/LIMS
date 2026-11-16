import * as React from "react";
import {
  AlertTriangle,
  Check,
  CheckCircle2,
  Copy,
  KeyRound,
  Loader2,
  Lock,
  QrCode,
  ShieldCheck,
  Smartphone,
} from "lucide-react";

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
import { useAuth } from "@/hooks/use-auth";
import { mfaApi } from "@/lib/api";
import type { MfaSetupResponse } from "@/lib/types";

interface MfaConfigModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function MfaConfigModal({ open, onOpenChange }: MfaConfigModalProps) {
  const { user } = useAuth();
  const [step, setStep] = React.useState<"initial" | "setup" | "recovery_display" | "disable">("initial");
  const [setupData, setSetupData] = React.useState<MfaSetupResponse | null>(null);
  const [password, setPassword] = React.useState("");
  const [code, setCode] = React.useState("");
  const [recoveryCodes, setRecoveryCodes] = React.useState<string[]>([]);
  const [copied, setCopied] = React.useState(false);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (open) {
      setStep("initial");
      setPassword("");
      setCode("");
      setError(null);
      setCopied(false);
      setSetupData(null);
    }
  }, [open, user?.mfa_enabled]);

  async function handleStartSetup() {
    setLoading(true);
    setError(null);
    try {
      const res = await mfaApi.setup();
      setSetupData(res);
      setStep("setup");
    } catch (err: any) {
      setError(err?.message ?? "Falha ao gerar pareamento MFA.");
    } finally {
      setLoading(false);
    }
  }

  async function handleConfirmEnable(e: React.FormEvent) {
    e.preventDefault();
    if (!setupData) return;
    setLoading(true);
    setError(null);
    try {
      const res = await mfaApi.enable({
        secret: setupData.secret,
        code: code.trim(),
        password,
      });
      setRecoveryCodes(res.recovery_codes);
      setStep("recovery_display");
      // Notifica o app que a sessão mudou para atualizar mfa_enabled no context
      if (user) {
        user.mfa_enabled = true;
      }
    } catch (err: any) {
      setError(err?.message ?? "Código TOTP inválido ou senha incorreta.");
    } finally {
      setLoading(false);
    }
  }

  async function handleConfirmDisable(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await mfaApi.disable({
        password,
        code: code.trim(),
      });
      if (user) {
        user.mfa_enabled = false;
      }
      onOpenChange(false);
    } catch (err: any) {
      setError(err?.message ?? "Senha incorreta ou código inválido.");
    } finally {
      setLoading(false);
    }
  }

  function handleCopyRecoveryCodes() {
    navigator.clipboard.writeText(recoveryCodes.join("\n"));
    setCopied(true);
    setTimeout(() => setCopied(false), 3000);
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <div className="flex items-center gap-2 text-primary">
            <span className="flex h-9 w-9 items-center justify-center rounded-full bg-primary/10">
              <ShieldCheck className="h-5 w-5" />
            </span>
            <span className="text-[11px] font-semibold uppercase tracking-[0.16em]">
              Segurança & Conformidade (21 CFR Part 11)
            </span>
          </div>
          <DialogTitle>Autenticação Multifator (MFA TOTP)</DialogTitle>
          <DialogDescription>
            Proteção reforçada para emissão de laudos oficiais e assinaturas periciais.
          </DialogDescription>
        </DialogHeader>

        {error && (
          <div className="rounded-md border border-rose-200 bg-rose-50 p-3 text-xs text-rose-800">
            {error}
          </div>
        )}

        {/* 1. ESTADO INICIAL */}
        {step === "initial" && (
          <div className="space-y-4 py-2">
            <div className="flex items-start gap-3 rounded-lg border p-3.5 bg-muted/40">
              <Smartphone className="h-5 w-5 text-primary shrink-0 mt-0.5" />
              <div className="text-sm">
                <p className="font-medium text-foreground">
                  Status: {user?.mfa_enabled ? "Ativo e Protegido" : "Não configurado"}
                </p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {user?.mfa_enabled
                    ? "Sua conta exige segundo fator temporal (TOTP) para autenticação e assinatura de registros técnicos."
                    : "Ative o MFA usando Google Authenticator, Microsoft Authenticator ou 1Password."}
                </p>
              </div>
            </div>

            {user?.mfa_enabled ? (
              <div className="space-y-2">
                <Button
                  variant="destructive"
                  className="w-full"
                  onClick={() => {
                    setError(null);
                    setPassword("");
                    setCode("");
                    setStep("disable");
                  }}
                >
                  Desativar Autenticação Multifator
                </Button>
              </div>
            ) : (
              <Button
                className="w-full"
                onClick={handleStartSetup}
                disabled={loading}
              >
                {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <QrCode className="h-4 w-4 mr-2" />}
                Configurar MFA Agora
              </Button>
            )}
          </div>
        )}

        {/* 2. ETAPA DE SETUP (QR CODE + CONFIRMAÇÃO) */}
        {step === "setup" && setupData && (
          <form onSubmit={handleConfirmEnable} className="space-y-4 py-2">
            <div className="flex flex-col items-center justify-center p-3 border rounded-lg bg-white">
              <img
                src={`data:image/png;base64,${setupData.qr_code_base64}`}
                alt="QR Code MFA TOTP"
                className="w-48 h-48 object-contain"
              />
              <p className="text-[11px] text-muted-foreground mt-2 text-center">
                Escaneie o código acima com seu aplicativo autenticador.
              </p>
            </div>

            <div className="rounded border bg-muted/30 p-2 text-center">
              <span className="text-[10px] uppercase font-semibold text-muted-foreground">Chave Secreta Manual</span>
              <p className="font-mono text-xs tracking-wider font-semibold select-all text-primary">
                {setupData.secret}
              </p>
            </div>

            <div className="space-y-3">
              <div className="grid gap-1.5">
                <Label htmlFor="mfa-code" className="text-xs">Código de 6 dígitos gerado no app</Label>
                <div className="relative">
                  <Smartphone className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    id="mfa-code"
                    type="text"
                    autoComplete="one-time-code"
                    className="pl-9 font-mono tracking-widest text-center text-sm font-semibold"
                    placeholder="000000"
                    maxLength={6}
                    value={code}
                    onChange={(e) => setCode(e.target.value)}
                    required
                  />
                </div>
              </div>

              <div className="grid gap-1.5">
                <Label htmlFor="mfa-pwd" className="text-xs">Sua senha atual</Label>
                <div className="relative">
                  <KeyRound className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    id="mfa-pwd"
                    type="password"
                    autoComplete="current-password"
                    className="pl-9 text-xs"
                    placeholder="Confirme sua senha para validar a ativação"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />
                </div>
              </div>
            </div>

            <DialogFooter className="gap-2 sm:gap-0">
              <Button
                type="button"
                variant="outline"
                onClick={() => setStep("initial")}
                disabled={loading}
              >
                Voltar
              </Button>
              <Button type="submit" disabled={loading || code.length < 6 || !password}>
                {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Check className="h-4 w-4 mr-2" />}
                Confirmar e Ativar
              </Button>
            </DialogFooter>
          </form>
        )}

        {/* 3. EXIBIÇÃO ÚNICA DOS RECOVERY CODES */}
        {step === "recovery_display" && (
          <div className="space-y-4 py-2">
            <div className="rounded-lg border border-amber-300 bg-amber-50 p-3 flex gap-2.5 items-start">
              <AlertTriangle className="h-5 w-5 text-amber-600 shrink-0 mt-0.5" />
              <div className="text-xs text-amber-900 leading-relaxed">
                <p className="font-semibold">Importante: Guarde seus códigos de recuperação!</p>
                <p className="mt-0.5">
                  Estes 8 códigos são de uso único. Caso perca o acesso ao seu smartphone, eles serão o único meio de recuperar seu acesso institucional.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2 border rounded-lg p-3 bg-muted/40 font-mono text-xs text-center font-bold">
              {recoveryCodes.map((rc, idx) => (
                <div key={idx} className="bg-background border rounded px-2 py-1.5 shadow-sm text-foreground">
                  {rc}
                </div>
              ))}
            </div>

            <Button
              type="button"
              variant="outline"
              className="w-full text-xs"
              onClick={handleCopyRecoveryCodes}
            >
              {copied ? (
                <>
                  <CheckCircle2 className="h-4 w-4 text-emerald-600 mr-2" />
                  Códigos Copiados para a Área de Transferência
                </>
              ) : (
                <>
                  <Copy className="h-4 w-4 mr-2" />
                  Copiar Todos os 8 Códigos
                </>
              )}
            </Button>

            <DialogFooter>
              <Button
                type="button"
                className="w-full"
                onClick={() => onOpenChange(false)}
              >
                Concluir e Salvar
              </Button>
            </DialogFooter>
          </div>
        )}

        {/* 4. ETAPA DE DESATIVAÇÃO */}
        {step === "disable" && (
          <form onSubmit={handleConfirmDisable} className="space-y-4 py-2">
            <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-xs text-rose-900 leading-relaxed">
              Ao desativar o segundo fator, suas assinaturas periciais voltarão a exigir apenas sua senha regular.
            </div>

            <div className="space-y-3">
              <div className="grid gap-1.5">
                <Label htmlFor="mfa-disable-code" className="text-xs">Código TOTP ou Código de Recuperação</Label>
                <div className="relative">
                  <Smartphone className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    id="mfa-disable-code"
                    type="text"
                    className="pl-9 font-mono text-xs"
                    placeholder="6 dígitos ou XXXX-XXXX"
                    value={code}
                    onChange={(e) => setCode(e.target.value)}
                    required
                  />
                </div>
              </div>

              <div className="grid gap-1.5">
                <Label htmlFor="mfa-disable-pwd" className="text-xs">Sua senha atual</Label>
                <div className="relative">
                  <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    id="mfa-disable-pwd"
                    type="password"
                    autoComplete="current-password"
                    className="pl-9 text-xs"
                    placeholder="Confirme sua senha"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />
                </div>
              </div>
            </div>

            <DialogFooter className="gap-2 sm:gap-0">
              <Button
                type="button"
                variant="outline"
                onClick={() => setStep("initial")}
                disabled={loading}
              >
                Voltar
              </Button>
              <Button
                type="submit"
                variant="destructive"
                disabled={loading || !code || !password}
              >
                {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                Confirmar Desativação
              </Button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}
