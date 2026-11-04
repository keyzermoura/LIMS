import * as React from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ClipboardCheck,
  FileCheck2,
  FlaskConical,
  Loader2,
  LockKeyhole,
  Plus,
  ShieldCheck,
  Sigma,
  TriangleAlert,
} from "lucide-react";
import { useSearchParams } from "react-router-dom";

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
import { useAuth } from "@/hooks/use-auth";
import { useESignature } from "@/hooks/use-esignature";
import { api, ApiError } from "@/lib/api";
import type {
  DeviceSample,
  LabTest,
  Page,
  TestOutcome,
  TestResultResponse,
} from "@/lib/types";
import {
  OUTCOME_LABELS,
  formatDateTime,
  shortHash,
} from "@/lib/utils";

export function TestsPage() {
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const selectedId = searchParams.get("sample");
  const [newTestOpen, setNewTestOpen] = React.useState(false);

  const canWrite =
    user?.role === "ADMIN" || user?.role === "TECNICO" || user?.role === "FISCAL";

  const samplesQuery = useQuery({
    queryKey: ["samples", "recent"],
    queryFn: () => api.get<Page<DeviceSample>>("/samples?size=50"),
  });
  const samples = samplesQuery.data?.items ?? [];

  React.useEffect(() => {
    if (!selectedId && samples.length > 0) {
      setSearchParams({ sample: samples[0].id }, { replace: true });
    }
  }, [selectedId, samples, setSearchParams]);

  const sample = samples.find((item) => item.id === selectedId) ?? null;

  const testsQuery = useQuery({
    queryKey: ["tests", selectedId],
    queryFn: () => api.get<Page<LabTest>>(`/tests?sample_id=${selectedId}&size=100`),
    enabled: Boolean(selectedId),
  });

  const tests = testsQuery.data?.items ?? [];
  const pending = tests.filter((test) => test.status === "PENDENTE").length;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="gap-4 border-b border-border pb-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="min-w-0 flex-1">
            <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-primary">
              Bancada
            </p>
            <CardTitle className="mt-1 text-lg">Execução de ensaios e assinatura de laudos</CardTitle>
            <CardDescription className="mt-1">
              Cada resultado é gravado em versão imutável e assinado com reautenticação.
            </CardDescription>
          </div>

          <div className="flex w-full flex-col gap-2 sm:flex-row sm:items-center lg:w-auto">
            <Select
              value={selectedId ?? undefined}
              onValueChange={(value) => setSearchParams({ sample: value })}
              disabled={samples.length === 0}
            >
              <SelectTrigger className="w-full sm:w-[340px]">
                <SelectValue placeholder="Selecione a amostra" />
              </SelectTrigger>
              <SelectContent>
                {samples.map((item) => (
                  <SelectItem key={item.id} value={item.id}>
                    {item.accession_number} · {item.commercial_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {canWrite ? (
              <Button
                onClick={() => setNewTestOpen(true)}
                disabled={
                  !sample ||
                  sample.status === "DESCARTADO" ||
                  sample.status === "APROVADO"
                }
                title={
                  sample?.status === "APROVADO"
                    ? "Reabra a amostra para EM_TESTE (com assinatura) antes de programar um novo ensaio."
                    : undefined
                }
              >
                <Plus className="h-4 w-4" />
                Novo ensaio
              </Button>
            ) : null}
          </div>
        </CardHeader>

        <CardContent className="grid gap-4 pt-5 sm:grid-cols-2 lg:grid-cols-4">
          <Metric label="Amostra" value={sample?.accession_number ?? "—"} mono />
          <Metric
            label="Status"
            value={
              sample ? (
                <StatusBadge status={sample.status} kind="sample" />
              ) : (
                <span className="text-muted-foreground">—</span>
              )
            }
          />
          <Metric label="Ensaios" value={String(tests.length)} />
          <Metric
            label="Pendentes de assinatura"
            value={
              <span className={pending > 0 ? "text-warning" : "text-success"}>
                {pending}
              </span>
            }
          />
        </CardContent>
      </Card>

      {!sample ? (
        <Card>
          <CardContent className="flex flex-col items-center gap-2 py-16 text-center">
            <FlaskConical className="h-8 w-8 text-muted-foreground/40" />
            <p className="text-sm font-medium">Nenhuma amostra selecionada</p>
            <p className="text-[13px] text-muted-foreground">
              Registre uma amostra no painel de entrada para programar ensaios.
            </p>
          </CardContent>
        </Card>
      ) : testsQuery.isLoading ? (
        <div className="grid gap-4 xl:grid-cols-2">
          {[0, 1].map((index) => (
            <div key={index} className="h-64 animate-pulse rounded-lg bg-muted" />
          ))}
        </div>
      ) : tests.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center gap-3 py-16 text-center">
            <FlaskConical className="h-8 w-8 text-muted-foreground/40" />
            <div>
              <p className="text-sm font-medium">Nenhum ensaio programado</p>
              <p className="mt-1 text-[13px] text-muted-foreground">
                Programe o primeiro ensaio para a amostra {sample.accession_number}.
              </p>
            </div>
            {canWrite && sample.status !== "DESCARTADO" ? (
              <Button
                variant="outline"
                onClick={() => setNewTestOpen(true)}
                disabled={sample.status === "APROVADO"}
                title={
                  sample.status === "APROVADO"
                    ? "Reabra a amostra para EM_TESTE (com assinatura) antes de programar um novo ensaio."
                    : undefined
                }
              >
                <Plus className="h-4 w-4" />
                Programar ensaio
              </Button>
            ) : null}
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 xl:grid-cols-2">
          {tests.map((test) => (
            <TestCard
              key={`${test.id}-${test.version}`}
              test={test}
              onSaved={() => {
                void queryClient.invalidateQueries({ queryKey: ["tests", selectedId] });
                void queryClient.invalidateQueries({ queryKey: ["samples"] });
                void queryClient.invalidateQueries({
                  queryKey: ["timeline", selectedId],
                });
                void queryClient.invalidateQueries({ queryKey: ["capas"] });
              }}
            />
          ))}
        </div>
      )}

      {sample ? (
        <NewTestDialog
          open={newTestOpen}
          onOpenChange={setNewTestOpen}
          sample={sample}
          onCreated={() => {
            void queryClient.invalidateQueries({ queryKey: ["tests", selectedId] });
            void queryClient.invalidateQueries({ queryKey: ["samples"] });
            void queryClient.invalidateQueries({ queryKey: ["timeline", selectedId] });
          }}
        />
      ) : null}
    </div>
  );
}

function Metric({
  label,
  value,
  mono,
}: {
  label: string;
  value: React.ReactNode;
  mono?: boolean;
}) {
  return (
    <div className="rounded-md border border-border bg-muted/25 px-3 py-2.5">
      <p className="data-label">{label}</p>
      <div className={`mt-1 text-sm font-medium ${mono ? "font-mono text-xs" : ""}`}>
        {value}
      </div>
    </div>
  );
}

function TestCard({ test, onSaved }: { test: LabTest; onSaved: () => void }) {
  const { push } = useToast();
  const { requestSignature } = useESignature();
  const { user } = useAuth();

  const isSigned = test.status === "CONCLUIDO";
  const hasLimits = test.lower_limit !== null || test.upper_limit !== null;

  const [value, setValue] = React.useState(test.result_value ?? "");
  const [resultText, setResultText] = React.useState(test.result_text ?? "");
  const [outcome, setOutcome] = React.useState<TestOutcome | "">(test.outcome ?? "");
  const [notes, setNotes] = React.useState(test.notes ?? "");
  const [amendmentReason, setAmendmentReason] = React.useState("");
  const [amending, setAmending] = React.useState(false);
  const [submitting, setSubmitting] = React.useState(false);

  // O backend só permite que o testador designado (ou ADMIN) assine.
  const canSign =
    user?.role === "ADMIN" ||
    (user?.role === "TECNICO" &&
      (!test.tested_by || test.tested_by.id === user.id));
  const otherTester =
    user?.role === "TECNICO" && test.tested_by && test.tested_by.id !== user.id
      ? test.tested_by.full_name
      : null;

  const numericValue = React.useMemo(() => {
    if (!value) return null;
    const parsed = Number(String(value).replace(",", "."));
    return Number.isFinite(parsed) ? parsed : null;
  }, [value]);

  const predictedOutcome: TestOutcome | null = React.useMemo(() => {
    if (!hasLimits) return outcome || null;
    if (numericValue === null) return null;
    if (test.lower_limit !== null && numericValue < Number(test.lower_limit)) {
      return "REPROVADO";
    }
    if (test.upper_limit !== null && numericValue > Number(test.upper_limit)) {
      return "REPROVADO";
    }
    return "APROVADO";
  }, [hasLimits, numericValue, outcome, test.lower_limit, test.upper_limit]);

  async function handleSign(event: React.FormEvent) {
    event.preventDefault();

    if (!hasLimits && outcome === "") {
      push({ variant: "warning", title: "Selecione o desfecho do ensaio." });
      return;
    }
    if (hasLimits && numericValue === null) {
      push({ variant: "warning", title: "Informe um resultado numérico válido." });
      return;
    }
    if (!hasLimits && resultText.trim().length < 2) {
      push({
        variant: "warning",
        title: "Descreva o resultado observado",
        description: "Ensaios qualitativos exigem a descrição do achado.",
      });
      return;
    }
    if (isSigned && amendmentReason.trim().length < 10) {
      push({
        variant: "warning",
        title: "Justifique a emenda",
        description:
          "Resultados assinados são imutáveis. Descreva o motivo da correção.",
      });
      return;
    }

    const token = await requestSignature({
      entityType: "LabTest",
      entityId: test.id,
      action: "UPDATE",
      meaning: "RESPONSABILIDADE_TECNICA",
      title: isSigned ? "Assinar emenda de laudo" : "Assinar laudo do ensaio",
      recordLabel: test.name,
      suggestedReason: isSigned
        ? amendmentReason.trim()
        : `Lançamento e assinatura do resultado do ensaio ${test.name} (${test.unit}).`,
    });
    if (!token) return;

    setSubmitting(true);
    try {
      const response = await api.patch<TestResultResponse>(
        `/tests/${test.id}/result`,
        {
          result_value: hasLimits ? numericValue : null,
          result_text: hasLimits ? null : resultText.trim(),
          outcome: hasLimits ? null : outcome,
          notes: notes.trim() || null,
          amendment_reason: isSigned ? amendmentReason.trim() : null,
          version: test.version,
        },
        token,
      );

      if (response.alert) {
        push({
          variant: "destructive",
          title: "Resultado reprovado — CAPA aberta",
          description: response.alert.message,
        });
      } else {
        push({
          variant: "success",
          title: "Laudo assinado",
          description: `Versão ${response.result_version.version} registrada · auditoria #${response.audit_log_id}.`,
        });
      }
      setAmending(false);
      setAmendmentReason("");
      onSaved();
    } catch (error) {
      push({
        variant: "destructive",
        title: "Não foi possível gravar o resultado",
        description:
          error instanceof ApiError ? error.message : "Verifique os dados.",
      });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Card className="flex flex-col">
      <CardHeader className="gap-2 border-b border-border pb-4">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <CardTitle className="text-[15px] leading-snug">{test.name}</CardTitle>
            <CardDescription className="mt-1 text-[12px]">
              {test.method ?? "Método não informado"}
            </CardDescription>
          </div>
          <StatusBadge status={test.status} kind="test" />
        </div>
        <div className="flex flex-wrap items-center gap-2 text-[11px] text-muted-foreground">
          <span className="inline-flex items-center gap-1 rounded border border-border bg-muted/40 px-1.5 py-0.5">
            <Sigma className="h-3 w-3" />
            {test.lower_limit !== null ? `${Number(test.lower_limit)}` : "—"} a{" "}
            {test.upper_limit !== null ? `${Number(test.upper_limit)}` : "—"} {test.unit}
          </span>
          {test.acceptance_criteria ? (
            <span className="line-clamp-1">{test.acceptance_criteria}</span>
          ) : null}
          <span className="ml-auto font-mono">v{test.result_version}</span>
        </div>
      </CardHeader>

      <CardContent className="flex flex-1 flex-col gap-4 pt-4">
        {isSigned && test.signed_at ? (
          <div className="flex items-start gap-2 rounded-md border border-emerald-200 bg-emerald-50/60 px-3 py-2.5">
            <LockKeyhole className="mt-0.5 h-4 w-4 shrink-0 text-emerald-700" />
            <div className="min-w-0 text-[12px] leading-snug text-emerald-950">
              <p className="font-semibold">
                Resultado assinado por {test.signed_by?.full_name ?? "—"}
              </p>
              <p className="text-emerald-900/80">
                {formatDateTime(test.signed_at)} ·{" "}
                {test.outcome ? OUTCOME_LABELS[test.outcome] : "sem desfecho"}
              </p>
              <p className="mt-1 font-mono text-[10px] text-emerald-900/70">
                assinatura {shortHash(test.signature_id, 14)}
              </p>
            </div>
          </div>
        ) : null}

        <form onSubmit={handleSign} className="flex flex-1 flex-col gap-4">
          {isSigned && !amending ? (
            <div className="rounded-md border border-border bg-muted/30 px-3 py-3">
              <p className="data-label">Resultado registrado</p>
              <p className="mt-1 text-2xl font-semibold tabular-nums">
                {test.result_value !== null
                  ? Number(test.result_value).toLocaleString("pt-BR", {
                      maximumFractionDigits: 4,
                    })
                  : "—"}
                <span className="ml-1 text-sm font-normal text-muted-foreground">
                  {test.unit}
                </span>
              </p>
              {test.result_text ? (
                <p className="mt-1 text-[13px]">{test.result_text}</p>
              ) : null}
              {test.notes ? (
                <p className="mt-2 border-t border-border pt-2 text-[12px] text-muted-foreground">
                  {test.notes}
                </p>
              ) : null}
            </div>
          ) : (
            <>
              {hasLimits ? (
                <div className="grid gap-1.5">
                  <Label htmlFor={`result-${test.id}`}>
                    Resultado medido ({test.unit}) *
                  </Label>
                  <div className="relative">
                    <Input
                      id={`result-${test.id}`}
                      inputMode="decimal"
                      value={value}
                      onChange={(event) => setValue(event.target.value)}
                      placeholder="0,00"
                      className="pr-14 text-lg font-semibold tabular-nums"
                      autoComplete="off"
                    />
                    <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-xs text-muted-foreground">
                      {test.unit}
                    </span>
                  </div>
                </div>
              ) : (
                <>
                  <div className="grid gap-1.5">
                    <Label htmlFor={`outcome-${test.id}`}>Desfecho *</Label>
                    <Select
                      value={outcome}
                      onValueChange={(next) => setOutcome(next as TestOutcome)}
                    >
                      <SelectTrigger id={`outcome-${test.id}`}>
                        <SelectValue placeholder="Selecione o desfecho" />
                      </SelectTrigger>
                      <SelectContent>
                        {(["APROVADO", "REPROVADO", "INCONCLUSIVO"] as TestOutcome[]).map(
                          (option) => (
                            <SelectItem key={option} value={option}>
                              {OUTCOME_LABELS[option]}
                            </SelectItem>
                          ),
                        )}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="grid gap-1.5">
                    <Label htmlFor={`text-${test.id}`}>Resultado observado *</Label>
                    <Textarea
                      id={`text-${test.id}`}
                      rows={2}
                      value={resultText}
                      onChange={(event) => setResultText(event.target.value)}
                      placeholder="Descrição qualitativa do achado."
                    />
                  </div>
                </>
              )}

              <div className="grid gap-1.5">
                <Label htmlFor={`notes-${test.id}`}>Observações do ensaio</Label>
                <Textarea
                  id={`notes-${test.id}`}
                  rows={2}
                  value={notes}
                  onChange={(event) => setNotes(event.target.value)}
                  placeholder="Condições ambientais, corpo de prova, repetições…"
                />
              </div>

              {isSigned ? (
                <div className="grid gap-1.5">
                  <Label htmlFor={`amendment-${test.id}`}>
                    Motivo da emenda (obrigatório) *
                  </Label>
                  <Textarea
                    id={`amendment-${test.id}`}
                    rows={2}
                    value={amendmentReason}
                    onChange={(event) => setAmendmentReason(event.target.value)}
                    placeholder="Ex.: Correção de transcrição do valor lido no equipamento."
                  />
                  <p className="text-[11px] text-muted-foreground">
                    A versão anterior é preservada. A emenda cria a versão{" "}
                    {test.result_version + 1}.
                  </p>
                </div>
              ) : null}
            </>
          )}

          {predictedOutcome === "REPROVADO" && (!isSigned || amending) ? (
            <div className="flex items-start gap-2 rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-[12px] text-rose-900">
              <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0" />
              <span>
                Resultado fora do limite de tolerância. Ao assinar, uma CAPA será
                aberta automaticamente e o alerta será registrado.
              </span>
            </div>
          ) : null}

          {canSign ? (
            <div className="mt-auto flex flex-wrap items-center gap-2">
              {isSigned && !amending ? (
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setAmending(true)}
                >
                  <FileCheck2 className="h-4 w-4" />
                  Emitir emenda
                </Button>
              ) : (
                <>
                  <Button type="submit" disabled={submitting}>
                    {submitting ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <ShieldCheck className="h-4 w-4" />
                    )}
                    {isSigned ? "Salvar emenda assinada" : "Salvar e assinar laudo"}
                  </Button>
                  {isSigned ? (
                    <Button
                      type="button"
                      variant="ghost"
                      onClick={() => setAmending(false)}
                      disabled={submitting}
                    >
                      Cancelar
                    </Button>
                  ) : null}
                </>
              )}
              <span className="ml-auto inline-flex items-center gap-1 text-[11px] text-muted-foreground">
                <ClipboardCheck className="h-3 w-3" />
                auditoria automática
              </span>
            </div>
          ) : (
            <p className="mt-auto rounded border border-dashed border-border px-3 py-2 text-[11px] text-muted-foreground">
              {otherTester
                ? `Aguardando assinatura do testador responsável (${otherTester}).`
                : "Somente técnicos e administradores podem assinar laudos."}
            </p>
          )}
        </form>
      </CardContent>
    </Card>
  );
}

function NewTestDialog({
  open,
  onOpenChange,
  sample,
  onCreated,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  sample: DeviceSample;
  onCreated: () => void;
}) {
  const { push } = useToast();
  const { requestSignature } = useESignature();
  const [name, setName] = React.useState("");
  const [method, setMethod] = React.useState("");
  const [unit, setUnit] = React.useState("");
  const [lower, setLower] = React.useState("");
  const [upper, setUpper] = React.useState("");
  const [criteria, setCriteria] = React.useState("");
  const [submitting, setSubmitting] = React.useState(false);

  React.useEffect(() => {
    if (!open) return;
    setName("");
    setMethod("");
    setUnit("");
    setLower("");
    setUpper("");
    setCriteria("");
  }, [open]);

  async function handleCreate(event: React.FormEvent) {
    event.preventDefault();
    if (name.trim().length < 2 || !unit.trim()) {
      push({ variant: "warning", title: "Informe nome e unidade do ensaio." });
      return;
    }

    const id = crypto.randomUUID();
    const token = await requestSignature({
      entityType: "LabTest",
      entityId: id,
      action: "CREATE",
      meaning: "AUTORIA",
      title: "Programar novo ensaio",
      recordLabel: `${name} · ${sample.accession_number}`,
      suggestedReason: `Programação do ensaio ${name} para a amostra ${sample.accession_number}.`,
    });
    if (!token) return;

    setSubmitting(true);
    try {
      await api.post(
        "/tests",
        {
          id,
          device_sample_id: sample.id,
          name: name.trim(),
          method: method.trim() || null,
          parameters: {},
          unit: unit.trim(),
          lower_limit: lower.trim() ? Number(lower.replace(",", ".")) : null,
          upper_limit: upper.trim() ? Number(upper.replace(",", ".")) : null,
          acceptance_criteria: criteria.trim() || null,
        },
        token,
      );
      push({
        variant: "success",
        title: "Ensaio programado",
        description:
          sample.status === "RECEBIDO"
            ? "A amostra foi movida para o status Em teste."
            : `Ensaio registrado no protocolo da amostra ${sample.accession_number}.`,
      });
      onOpenChange(false);
      onCreated();
    } catch (error) {
      push({
        variant: "destructive",
        title: "Não foi possível programar",
        description:
          error instanceof ApiError ? error.message : "Verifique os dados.",
      });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Programar ensaio</DialogTitle>
          <DialogDescription>
            {sample.accession_number} · {sample.commercial_name}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleCreate} className="grid gap-4">
          <div className="grid gap-1.5">
            <Label htmlFor="test-name">Nome do ensaio *</Label>
            <Input
              id="test-name"
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="Ex.: Resistência mecânica"
              required
            />
          </div>
          <div className="grid gap-1.5">
            <Label htmlFor="test-method">Método / norma</Label>
            <Input
              id="test-method"
              value={method}
              onChange={(event) => setMethod(event.target.value)}
              placeholder="Ex.: ABNT NBR IEC 60601-1"
            />
          </div>
          <div className="grid gap-4 sm:grid-cols-3">
            <div className="grid gap-1.5">
              <Label htmlFor="test-unit">Unidade *</Label>
              <Input
                id="test-unit"
                value={unit}
                onChange={(event) => setUnit(event.target.value)}
                placeholder="N"
                required
              />
            </div>
            <div className="grid gap-1.5">
              <Label htmlFor="test-lower">Limite inferior</Label>
              <Input
                id="test-lower"
                inputMode="decimal"
                value={lower}
                onChange={(event) => setLower(event.target.value)}
                placeholder="10"
              />
            </div>
            <div className="grid gap-1.5">
              <Label htmlFor="test-upper">Limite superior</Label>
              <Input
                id="test-upper"
                inputMode="decimal"
                value={upper}
                onChange={(event) => setUpper(event.target.value)}
                placeholder="50"
              />
            </div>
          </div>
          <div className="grid gap-1.5">
            <Label htmlFor="test-criteria">Critério de aceitação</Label>
            <Textarea
              id="test-criteria"
              rows={2}
              value={criteria}
              onChange={(event) => setCriteria(event.target.value)}
              placeholder="Descreva o critério objetivo de aprovação."
            />
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={submitting}
            >
              Cancelar
            </Button>
            <Button type="submit" disabled={submitting}>
              {submitting ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <ShieldCheck className="h-4 w-4" />
              )}
              Programar e assinar
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
