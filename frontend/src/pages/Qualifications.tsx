import * as React from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertCircle,
  Award,
  BookOpen,
  Calendar,
  CheckCircle2,
  Clock,
  GraduationCap,
  Loader2,
  Plus,
  ShieldAlert,
  ShieldCheck,
  UserCheck,
  XCircle,
} from "lucide-react";

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
import { useToast } from "@/components/ui/toast";
import { useAuth } from "@/hooks/use-auth";
import { qualificationsApi, methodsApi, api, ApiError } from "@/lib/api";
import type {
  AnalystQualification,
  QualificationStatus,
  TestMethod,
  UserBrief,
} from "@/lib/types";
import { formatDateTime } from "@/lib/utils";

export function QualificationsPage() {
  const { user } = useAuth();
  const { push } = useToast();
  const queryClient = useQueryClient();

  const [statusFilter, setStatusFilter] = React.useState<string>("TODOS");
  const [grantModalOpen, setGrantModalOpen] = React.useState(false);
  const [revokeModalOpen, setRevokeModalOpen] = React.useState(false);
  const [trainingsModalOpen, setTrainingsModalOpen] = React.useState(false);
  const [selectedQual, setSelectedQual] = React.useState<AnalystQualification | null>(null);

  // Form de concessão
  const [targetUserId, setTargetUserId] = React.useState("");
  const [targetMethodId, setTargetMethodId] = React.useState("");
  const [grantStatus, setGrantStatus] = React.useState<QualificationStatus>("QUALIFICADO");
  const [expiresAt, setExpiresAt] = React.useState("");
  const [scope, setScope] = React.useState("");
  const [notes, setNotes] = React.useState("");
  const [trainingTitle, setTrainingTitle] = React.useState("");
  const [trainingHours, setTrainingHours] = React.useState("8.00");
  const [certificateCode, setCertificateCode] = React.useState("");
  const [signaturePassword, setSignaturePassword] = React.useState("");
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  // Form de suspensão
  const [revokeReason, setRevokeReason] = React.useState("");
  const [revokePassword, setRevokePassword] = React.useState("");

  // Queries
  const { data: qualifications = [], isLoading: isLoadingQuals } = useQuery({
    queryKey: ["qualifications", statusFilter],
    queryFn: () =>
      qualificationsApi.list(
        statusFilter === "TODOS" ? undefined : { status: statusFilter }
      ),
  });

  const { data: methods = [] } = useQuery<TestMethod[]>({
    queryKey: ["methods"],
    queryFn: () => methodsApi.list(undefined, true),
  });

  const { data: users = [] } = useQuery<UserBrief[]>({
    queryKey: ["users"],
    queryFn: () => api.get<UserBrief[]>("/users"),
  });

  const canManage = user?.role === "ADMIN" || user?.role === "FISCAL";

  // Estatísticas
  const totalActive = qualifications.filter((q) => q.is_active).length;
  const totalSuspended = qualifications.filter(
    (q) => q.status === "SUSPENSO" || q.status === "EXPIRADO"
  ).length;
  const uniqueAnalysts = new Set(qualifications.map((q) => q.user_id)).size;

  async function handleGrant(e: React.FormEvent) {
    e.preventDefault();
    if (!targetUserId || !targetMethodId) {
      push({
        title: "Campos obrigatórios",
        description: "Selecione o analista e o método de ensaio.",
        variant: "destructive",
      });
      return;
    }

    setIsSubmitting(true);
    try {
      let signatureToken: string | undefined;
      if (signaturePassword) {
        const sig = await api.post<{ token: string }>("/auth/sign", {
          password: signaturePassword,
          entity_type: "User",
          entity_id: targetUserId,
          action: "UPDATE",
          meaning: "APROVACAO",
          reason: "Habilitação técnica de analista em conformidade com a ISO/IEC 17025 §6.2.",
        });
        signatureToken = sig.token;
      }

      await qualificationsApi.grant(
        {
          user_id: targetUserId,
          method_id: targetMethodId,
          status: grantStatus,
          expires_at: expiresAt ? new Date(expiresAt).toISOString() : null,
          scope: scope || null,
          notes: notes || null,
          trainings: trainingTitle
            ? [
                {
                  title: trainingTitle,
                  hours: Number(trainingHours) || 8.0,
                  certificate_code: certificateCode || null,
                },
              ]
            : [],
        },
        signatureToken
      );

      push({
        title: "Habilitação concedida com sucesso",
        description: "Competência do analista registrada e auditada.",
      });

      setGrantModalOpen(false);
      setTargetUserId("");
      setTargetMethodId("");
      setScope("");
      setNotes("");
      setTrainingTitle("");
      setSignaturePassword("");
      queryClient.invalidateQueries({ queryKey: ["qualifications"] });
    } catch (err) {
      push({
        title: "Erro ao conceder habilitação",
        description: err instanceof ApiError ? err.message : "Falha na comunicação.",
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleRevoke(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedQual) return;
    if (revokeReason.trim().length < 10) {
      push({
        title: "Justificativa obrigatória",
        description: "Informe o motivo da suspensão com no mínimo 10 caracteres.",
        variant: "destructive",
      });
      return;
    }

    setIsSubmitting(true);
    try {
      let signatureToken: string | undefined;
      if (revokePassword) {
        const sig = await api.post<{ token: string }>("/auth/sign", {
          password: revokePassword,
          entity_type: "User",
          entity_id: selectedQual.user_id,
          action: "UPDATE",
          meaning: "APROVACAO",
          reason: "Suspensão formal de competência analítica.",
        });
        signatureToken = sig.token;
      }

      await qualificationsApi.revoke(
        selectedQual.id,
        {
          status: "SUSPENSO",
          reason: revokeReason,
        },
        signatureToken
      );

      push({
        title: "Habilitação suspensa",
        description: "O analista está impedido de executar este método até reciclagem.",
      });

      setRevokeModalOpen(false);
      setSelectedQual(null);
      setRevokeReason("");
      setRevokePassword("");
      queryClient.invalidateQueries({ queryKey: ["qualifications"] });
    } catch (err) {
      push({
        title: "Erro ao suspender",
        description: err instanceof ApiError ? err.message : "Falha na comunicação.",
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  }

  function getStatusBadge(qual: AnalystQualification) {
    if (!qual.is_active || qual.status === "SUSPENSO") {
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-rose-100 px-2.5 py-0.5 text-xs font-semibold text-rose-800 dark:bg-rose-950 dark:text-rose-300">
          <XCircle className="h-3 w-3" />
          {qual.status}
        </span>
      );
    }
    if (qual.status === "EM_SUPERVISAO") {
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-semibold text-amber-800 dark:bg-amber-950 dark:text-amber-300">
          <Clock className="h-3 w-3" />
          EM SUPERVISÃO
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-semibold text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
        <CheckCircle2 className="h-3 w-3" />
        QUALIFICADO
      </span>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
            Matriz de Competências & Qualificação de Analistas
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Habilitação formal de pessoal, registros de capacitação e bloqueio regulatório (ISO/IEC 17025 §6.2).
          </p>
        </div>

        {canManage && (
          <Button
            onClick={() => setGrantModalOpen(true)}
            className="flex items-center gap-2 bg-sky-600 hover:bg-sky-700"
          >
            <Plus className="h-4 w-4" />
            Habilitar Analista
          </Button>
        )}
      </div>

      {/* Cards de Métricas */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card className="border-slate-200 dark:border-slate-800">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600 dark:text-slate-400">
              Habilitações Ativas
            </CardTitle>
            <ShieldCheck className="h-4 w-4 text-emerald-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-slate-900 dark:text-slate-100">
              {totalActive}
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Capacitações com autorização vigente de bancada
            </p>
          </CardContent>
        </Card>

        <Card className="border-slate-200 dark:border-slate-800">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600 dark:text-slate-400">
              Analistas Habilitados
            </CardTitle>
            <UserCheck className="h-4 w-4 text-sky-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-slate-900 dark:text-slate-100">
              {uniqueAnalysts}
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Profissionais aptos para ensaios metrológicos
            </p>
          </CardContent>
        </Card>

        <Card className="border-slate-200 dark:border-slate-800">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600 dark:text-slate-400">
              Suspensas / Reciclagem
            </CardTitle>
            <ShieldAlert className="h-4 w-4 text-rose-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-slate-900 dark:text-slate-100">
              {totalSuspended}
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Bloqueados preventivamente por vencimento ou desvio
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Tabela de Qualificações */}
      <Card className="border-slate-200 dark:border-slate-800">
        <CardHeader className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between pb-4">
          <div>
            <CardTitle className="text-base font-semibold">
              Quadro de Autorizações por Método Analítico
            </CardTitle>
            <CardDescription>
              Operadores vinculados a métodos específicos de ensaio conforme portaria técnica.
            </CardDescription>
          </div>

          <div className="flex items-center gap-2">
            <Label htmlFor="statusFilter" className="text-xs text-slate-500">
              Status:
            </Label>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-40 h-8 text-xs">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="TODOS">Todos os Status</SelectItem>
                <SelectItem value="QUALIFICADO">Qualificado</SelectItem>
                <SelectItem value="EM_SUPERVISAO">Em Supervisão</SelectItem>
                <SelectItem value="SUSPENSO">Suspenso</SelectItem>
                <SelectItem value="EXPIRADO">Expirado</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardHeader>

        <CardContent>
          {isLoadingQuals ? (
            <div className="flex h-32 items-center justify-center">
              <Loader2 className="h-6 w-6 animate-spin text-sky-600" />
            </div>
          ) : qualifications.length === 0 ? (
            <div className="flex h-32 flex-col items-center justify-center text-center text-slate-500">
              <GraduationCap className="h-8 w-8 text-slate-400 mb-2" />
              <p className="text-sm font-medium">Nenhuma qualificação cadastrada.</p>
              <p className="text-xs">
                Utilize o botão "Habilitar Analista" para cadastrar competências técnicas.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase">
                  <tr>
                    <th className="p-3">Analista / Operador</th>
                    <th className="p-3">Método / Norma Técnica</th>
                    <th className="p-3">Status</th>
                    <th className="p-3">Habilitação & Validade</th>
                    <th className="p-3">Treinamentos</th>
                    <th className="p-3 text-right">Ações</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {qualifications.map((qual) => (
                    <tr key={qual.id} className="hover:bg-slate-50/80 dark:hover:bg-slate-900/50">
                      <td className="p-3">
                        <p className="font-medium text-slate-900 dark:text-slate-100">
                          {qual.user_name || "Analista"}
                        </p>
                        <p className="text-xs text-slate-500">
                          ID: {qual.user_id.slice(0, 8)}...
                        </p>
                      </td>
                      <td className="p-3">
                        <span className="font-mono text-xs font-bold text-sky-700 bg-sky-50 dark:bg-sky-950/60 dark:text-sky-300 px-2 py-0.5 rounded">
                          {qual.method_code}
                        </span>
                        <p className="text-xs text-slate-700 dark:text-slate-300 mt-0.5">
                          {qual.method_name}
                        </p>
                      </td>
                      <td className="p-3">{getStatusBadge(qual)}</td>
                      <td className="p-3 text-xs text-slate-600 dark:text-slate-400">
                        <p>Concedido: {formatDateTime(qual.granted_at)}</p>
                        <p className="text-slate-500">
                          Expira: {qual.expires_at ? formatDateTime(qual.expires_at) : "Sem expiração"}
                        </p>
                      </td>
                      <td className="p-3">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setSelectedQual(qual);
                            setTrainingsModalOpen(true);
                          }}
                          className="h-7 text-xs flex items-center gap-1.5 text-slate-600 hover:text-sky-700"
                        >
                          <BookOpen className="h-3.5 w-3.5" />
                          {qual.trainings?.length || 0} Registro(s)
                        </Button>
                      </td>
                      <td className="p-3 text-right">
                        {canManage && qual.is_active && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              setSelectedQual(qual);
                              setRevokeModalOpen(true);
                            }}
                            className="h-7 text-xs text-rose-600 border-rose-200 hover:bg-rose-50 dark:hover:bg-rose-950/50"
                          >
                            Suspender
                          </Button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Modal: Conceder Habilitação Técnica */}
      <Dialog open={grantModalOpen} onOpenChange={setGrantModalOpen}>
        <DialogContent className="max-w-lg">
          <form onSubmit={handleGrant} className="space-y-4">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2 text-sky-700 dark:text-sky-300">
                <Award className="h-5 w-5" />
                Habilitar Analista (ISO/IEC 17025 §6.2)
              </DialogTitle>
              <DialogDescription>
                Concessão formal de competência para execução e cálculo de incerteza em método padronizado.
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-3">
              <div>
                <Label>Analista / Operador de Laboratório *</Label>
                <Select value={targetUserId} onValueChange={setTargetUserId}>
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Selecione o analista" />
                  </SelectTrigger>
                  <SelectContent>
                    {users.map((u: UserBrief) => (
                      <SelectItem key={u.id} value={u.id}>
                        {u.full_name} ({u.username} - {u.role})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label>Método Analítico Padronizado *</Label>
                <Select value={targetMethodId} onValueChange={setTargetMethodId}>
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Selecione o método" />
                  </SelectTrigger>
                  <SelectContent>
                    {methods.map((m: TestMethod) => (
                      <SelectItem key={m.id} value={m.id}>
                        {m.code} — {m.name} ({m.standard})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label>Status Inicial</Label>
                  <Select
                    value={grantStatus}
                    onValueChange={(val) => setGrantStatus(val as QualificationStatus)}
                  >
                    <SelectTrigger className="w-full">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="QUALIFICADO">Qualificado Pleno</SelectItem>
                      <SelectItem value="EM_SUPERVISAO">Em Supervisão</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Data de Validade (Opcional)</Label>
                  <Input
                    type="date"
                    value={expiresAt}
                    onChange={(e) => setExpiresAt(e.target.value)}
                  />
                </div>
              </div>

              <div>
                <Label>Escopo Específico de Autorização</Label>
                <Input
                  value={scope}
                  onChange={(e) => setScope(e.target.value)}
                  placeholder="Ex: Execução de rotina e calibração de bancada"
                />
              </div>

              {/* Registro de Treinamento Comprobatório */}
              <div className="rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/50 p-3 space-y-2">
                <p className="text-xs font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                  <GraduationCap className="h-4 w-4 text-sky-600" />
                  Treinamento Comprobatório Inicial
                </p>
                <div className="grid grid-cols-3 gap-2">
                  <div className="col-span-2">
                    <Input
                      value={trainingTitle}
                      onChange={(e) => setTrainingTitle(e.target.value)}
                      placeholder="Título do Curso ou Treinamento de Bancada"
                      className="text-xs"
                    />
                  </div>
                  <div>
                    <Input
                      type="number"
                      step="0.5"
                      value={trainingHours}
                      onChange={(e) => setTrainingHours(e.target.value)}
                      placeholder="Horas"
                      className="text-xs"
                    />
                  </div>
                </div>
                <Input
                  value={certificateCode}
                  onChange={(e) => setCertificateCode(e.target.value)}
                  placeholder="Código do Certificado ou Evidência (ALCOA+)"
                  className="text-xs"
                />
              </div>

              <div className="border-t pt-2">
                <Label className="flex items-center gap-1.5 text-slate-700 dark:text-slate-300">
                  <ShieldCheck className="h-4 w-4 text-emerald-600" />
                  Assinatura Eletrônica (21 CFR Part 11)
                </Label>
                <Input
                  type="password"
                  value={signaturePassword}
                  onChange={(e) => setSignaturePassword(e.target.value)}
                  placeholder="Digite sua senha de login para selar a habilitação"
                  className="mt-1"
                />
              </div>
            </div>

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setGrantModalOpen(false)}
                disabled={isSubmitting}
              >
                Cancelar
              </Button>
              <Button
                type="submit"
                className="bg-sky-600 hover:bg-sky-700"
                disabled={isSubmitting}
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Gravando...
                  </>
                ) : (
                  "Conceder Habilitação"
                )}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Modal: Suspender Habilitação Técnica */}
      <Dialog open={revokeModalOpen} onOpenChange={setRevokeModalOpen}>
        <DialogContent className="max-w-md">
          <form onSubmit={handleRevoke} className="space-y-4">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2 text-rose-600">
                <AlertCircle className="h-5 w-5" />
                Suspender Habilitação Técnica
              </DialogTitle>
              <DialogDescription>
                A suspensão bloqueia imediatamente o operador de iniciar ou formalizar ensaios neste método.
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-3">
              <p className="text-xs text-slate-600 dark:text-slate-400">
                <strong>Analista:</strong> {selectedQual?.user_name} <br />
                <strong>Método:</strong> {selectedQual?.method_code} — {selectedQual?.method_name}
              </p>

              <div>
                <Label>Justificativa Técnica Mandatória (ALCOA+) *</Label>
                <Textarea
                  value={revokeReason}
                  onChange={(e) => setRevokeReason(e.target.value)}
                  placeholder="Descreva o motivo (ex: necessidade de reciclagem pós-desvio, revisão de norma)..."
                  rows={3}
                  className="mt-1"
                />
              </div>

              <div>
                <Label>Senha para Assinatura Eletrônica (Part 11)</Label>
                <Input
                  type="password"
                  value={revokePassword}
                  onChange={(e) => setRevokePassword(e.target.value)}
                  placeholder="Sua senha para autenticar a suspensão"
                  className="mt-1"
                />
              </div>
            </div>

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setRevokeModalOpen(false)}
                disabled={isSubmitting}
              >
                Cancelar
              </Button>
              <Button
                type="submit"
                variant="destructive"
                disabled={isSubmitting}
              >
                {isSubmitting ? "Suspendendo..." : "Confirmar Suspensão"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Modal: Histórico de Treinamentos */}
      <Dialog open={trainingsModalOpen} onOpenChange={setTrainingsModalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-sky-700 dark:text-sky-300">
              <BookOpen className="h-5 w-5" />
              Treinamentos & Comprovações de Horas
            </DialogTitle>
            <DialogDescription>
              {selectedQual?.user_name} — {selectedQual?.method_code}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-3 max-h-72 overflow-y-auto">
            {selectedQual?.trainings && selectedQual.trainings.length > 0 ? (
              selectedQual.trainings.map((t) => (
                <div
                  key={t.id}
                  className="rounded-lg border border-slate-200 dark:border-slate-800 p-3 text-xs space-y-1"
                >
                  <p className="font-semibold text-slate-800 dark:text-slate-200">{t.title}</p>
                  <p className="text-slate-500">
                    Carga Horária: {t.hours}h | Concluído em: {formatDateTime(t.completed_at)}
                  </p>
                  {t.certificate_code && (
                    <p className="font-mono text-[11px] text-sky-700 dark:text-sky-300">
                      Certificado: {t.certificate_code}
                    </p>
                  )}
                </div>
              ))
            ) : (
              <p className="text-xs text-center text-slate-500 py-4">
                Nenhum treinamento registrado individualmente para esta qualificação.
              </p>
            )}
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setTrainingsModalOpen(false)}
            >
              Fechar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
