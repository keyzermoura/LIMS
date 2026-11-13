import * as React from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  CheckCircle2,
  FileCheck2,
  FileText,
  Loader2,
  QrCode,
  RefreshCw,
  Scale,
  ShieldAlert,
  ShieldCheck,
  UserCheck,
  XCircle,
} from "lucide-react";

import { StatusBadge } from "@/components/StatusBadge";
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
import { useESignature } from "@/hooks/use-esignature";
import { useAuth } from "@/hooks/use-auth";
import { api, ApiError, reportsApi, reviewsApi } from "@/lib/api";
import type {
  CoordinationReview,
  CoordinationReviewStatus,
  LabTest,
  OfficialReport,
  TestOutcome,
} from "@/lib/types";
import { formatDateTime } from "@/lib/utils";

export function CoordinationReviewsPage() {
  const { user } = useAuth();
  const { push } = useToast();
  const { requestSignature } = useESignature();
  const queryClient = useQueryClient();

  const [activeTab, setActiveTab] = React.useState<"receipts" | "tests" | "reports">("receipts");

  // Estados de Revisão de Recebimento (Fase 1)
  const [activeReview, setActiveReview] = React.useState<CoordinationReview | null>(null);
  const [reviewAction, setReviewAction] = React.useState<CoordinationReviewStatus>("APROVADO");
  const [reviewNotes, setReviewNotes] = React.useState("");
  const [submitting, setSubmitting] = React.useState(false);

  // Estados de Revisão por Pares de Ensaios (Fase 3)
  const [activeTestReview, setActiveTestReview] = React.useState<LabTest | null>(null);
  const [testDecisionStatus, setTestDecisionStatus] = React.useState<CoordinationReviewStatus>("APROVADO");
  const [testJustification, setTestJustification] = React.useState("");
  const [testReviewNotes, setTestReviewNotes] = React.useState("");

  // Estados de Emissão de Laudo Oficial
  const [showReportDialog, setShowReportDialog] = React.useState(false);
  const [reportTitle, setReportTitle] = React.useState("Laudo Pericial Oficial de Conformidade Técnica");
  const [reportConclusion, setReportConclusion] = React.useState<TestOutcome>("APROVADO");
  const [reportSummary, setReportSummary] = React.useState("");
  const [issuedReport, setIssuedReport] = React.useState<OfficialReport | null>(null);

  // Queries
  const {
    data: reviews,
    isLoading: isLoadingReviews,
    isFetching: isFetchingReviews,
    refetch: refetchReviews,
  } = useQuery<CoordinationReview[]>({
    queryKey: ["coordination-reviews-pending"],
    queryFn: () => api.get<CoordinationReview[]>("/coordination/reviews/pending"),
  });

  const {
    data: pendingTests,
    isLoading: isLoadingTests,
    isFetching: isFetchingTests,
    refetch: refetchTests,
  } = useQuery<LabTest[]>({
    queryKey: ["test-reviews-pending"],
    queryFn: () => reviewsApi.listPending(),
  });

  const isCoordinationRole = user?.role === "ADMIN" || user?.role === "FISCAL";

  // Deliberação de Recebimento
  async function handleDeliberateReceipt(e: React.FormEvent) {
    e.preventDefault();
    if (!activeReview) return;

    if (reviewNotes.trim().length < 5) {
      push({
        title: "Justificativa obrigatória",
        description: "Informe uma fundamentação de no mínimo 5 caracteres.",
        variant: "warning",
      });
      return;
    }

    if (activeReview.decision?.decided_by?.id === user?.id) {
      push({
        title: "Violação de Segregação (D10)",
        description:
          "Você formalizou a decisão técnica original. Outro fiscal ou coordenador deve deliberar esta revisão.",
        variant: "destructive",
      });
      return;
    }

    try {
      setSubmitting(true);
      const token = await requestSignature({
        entityType: "CoordinationReview",
        entityId: activeReview.id,
        action: "UPDATE",
        meaning: "APROVACAO",
        suggestedReason: `Deliberação da coordenação: ${reviewAction}`,
        recordLabel: `Revisão ${activeReview.id.slice(0, 8)}`,
      });

      if (!token) {
        setSubmitting(false);
        return;
      }

      await api.post(
        `/coordination/reviews/${activeReview.id}/action`,
        {
          status: reviewAction,
          review_notes: reviewNotes.trim(),
        },
        token,
      );

      push({
        title: "Deliberação Registrada",
        description: `Revisão concluída com status: ${reviewAction}.`,
        variant: "success",
      });

      setActiveReview(null);
      setReviewNotes("");
      await queryClient.invalidateQueries({ queryKey: ["coordination-reviews-pending"] });
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Erro ao deliberar revisão.";
      push({ title: "Falha na deliberação", description: msg, variant: "destructive" });
    } finally {
      setSubmitting(false);
    }
  }

  // Julgamento de Ensaio por Pares (Peer Review)
  async function handleDeliberateTest(e: React.FormEvent) {
    e.preventDefault();
    if (!activeTestReview) return;

    if (activeTestReview.tested_by?.id === user?.id && user?.role !== "ADMIN") {
      push({
        title: "Segregação de Funções Violada (ISO/IEC 17025)",
        description: "O revisor técnico independente não pode ser o mesmo analista que executou o ensaio.",
        variant: "destructive",
      });
      return;
    }

    if (testDecisionStatus === "DEVOLVIDO" && testJustification.trim().length < 10) {
      push({
        title: "Justificativa Obrigatória",
        description: "Ao devolver ensaio com ressalva, informe uma justificativa técnica detalhada (mínimo 10 caracteres).",
        variant: "warning",
      });
      return;
    }

    try {
      setSubmitting(true);
      const token = await requestSignature({
        entityType: "LabTest",
        entityId: activeTestReview.id,
        action: "UPDATE",
        meaning: "APROVACAO",
        suggestedReason: `Parecer de revisão técnica por pares: ${testDecisionStatus}`,
        recordLabel: `Ensaio ${activeTestReview.name}`,
      });

      if (!token) {
        setSubmitting(false);
        return;
      }

      await reviewsApi.decide(
        activeTestReview.id,
        {
          status: testDecisionStatus,
          justification: testJustification.trim() || null,
          notes: testReviewNotes.trim() || null,
        },
        token,
      );

      push({
        title: "Parecer Técnico Registrado",
        description: `O ensaio foi homologado com status: ${testDecisionStatus}.`,
        variant: "success",
      });

      setActiveTestReview(null);
      setTestJustification("");
      setTestReviewNotes("");
      await queryClient.invalidateQueries({ queryKey: ["test-reviews-pending"] });
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Erro ao emitir parecer.";
      push({ title: "Falha no parecer", description: msg, variant: "destructive" });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <Scale className="h-6 w-6 text-primary" />
            Revisão e Homologação Técnica
          </h1>
          <p className="text-sm text-muted-foreground">
            Instância colegiada de segregação de funções (ISO/IEC 17025) e deliberação técnica regulatória.
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            refetchReviews();
            refetchTests();
          }}
          disabled={isFetchingReviews || isFetchingTests}
        >
          <RefreshCw className={`mr-2 h-4 w-4 ${isFetchingReviews || isFetchingTests ? "animate-spin" : ""}`} />
          Atualizar
        </Button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-border space-x-4">
        <button
          type="button"
          onClick={() => setActiveTab("receipts")}
          className={`pb-3 text-sm font-semibold border-b-2 transition-colors flex items-center gap-2 ${
            activeTab === "receipts"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <UserCheck className="h-4 w-4" />
          Decisões de Recebimento (Fase 1 / D10)
          {Boolean(reviews?.length) && (
            <span className="ml-1 rounded-full bg-amber-100 px-2 py-0.5 text-xs font-bold text-amber-900 border border-amber-200">
              {reviews?.length}
            </span>
          )}
        </button>

        <button
          type="button"
          onClick={() => setActiveTab("tests")}
          className={`pb-3 text-sm font-semibold border-b-2 transition-colors flex items-center gap-2 ${
            activeTab === "tests"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <FileCheck2 className="h-4 w-4" />
          Revisão de Ensaios por Pares (Fase 3 / ISO 17025)
          {Boolean(pendingTests?.length) && (
            <span className="ml-1 rounded-full bg-blue-100 px-2 py-0.5 text-xs font-bold text-blue-900 border border-blue-200">
              {pendingTests?.length}
            </span>
          )}
        </button>
      </div>

      {/* TAB 1: Recebimentos */}
      {activeTab === "receipts" && (
        <div className="space-y-4">
          <div className="rounded-lg border border-amber-200 bg-amber-50/70 p-4 text-xs text-amber-950 flex items-start gap-3">
            <ShieldAlert className="h-5 w-5 text-amber-700 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <p className="font-semibold text-sm">
                Diretriz Regulatória D10 — Princípio dos Quatro Olhos (Four-Eyes Principle)
              </p>
              <p className="text-amber-900 leading-relaxed">
                Nenhum ato de admissão com ressalva ou rejeição pode ser deliberado pelo
                mesmo profissional responsável pela conferência física ou decisão preliminar.
              </p>
            </div>
          </div>

          <Card>
            <CardHeader className="border-b pb-4">
              <CardTitle className="text-lg">Revisões de Recebimento Pendentes</CardTitle>
              <CardDescription>
                Processos encaminhados com apontamento de ressalva ou rejeição física
              </CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              {isLoadingReviews ? (
                <div className="flex h-48 items-center justify-center">
                  <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                </div>
              ) : !reviews?.length ? (
                <div className="flex flex-col items-center justify-center py-16 text-center text-muted-foreground">
                  <CheckCircle2 className="h-10 w-10 text-emerald-600/70 mb-3" />
                  <p className="text-sm font-semibold text-foreground">
                    Nenhuma revisão de recebimento pendente.
                  </p>
                </div>
              ) : (
                <div className="divide-y divide-border">
                  {reviews.map((r) => {
                    const isAuthor = r.decision?.decided_by?.id === user?.id;
                    return (
                      <div
                        key={r.id}
                        className="p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:bg-muted/10 transition-colors"
                      >
                        <div className="space-y-2">
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-muted">
                              ID: {r.id.slice(0, 8)}
                            </span>
                            <StatusBadge status={r.status} kind="coordination" />
                            {r.decision && (
                              <StatusBadge status={r.decision.decision} kind="decision" />
                            )}
                            <span className="text-xs text-muted-foreground">
                              · Aberto em {formatDateTime(r.created_at)}
                            </span>
                          </div>
                          <div className="text-xs bg-muted/20 p-3 rounded-lg border space-y-1">
                            <div>
                              <strong>Decisão Formalizada por:</strong>{" "}
                              <span className="text-foreground font-semibold">
                                {r.decision?.decided_by?.full_name || "Técnico"}
                              </span>{" "}
                              ({r.decision?.decided_by?.role || "TECNICO"})
                            </div>
                            <div>
                              <strong>Justificativa:</strong> {r.decision?.justification || "Sem justificativa"}
                            </div>
                          </div>
                        </div>

                        <div>
                          {isAuthor ? (
                            <span className="text-xs text-amber-700 italic border border-amber-300 bg-amber-50 px-3 py-1.5 rounded-md">
                              Bloqueado (Autor da Decisão)
                            </span>
                          ) : (
                            <Button
                              size="sm"
                              disabled={!isCoordinationRole}
                              onClick={() => {
                                setActiveReview(r);
                                setReviewAction("APROVADO");
                                setReviewNotes("");
                              }}
                            >
                              Deliberar
                            </Button>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* TAB 2: Revisão Técnica de Ensaios por Pares (Fase 3) */}
      {activeTab === "tests" && (
        <div className="space-y-4">
          <div className="rounded-lg border border-blue-200 bg-blue-50/70 p-4 text-xs text-blue-950 flex items-start gap-3">
            <ShieldCheck className="h-5 w-5 text-blue-700 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <p className="font-semibold text-sm">
                Segregação Técnica ISO/IEC 17025 §7.7 e 21 CFR Part 11
              </p>
              <p className="text-blue-900 leading-relaxed">
                Todo ensaio concluído na bancada exige revisão e homologação independente por outro par técnico
                ou coordenação analítica antes de poder compor o Laudo Pericial Oficial consolidado.
              </p>
            </div>
          </div>

          <Card>
            <CardHeader className="border-b pb-4">
              <CardTitle className="text-lg">Ensaios Analíticos Aguardando Homologação</CardTitle>
              <CardDescription>
                Resultados de bancada concluídos com assinaturas de execução prontas para peer review
              </CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              {isLoadingTests ? (
                <div className="flex h-48 items-center justify-center">
                  <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                </div>
              ) : !pendingTests?.length ? (
                <div className="flex flex-col items-center justify-center py-16 text-center text-muted-foreground">
                  <CheckCircle2 className="h-10 w-10 text-emerald-600/70 mb-3" />
                  <p className="text-sm font-semibold text-foreground">
                    Nenhum ensaio pendente de revisão técnica.
                  </p>
                  <p className="text-xs">
                    Todos os ensaios analíticos concluídos foram devidamente homologados ou devolvidos.
                  </p>
                </div>
              ) : (
                <div className="divide-y divide-border">
                  {pendingTests.map((test) => {
                    const isTester = test.tested_by?.id === user?.id && user?.role !== "ADMIN";

                    return (
                      <div
                        key={test.id}
                        className="p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:bg-muted/10 transition-colors"
                      >
                        <div className="space-y-2">
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-muted">
                              ID: {test.id.slice(0, 8)}
                            </span>
                            <span className="font-semibold text-sm text-foreground">{test.name}</span>
                            <StatusBadge status={test.status} kind="test" />
                            {test.outcome && <StatusBadge status={test.outcome} kind="outcome" />}
                          </div>

                          <div className="text-xs grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 bg-muted/20 p-3 rounded-lg border">
                            <div>
                              <strong>Resultado:</strong>{" "}
                              <span className="font-mono text-foreground font-bold">
                                {test.result_value ?? "—"} {test.unit}
                              </span>
                            </div>
                            <div>
                              <strong>Critério de Aceitação:</strong>{" "}
                              <span className="text-muted-foreground">{test.acceptance_criteria || "Sem especificação"}</span>
                            </div>
                            <div>
                              <strong>Analista Executor:</strong>{" "}
                              <span className="text-foreground font-semibold">
                                {test.tested_by?.full_name || "Desconhecido"}
                              </span>
                            </div>
                          </div>
                        </div>

                        <div>
                          {isTester ? (
                            <span className="text-xs text-amber-700 italic border border-amber-300 bg-amber-50 px-3 py-1.5 rounded-md">
                              Bloqueado (Executor do Ensaio)
                            </span>
                          ) : (
                            <Button
                              size="sm"
                              onClick={() => {
                                setActiveTestReview(test);
                                setTestDecisionStatus("APROVADO");
                                setTestJustification("");
                                setTestReviewNotes("");
                              }}
                            >
                              Emitir Parecer
                            </Button>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Dialog: Deliberação de Recebimento (Fase 1) */}
      <Dialog open={Boolean(activeReview)} onOpenChange={(open) => !open && setActiveReview(null)}>
        <DialogContent>
          <form onSubmit={handleDeliberateReceipt}>
            <DialogHeader>
              <DialogTitle>Deliberação da Coordenação Técnica</DialogTitle>
              <DialogDescription>
                Emissão de parecer independente formal com assinatura eletrônica.
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Decisão da Coordenação</Label>
                <Select
                  value={reviewAction}
                  onValueChange={(val) => setReviewAction(val as CoordinationReviewStatus)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="APROVADO">Aprovar (Com ou sem ressalvas aceitas)</SelectItem>
                    <SelectItem value="DEVOLVIDO">Devolver para retificação técnica</SelectItem>
                    <SelectItem value="REJEITADO">Rejeitar definitivamente</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Parecer / Fundamentação Técnica</Label>
                <Textarea
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                  placeholder="Fundamentação regulatória da deliberação colegiada..."
                  rows={4}
                  required
                />
              </div>
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setActiveReview(null)}>
                Cancelar
              </Button>
              <Button type="submit" disabled={submitting}>
                {submitting ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                Assinar e Concluir Deliberação
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Dialog: Parecer Técnico de Ensaio (Fase 3 - Peer Review) */}
      <Dialog open={Boolean(activeTestReview)} onOpenChange={(open) => !open && setActiveTestReview(null)}>
        <DialogContent>
          <form onSubmit={handleDeliberateTest}>
            <DialogHeader>
              <DialogTitle>Revisão Técnica por Pares (Peer Review)</DialogTitle>
              <DialogDescription>
                Homologação técnica independente do ensaio analítico:{" "}
                <strong className="text-foreground">{activeTestReview?.name}</strong>
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Parecer da Revisão</Label>
                <Select
                  value={testDecisionStatus}
                  onValueChange={(val) => setTestDecisionStatus(val as CoordinationReviewStatus)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="APROVADO">Aprovar e Homologar Ensaio</SelectItem>
                    <SelectItem value="DEVOLVIDO">Devolver com Ressalva (Exige Reteste/Correção)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {testDecisionStatus === "DEVOLVIDO" && (
                <div className="space-y-2">
                  <Label className="text-destructive font-semibold">
                    Justificativa Obrigatória da Devolução (mínimo 10 caracteres)
                  </Label>
                  <Textarea
                    value={testJustification}
                    onChange={(e) => setTestJustification(e.target.value)}
                    placeholder="Descreva detalhadamente o motivo da não aprovação ou necessidade de repetição..."
                    rows={3}
                    required
                  />
                </div>
              )}

              <div className="space-y-2">
                <Label>Observações e Apontamentos Técnicos</Label>
                <Textarea
                  value={testReviewNotes}
                  onChange={(e) => setTestReviewNotes(e.target.value)}
                  placeholder="Comentários sobre a conformidade metrológica e analítica..."
                  rows={3}
                />
              </div>
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setActiveTestReview(null)}>
                Cancelar
              </Button>
              <Button type="submit" disabled={submitting}>
                {submitting ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                Assinar e Homologar Parecer
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
