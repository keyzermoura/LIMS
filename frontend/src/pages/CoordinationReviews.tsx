import * as React from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  CheckCircle2,
  Loader2,
  RefreshCw,
  Scale,
  ShieldAlert,
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
import { Textarea } from "@/components/ui/input";
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
import { api, ApiError } from "@/lib/api";
import type {
  CoordinationReview,
  CoordinationReviewStatus,
} from "@/lib/types";
import { formatDateTime } from "@/lib/utils";

export function CoordinationReviewsPage() {
  const { user } = useAuth();
  const { push } = useToast();
  const { requestSignature } = useESignature();
  const queryClient = useQueryClient();

  const [activeReview, setActiveReview] = React.useState<CoordinationReview | null>(null);
  const [reviewAction, setReviewAction] =
    React.useState<CoordinationReviewStatus>("APROVADO");
  const [reviewNotes, setReviewNotes] = React.useState("");
  const [submitting, setSubmitting] = React.useState(false);

  const { data: reviews, isLoading, isFetching, refetch } = useQuery<
    CoordinationReview[]
  >({
    queryKey: ["coordination-reviews-pending"],
    queryFn: () => api.get<CoordinationReview[]>("/coordination/reviews/pending"),
  });

  const isCoordinationRole = user?.role === "ADMIN" || user?.role === "FISCAL";

  async function handleDeliberate(e: React.FormEvent) {
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

    // Regra D10: Segregação estrita de funções (4-eyes principle)
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
      await queryClient.invalidateQueries({ queryKey: ["receipts"] });
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Erro ao deliberar revisão.";
      push({ title: "Falha na deliberação", description: msg, variant: "destructive" });
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
            Revisão da Coordenação Técnica
          </h1>
          <p className="text-sm text-muted-foreground">
            Instância superior de deliberação para ressalvas, inconformidades e
            segregação de funções regulatória (Diretriz D10).
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => refetch()}
          disabled={isFetching}
        >
          <RefreshCw className={`mr-2 h-4 w-4 ${isFetching ? "animate-spin" : ""}`} />
          Atualizar
        </Button>
      </div>

      {/* Alerta de Segregação de Funções (Regra D10) */}
      <div className="rounded-lg border border-amber-200 bg-amber-50/70 p-4 text-xs text-amber-950 flex items-start gap-3">
        <ShieldAlert className="h-5 w-5 text-amber-700 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <p className="font-semibold text-sm">
            Diretriz Regulatória D10 — Princípio dos Quatro Olhos (Four-Eyes Principle)
          </p>
          <p className="text-amber-900 leading-relaxed">
            Nenhum ato de admissão com ressalva ou rejeição pode ser deliberado pelo
            mesmo profissional responsável pela conferência ou decisão preliminar.
            A coordenação avalia os apontamentos técnicos de forma independente,
            garantindo imparcialidade e conformidade com as Boas Práticas de Laboratório
            (BPL) e vigilância pós-mercado.
          </p>
        </div>
      </div>

      {/* Lista de Revisões Pendentes */}
      <Card>
        <CardHeader className="border-b pb-4">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg">Revisões Aguardando Deliberação</CardTitle>
              <CardDescription>
                Processos encaminhados por técnicos com apontamento de ressalva ou rejeição
              </CardDescription>
            </div>
            <span className="inline-flex items-center justify-center rounded-full bg-amber-100 px-3 py-1 text-xs font-bold text-amber-900 border border-amber-200">
              {reviews?.length ?? 0} pendente(s)
            </span>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex h-48 items-center justify-center">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : !reviews?.length ? (
            <div className="flex flex-col items-center justify-center py-16 text-center text-muted-foreground">
              <CheckCircle2 className="h-10 w-10 text-emerald-600/70 mb-3" />
              <p className="text-sm font-semibold text-foreground">
                Nenhuma revisão técnica pendente.
              </p>
              <p className="text-xs">
                Todas as conferências físicas e decisões preliminares estão regulares.
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
                          <StatusBadge
                            status={r.decision.decision}
                            kind="decision"
                          />
                        )}
                        <span className="text-xs text-muted-foreground">
                          · Aberto em {formatDateTime(r.created_at)}
                        </span>
                      </div>

                      {/* Dados da decisão técnica preliminar */}
                      <div className="text-xs bg-muted/20 p-3 rounded-lg border space-y-1">
                        <div className="text-muted-foreground">
                          <strong>Decisão Formalizada por:</strong>{" "}
                          <span className="text-foreground font-semibold">
                            {r.decision?.decided_by?.full_name || "Técnico responsável"}
                          </span>{" "}
                          ({r.decision?.decided_by?.role || "TECNICO"})
                        </div>
                        <div className="text-foreground">
                          <strong>Justificativa Preliminar:</strong>{" "}
                          {r.decision?.justification || "Sem justificativa"}
                        </div>
                      </div>

                      {/* Alerta de conflito de autor (D10) */}
                      {isAuthor && (
                        <div className="flex items-center gap-1.5 text-xs font-semibold text-rose-700 bg-rose-50 px-2.5 py-1 rounded border border-rose-200">
                          <XCircle className="h-4 w-4" />
                          Você formalizou a decisão técnica inicial. Outro coordenador deve deliberar.
                        </div>
                      )}
                    </div>

                    <div className="shrink-0 flex items-center gap-2">
                      {isCoordinationRole && (
                        <Button
                          size="sm"
                          disabled={isAuthor}
                          onClick={() => {
                            setActiveReview(r);
                            setReviewAction("APROVADO");
                            setReviewNotes("");
                          }}
                        >
                          <UserCheck className="mr-2 h-4 w-4" />
                          Deliberar Revisão
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

      {/* Modal: Deliberação da Coordenação */}
      <Dialog
        open={Boolean(activeReview)}
        onOpenChange={(open) => !open && setActiveReview(null)}
      >
        <DialogContent className="max-w-md">
          {activeReview && (
            <form onSubmit={handleDeliberate} className="space-y-4">
              <DialogHeader>
                <DialogTitle>Deliberação Superior da Coordenação</DialogTitle>
                <DialogDescription>
                  Avaliação conclusiva de ressalva ou retenção técnica. Requer assinatura eletrônica.
                </DialogDescription>
              </DialogHeader>

              <div className="space-y-1">
                <Label>Ação da Coordenação *</Label>
                <Select
                  value={reviewAction}
                  onValueChange={(val: CoordinationReviewStatus) => setReviewAction(val)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="APROVADO">
                      Aprovar com Ressalva (Liberar para Ensaio)
                    </SelectItem>
                    <SelectItem value="DEVOLVIDO">
                      Devolver para Diligência / Solicitar Informações
                    </SelectItem>
                    <SelectItem value="REJEITADO">
                      Confirmar Rejeição Definitiva
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-1">
                <Label htmlFor="rev-notes">Parecer / Fundamentação da Coordenação *</Label>
                <Textarea
                  id="rev-notes"
                  required
                  rows={4}
                  placeholder="Fundamente os critérios técnicos e regulatórios adotados pela coordenação..."
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                />
              </div>

              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setActiveReview(null)}
                >
                  Cancelar
                </Button>
                <Button type="submit" disabled={submitting}>
                  {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  Assinar e Deliberar
                </Button>
              </DialogFooter>
            </form>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
