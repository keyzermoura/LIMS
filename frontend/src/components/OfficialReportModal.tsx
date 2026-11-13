import * as React from "react";
import { CheckCircle2, Copy, FileText, Loader2, QrCode, ShieldCheck } from "lucide-react";

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
import type { DeviceSample, LabTest, OfficialReport, TestOutcome } from "@/lib/types";

interface OfficialReportModalProps {
  sample: DeviceSample;
  tests: LabTest[];
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onReportIssued?: (report: OfficialReport) => void;
}

export function OfficialReportModal({
  sample,
  tests,
  open,
  onOpenChange,
  onReportIssued,
}: OfficialReportModalProps) {
  const { push } = useToast();
  const { requestSignature } = useESignature();

  const approvedTests = tests.filter(
    (t) => t.status === "CONCLUIDO" && t.review_status === "APROVADO",
  );

  const [selectedTestIds, setSelectedTestIds] = React.useState<string[]>([]);
  const [title, setTitle] = React.useState("Laudo Pericial Oficial de Conformidade Técnica");
  const [conclusion, setConclusion] = React.useState<TestOutcome>("APROVADO");
  const [summary, setSummary] = React.useState("");
  const [submitting, setSubmitting] = React.useState(false);
  const [issuedReport, setIssuedReport] = React.useState<OfficialReport | null>(null);

  React.useEffect(() => {
    if (open) {
      setSelectedTestIds(approvedTests.map((t) => t.id));
      setIssuedReport(null);
    }
  }, [open, tests]);

  function toggleTest(id: string) {
    setSelectedTestIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id],
    );
  }

  async function handleGenerate(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedTestIds.length) {
      push({
        title: "Seleção obrigatória",
        description: "Selecione ao menos um ensaio aprovado para consolidar no laudo oficial.",
        variant: "warning",
      });
      return;
    }

    try {
      setSubmitting(true);
      const token = await requestSignature({
        entityType: "DeviceSample",
        entityId: sample.id,
        action: "CLOSE",
        meaning: "RESPONSABILIDADE_TECNICA",
        suggestedReason: `Emissão formal de Laudo Oficial: ${title}`,
        recordLabel: `Amostra ${sample.accession_number}`,
      });

      if (!token) {
        setSubmitting(false);
        return;
      }

      const report = await reportsApi.generateOfficial(
        {
          device_sample_id: sample.id,
          test_ids: selectedTestIds,
          title,
          conclusion,
          summary: summary.trim() || null,
        },
        token,
      );

      setIssuedReport(report);
      onReportIssued?.(report);
      push({
        title: "Laudo Pericial Emitido",
        description: `Laudo oficial ${report.report_number} gerado com hash SHA-256 e assinatura eletrônica.`,
        variant: "success",
      });
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Erro ao emitir laudo oficial.";
      push({ title: "Falha na emissão", description: msg, variant: "destructive" });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        {issuedReport ? (
          <div className="space-y-6 py-4">
            <div className="flex flex-col items-center justify-center text-center space-y-2">
              <div className="rounded-full bg-emerald-100 p-3 text-emerald-700">
                <ShieldCheck className="h-10 w-10" />
              </div>
              <h2 className="text-xl font-bold text-foreground">
                Laudo Oficial Emitido com Sucesso!
              </h2>
              <p className="text-sm font-mono font-semibold text-primary">
                {issuedReport.report_number}
              </p>
            </div>

            <div className="bg-muted/30 border rounded-lg p-4 space-y-3 text-xs">
              <div className="flex justify-between items-center border-b pb-2">
                <span className="text-muted-foreground">Amostra:</span>
                <span className="font-semibold text-foreground">{sample.accession_number}</span>
              </div>
              <div className="flex justify-between items-center border-b pb-2">
                <span className="text-muted-foreground">Dispositivo:</span>
                <span className="font-semibold text-foreground">{sample.commercial_name}</span>
              </div>
              <div className="flex justify-between items-center border-b pb-2">
                <span className="text-muted-foreground">Conclusão Pericial:</span>
                <span className="font-bold text-foreground">{issuedReport.conclusion}</span>
              </div>
              <div className="space-y-1">
                <span className="text-muted-foreground font-semibold">Hash Criptográfico SHA-256:</span>
                <div className="font-mono text-[11px] bg-background p-2 rounded border break-all select-all text-primary">
                  {issuedReport.sha256_hash}
                </div>
              </div>
              <div className="space-y-1">
                <span className="text-muted-foreground font-semibold">Token de Autenticidade Pública (QR Code):</span>
                <div className="font-mono text-xs bg-background p-2 rounded border break-all text-foreground">
                  /api/v1/reports/verify/{issuedReport.auth_token}
                </div>
              </div>
            </div>

            <DialogFooter>
              <Button onClick={() => onOpenChange(false)}>Fechar</Button>
            </DialogFooter>
          </div>
        ) : (
          <form onSubmit={handleGenerate} className="space-y-4">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-primary" />
                Emissão de Laudo Pericial Oficial Consolidado
              </DialogTitle>
              <DialogDescription>
                Consolidação dos ensaios aprovados para a amostra{" "}
                <strong className="text-foreground">{sample.accession_number}</strong> ({sample.commercial_name}).
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-2">
              <div className="space-y-2">
                <Label>Título do Laudo Oficial</Label>
                <Input
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label>Ensaios Homologados para Inclusão</Label>
                {!approvedTests.length ? (
                  <div className="p-4 border rounded-md text-xs text-amber-800 bg-amber-50">
                    Nenhum ensaio aprovado na revisão por pares para esta amostra. Conclua e homologue os ensaios primeiro.
                  </div>
                ) : (
                  <div className="border rounded-md divide-y max-h-48 overflow-y-auto">
                    {approvedTests.map((t) => (
                      <label
                        key={t.id}
                        className="flex items-center gap-3 p-3 text-xs hover:bg-muted/10 cursor-pointer"
                      >
                        <input
                          type="checkbox"
                          checked={selectedTestIds.includes(t.id)}
                          onChange={() => toggleTest(t.id)}
                          className="rounded border-gray-300"
                        />
                        <div className="flex-1">
                          <p className="font-semibold text-foreground">{t.name}</p>
                          <p className="text-muted-foreground">
                            Resultado: {t.result_value ?? "—"} {t.unit} · {t.outcome}
                          </p>
                        </div>
                      </label>
                    ))}
                  </div>
                )}
              </div>

              <div className="space-y-2">
                <Label>Conclusão Pericial do Laudo</Label>
                <Select
                  value={conclusion}
                  onValueChange={(val) => setConclusion(val as TestOutcome)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="APROVADO">APROVADO — Atende integralmente aos requisitos regulatórios</SelectItem>
                    <SelectItem value="REPROVADO">REPROVADO — Não conforme com as especificações normativas</SelectItem>
                    <SelectItem value="INCONCLUSIVO">INCONCLUSIVO — Amostra insuficiente ou parâmetros indeterminados</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Sumário Executivo e Fundamentação Técnica</Label>
                <Textarea
                  value={summary}
                  onChange={(e) => setReportSummary(e.target.value)}
                  placeholder="Parecer técnico conclusivo consolidando as evidências metrológicas de bancada..."
                  rows={4}
                />
              </div>
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                Cancelar
              </Button>
              <Button type="submit" disabled={submitting || !selectedTestIds.length}>
                {submitting ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                Assinar e Emitir Laudo Oficial
              </Button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}
