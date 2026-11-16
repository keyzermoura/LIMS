import * as React from "react";
import { AlertCircle, FileEdit, FileText, Loader2, ShieldAlert, ShieldCheck } from "lucide-react";

import { Button } from "@/components/ui/button";
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
import { reportsApi, ApiError } from "@/lib/api";
import type { OfficialReport, TestOutcome } from "@/lib/types";

interface OfficialReportAmendModalProps {
  report: OfficialReport;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onReportAmended?: (newReport: OfficialReport) => void;
}

export function OfficialReportAmendModal({
  report,
  open,
  onOpenChange,
  onReportAmended,
}: OfficialReportAmendModalProps) {
  const { push } = useToast();
  const { requestSignature } = useESignature();

  const [amendmentReason, setAmendmentReason] = React.useState("");
  const [title, setTitle] = React.useState(report.title);
  const [conclusion, setConclusion] = React.useState<TestOutcome>(report.conclusion);
  const [summary, setSummary] = React.useState(report.summary || "");
  const [submitting, setSubmitting] = React.useState(false);
  const [amendedReport, setAmendedReport] = React.useState<OfficialReport | null>(null);

  React.useEffect(() => {
    if (open) {
      setAmendmentReason("");
      setTitle(report.title);
      setConclusion(report.conclusion);
      setSummary(report.summary || "");
      setAmendedReport(null);
    }
  }, [open, report]);

  async function handleAmend(e: React.FormEvent) {
    e.preventDefault();
    if (amendmentReason.trim().length < 10) {
      push({
        title: "Justificativa obrigatória",
        description: "A justificativa técnica formal da emenda deve conter ao menos 10 caracteres (ISO/IEC 17025 §7.8.8).",
        variant: "warning",
      });
      return;
    }

    try {
      setSubmitting(true);
      const token = await requestSignature({
        entityType: "OfficialReport",
        entityId: report.id,
        action: "CLOSE",
        meaning: "RESPONSABILIDADE_TECNICA",
        suggestedReason: `Emissão de Emenda Formal ao Laudo ${report.report_number}: ${amendmentReason.trim()}`,
        recordLabel: `Laudo ${report.report_number}`,
      });

      if (!token) {
        setSubmitting(false);
        return;
      }

      const result = await reportsApi.amendOfficial(
        report.id,
        {
          amendment_reason: amendmentReason.trim(),
          title,
          conclusion,
          summary,
        },
        token,
      );

      setAmendedReport(result);
      if (onReportAmended) {
        onReportAmended(result);
      }
      push({
        title: "Emenda emitida com sucesso",
        description: `Novo laudo retificador registrado como Versão ${result.version} (${result.report_number}).`,
        variant: "success",
      });
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Falha ao emitir emenda ao laudo.";
      push({
        title: "Erro na Emissão de Emenda",
        description: msg,
        variant: "destructive",
      });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-xl max-h-[90vh] overflow-y-auto">
        {amendedReport ? (
          <div className="space-y-6 py-4">
            <div className="flex flex-col items-center justify-center text-center space-y-2">
              <div className="rounded-full bg-emerald-100 p-3 text-emerald-700">
                <ShieldCheck className="h-10 w-10" />
              </div>
              <h2 className="text-xl font-bold text-foreground">
                Emenda Homologada com Sucesso!
              </h2>
              <p className="text-sm font-mono font-semibold text-primary">
                {amendedReport.report_number} (Versão {amendedReport.version})
              </p>
            </div>

            <div className="bg-amber-50/60 border border-amber-200 rounded-lg p-4 space-y-2 text-xs text-amber-900">
              <div className="flex items-center gap-1.5 font-bold">
                <ShieldAlert className="h-4 w-4 text-amber-600" />
                Rastreabilidade e Imutabilidade (ISO/IEC 17025 §7.8.8)
              </div>
              <p>
                O laudo anterior (<strong>{report.report_number}</strong>) foi preservado intacto em base histórica com status de superado. O novo laudo substitui o original para todos os efeitos fiscais e jurídicos.
              </p>
            </div>

            <div className="bg-muted/30 border rounded-lg p-4 space-y-3 text-xs">
              <div className="flex justify-between items-center border-b pb-2">
                <span className="text-muted-foreground">Laudo Anterior Substituído:</span>
                <span className="font-mono text-foreground font-semibold">{report.report_number}</span>
              </div>
              <div className="flex justify-between items-center border-b pb-2">
                <span className="text-muted-foreground">Nova Versão Vigente:</span>
                <span className="font-bold text-foreground">Versão {amendedReport.version}</span>
              </div>
              <div className="space-y-1 border-b pb-2">
                <span className="text-muted-foreground font-semibold">Motivação Formal da Emenda:</span>
                <div className="italic text-foreground">{amendedReport.amendment_reason}</div>
              </div>
              <div className="space-y-1">
                <span className="text-muted-foreground font-semibold">Novo Hash SHA-256 do PDF:</span>
                <div className="font-mono text-[11px] bg-background p-2 rounded border break-all text-primary select-all">
                  {amendedReport.sha256_hash}
                </div>
              </div>
            </div>

            <DialogFooter className="flex items-center justify-between gap-2 sm:justify-between">
              <a
                href={reportsApi.getPdfUrl(amendedReport.id)}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 text-xs font-semibold text-primary hover:underline"
              >
                <FileText className="h-4 w-4" />
                Baixar Laudo Emendado em PDF
              </a>
              <Button onClick={() => onOpenChange(false)}>Fechar</Button>
            </DialogFooter>
          </div>
        ) : (
          <form onSubmit={handleAmend} className="space-y-4">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2 text-amber-700">
                <FileEdit className="h-5 w-5" />
                Emissão de Emenda Retificadora ao Laudo Oficial
              </DialogTitle>
              <DialogDescription>
                Em conformidade com a <strong>ISO/IEC 17025:2017 §7.8.8</strong>, a retificação de laudo exige justificativa técnica formal e gera uma nova versão auditada sem sobrescrever o laudo original.
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-2">
              <div className="rounded-md border border-slate-200 bg-slate-50 p-3 text-xs space-y-1">
                <p><strong>Laudo a ser emendado:</strong> <span className="font-mono">{report.report_number}</span> (Versão {report.version})</p>
                <p><strong>Nova versão a ser gerada:</strong> <span className="font-mono font-bold text-primary">Versão {report.version + 1}</span></p>
              </div>

              <div className="space-y-2">
                <Label className="flex items-center gap-1.5">
                  Justificativa Técnica Formal da Emenda <span className="text-rose-500">*</span>
                </Label>
                <Textarea
                  value={amendmentReason}
                  onChange={(e) => setAmendmentReason(e.target.value)}
                  placeholder="Descreva detalhadamente o motivo da retificação (ex.: retificação de grafia do lote, ajuste do parecer conclusivo, inclusão de incerteza complementar)..."
                  rows={3}
                  required
                />
                <p className="text-[11px] text-muted-foreground">Mínimo de 10 caracteres. Ficará exposto publicamente na validação de autenticidade.</p>
              </div>

              <div className="space-y-2">
                <Label>Título Retificado</Label>
                <Input
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label>Conclusão Pericial Retificada</Label>
                <Select
                  value={conclusion}
                  onValueChange={(val) => setConclusion(val as TestOutcome)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="APROVADO">APROVADO — Em conformidade</SelectItem>
                    <SelectItem value="REPROVADO">REPROVADO — Não conforme</SelectItem>
                    <SelectItem value="INCONCLUSIVO">INCONCLUSIVO — Indeterminado</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Sumário Executivo e Fundamentação Técnica Atualizada</Label>
                <Textarea
                  value={summary}
                  onChange={(e) => setSummary(e.target.value)}
                  placeholder="Fundamentação técnica atualizada para constar no documento PDF..."
                  rows={3}
                />
              </div>
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                Cancelar
              </Button>
              <Button
                type="submit"
                disabled={submitting || amendmentReason.trim().length < 10}
                className="bg-amber-600 hover:bg-amber-700 text-white"
              >
                {submitting ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                Assinar e Homologar Emenda
              </Button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}
