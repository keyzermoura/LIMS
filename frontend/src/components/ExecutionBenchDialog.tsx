import * as React from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Clock,
  Droplets,
  FileCheck2,
  FlaskConical,
  Gauge,
  Loader2,
  Pause,
  Play,
  Plus,
  RefreshCw,
  Sigma,
  Thermometer,
  Trash2,
  Wrench,
  XCircle,
} from "lucide-react";

import { StatusBadge } from "@/components/StatusBadge";
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
import { equipmentApi, executionsApi, ApiError } from "@/lib/api";
import type {
  LaboratoryEquipment,
  LabTest,
  TestExecution,
  TestOutcome,
} from "@/lib/types";
import { OUTCOME_LABELS, formatDateTime } from "@/lib/utils";

interface ReadingPoint {
  id: string;
  name: string;
  value: string;
}

interface ExecutionBenchDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  test: LabTest;
  sampleCode?: string;
  onImportToReport?: (execution: TestExecution) => void;
}

export function ExecutionBenchDialog({
  open,
  onOpenChange,
  test,
  sampleCode,
  onImportToReport,
}: ExecutionBenchDialogProps) {
  const { push } = useToast();
  const queryClient = useQueryClient();

  const [activeTab, setActiveTab] = React.useState<"bench" | "history">("bench");

  // Iniciar nova execução
  const [startEquipmentId, setStartEquipmentId] = React.useState<string>(test.equipment_id ?? "");
  const [startTemp, setStartTemp] = React.useState<string>("23.0");
  const [startHumidity, setStartHumidity] = React.useState<string>("55.0");
  const [startPressure, setStartPressure] = React.useState<string>("1013.2");
  const [startNotes, setStartNotes] = React.useState<string>("");
  const [isStarting, setIsStarting] = React.useState(false);

  // Execução ativa
  const [readings, setReadings] = React.useState<ReadingPoint[]>([
    { id: "1", name: "Leitura 1", value: "" },
    { id: "2", name: "Leitura 2", value: "" },
    { id: "3", name: "Leitura 3", value: "" },
  ]);
  const [execTemp, setExecTemp] = React.useState<string>("");
  const [execHumidity, setExecHumidity] = React.useState<string>("");
  const [execPressure, setExecPressure] = React.useState<string>("");
  const [execResultVal, setExecResultVal] = React.useState<string>("");
  const [execResultText, setExecResultText] = React.useState<string>("");
  const [execOutcome, setExecOutcome] = React.useState<TestOutcome | "">("");
  const [execNotes, setExecNotes] = React.useState<string>("");
  const [isSavingReadings, setIsSavingReadings] = React.useState(false);
  const [isCompleting, setIsCompleting] = React.useState(false);

  // Interrupção
  const [interruptModalOpen, setInterruptModalOpen] = React.useState(false);
  const [interruptReason, setInterruptReason] = React.useState("");
  const [isInterrupting, setIsInterrupting] = React.useState(false);

  // Queries
  const executionsQuery = useQuery({
    queryKey: ["executions", test.id],
    queryFn: () => executionsApi.list(test.id),
    enabled: open,
  });

  const equipmentQuery = useQuery({
    queryKey: ["equipment", "all"],
    queryFn: () => equipmentApi.list(),
    enabled: open,
  });

  const executions = executionsQuery.data ?? [];
  const equipmentList = equipmentQuery.data ?? [];

  const activeExecution = executions.find((e) => e.status === "EM_ANDAMENTO") ?? null;
  const completedExecutions = executions.filter((e) => e.status !== "EM_ANDAMENTO");

  // Sincronizar form da execução ativa quando ela mudar
  React.useEffect(() => {
    if (activeExecution) {
      setExecTemp(activeExecution.temperature_celsius !== null ? String(activeExecution.temperature_celsius) : "");
      setExecHumidity(activeExecution.humidity_percent !== null ? String(activeExecution.humidity_percent) : "");
      setExecPressure(activeExecution.pressure_hpa !== null ? String(activeExecution.pressure_hpa) : "");
      setExecResultVal(activeExecution.result_value !== null ? String(activeExecution.result_value) : "");
      setExecResultText(activeExecution.result_text ?? "");
      setExecOutcome(activeExecution.outcome ?? "");
      setExecNotes(activeExecution.notes ?? "");

      // Mapear raw_data para leitura de pontos se existir
      if (activeExecution.raw_data && Object.keys(activeExecution.raw_data).length > 0) {
        const rawPoints = Object.entries(activeExecution.raw_data).map(([k, v], idx) => ({
          id: String(idx + 1),
          name: k,
          value: typeof v === "object" ? JSON.stringify(v) : String(v ?? ""),
        }));
        setReadings(rawPoints);
      }
    }
  }, [activeExecution?.id]);

  // Checagem metrológica do equipamento selecionado
  const selectedEquipment = React.useMemo(() => {
    return equipmentList.find((e) => e.id === startEquipmentId) ?? null;
  }, [equipmentList, startEquipmentId]);

  const isEquipmentExpired = selectedEquipment?.calibration_status === "VENCIDO";
  const isEquipmentInMaintenance = selectedEquipment?.calibration_status === "EM_MANUTENCAO";

  // Calcular média automática das leituras numéricas
  const calculatedAverage = React.useMemo(() => {
    const validNumbers = readings
      .map((r) => Number(r.value.replace(",", ".")))
      .filter((n) => Number.isFinite(n) && !Number.isNaN(n));
    if (validNumbers.length === 0) return null;
    const sum = validNumbers.reduce((a, b) => a + b, 0);
    return sum / validNumbers.length;
  }, [readings]);

  function handleAddReadingPoint() {
    setReadings((prev) => [
      ...prev,
      { id: String(Date.now()), name: `Leitura ${prev.length + 1}`, value: "" },
    ]);
  }

  function handleRemoveReadingPoint(id: string) {
    setReadings((prev) => prev.filter((r) => r.id !== id));
  }

  function handleReadingChange(id: string, field: "name" | "value", text: string) {
    setReadings((prev) =>
      prev.map((r) => (r.id === id ? { ...r, [field]: text } : r))
    );
  }

  function handleApplyAverage() {
    if (calculatedAverage !== null) {
      setExecResultVal(calculatedAverage.toFixed(4));
    }
  }

  async function handleStartExecution(e: React.FormEvent) {
    e.preventDefault();
    if (!startEquipmentId) {
      push({
        title: "Instrumento obrigatório",
        description: "Selecione o instrumento calibrado para rastreabilidade ALCOA+.",
        variant: "warning",
      });
      return;
    }

    if (isEquipmentExpired) {
      push({
        title: "Bloqueio Metrológico (ISO/IEC 17025)",
        description: "O equipamento selecionado está com a calibração vencida. Selecione um instrumento apto.",
        variant: "destructive",
      });
      return;
    }

    setIsStarting(true);
    try {
      await executionsApi.start(test.id, {
        equipment_id: startEquipmentId,
        temperature_celsius: startTemp ? Number(startTemp) : null,
        humidity_percent: startHumidity ? Number(startHumidity) : null,
        pressure_hpa: startPressure ? Number(startPressure) : null,
        notes: startNotes.trim() || null,
      });

      push({
        title: "Execução iniciada na bancada",
        description: "Instrumento vinculado e condições ambientais registradas.",
        variant: "success",
      });

      queryClient.invalidateQueries({ queryKey: ["executions", test.id] });
    } catch (err) {
      push({
        title: "Falha ao iniciar execução",
        description: err instanceof ApiError ? err.message : "Erro de comunicação.",
        variant: "destructive",
      });
    } finally {
      setIsStarting(false);
    }
  }

  async function handleSaveReadings() {
    if (!activeExecution) return;

    setIsSavingReadings(true);
    try {
      const rawData: Record<string, unknown> = {};
      readings.forEach((r) => {
        if (r.name.trim()) {
          const num = Number(r.value.replace(",", "."));
          rawData[r.name.trim()] = Number.isFinite(num) && r.value.trim() !== "" ? num : r.value;
        }
      });

      await executionsApi.recordReadings(activeExecution.id, {
        temperature_celsius: execTemp ? Number(execTemp) : null,
        humidity_percent: execHumidity ? Number(execHumidity) : null,
        pressure_hpa: execPressure ? Number(execPressure) : null,
        raw_data: rawData,
        result_value: execResultVal ? Number(execResultVal.replace(",", ".")) : null,
        result_text: execResultText.trim() || null,
        notes: execNotes.trim() || null,
      });

      push({
        title: "Leituras salvas",
        description: "Dados intermediários sincronizados com a trilha de auditoria.",
        variant: "success",
      });

      queryClient.invalidateQueries({ queryKey: ["executions", test.id] });
    } catch (err) {
      push({
        title: "Erro ao salvar leituras",
        description: err instanceof ApiError ? err.message : "Erro na operação.",
        variant: "destructive",
      });
    } finally {
      setIsSavingReadings(false);
    }
  }

  async function handleCompleteExecution() {
    if (!activeExecution) return;

    if (!execOutcome) {
      push({
        title: "Desfecho obrigatório",
        description: "Indique o desfecho da execução (APROVADO, REPROVADO ou INCONCLUSIVO).",
        variant: "warning",
      });
      return;
    }

    setIsCompleting(true);
    try {
      const rawData: Record<string, unknown> = {};
      readings.forEach((r) => {
        if (r.name.trim()) {
          const num = Number(r.value.replace(",", "."));
          rawData[r.name.trim()] = Number.isFinite(num) && r.value.trim() !== "" ? num : r.value;
        }
      });

      const updated = await executionsApi.complete(activeExecution.id, {
        raw_data: rawData,
        result_value: execResultVal ? Number(execResultVal.replace(",", ".")) : null,
        result_text: execResultText.trim() || null,
        outcome: execOutcome,
        temperature_celsius: execTemp ? Number(execTemp) : null,
        humidity_percent: execHumidity ? Number(execHumidity) : null,
        pressure_hpa: execPressure ? Number(execPressure) : null,
        notes: execNotes.trim() || null,
      });

      push({
        title: "Tentativa de ensaio concluída",
        description: `Execução #${updated.execution_number} finalizada com status ${updated.outcome}.`,
        variant: "success",
      });

      queryClient.invalidateQueries({ queryKey: ["executions", test.id] });
      queryClient.invalidateQueries({ queryKey: ["tests"] });
    } catch (err) {
      push({
        title: "Falha ao concluir execução",
        description: err instanceof ApiError ? err.message : "Erro ao finalizar.",
        variant: "destructive",
      });
    } finally {
      setIsCompleting(false);
    }
  }

  async function handleConfirmInterrupt() {
    if (!activeExecution || !interruptReason.trim()) {
      push({
        title: "Motivo obrigatório",
        description: "Descreva a justificativa técnica para interrupção do ensaio (ALCOA+).",
        variant: "warning",
      });
      return;
    }

    setIsInterrupting(true);
    try {
      await executionsApi.interrupt(activeExecution.id, {
        reason: interruptReason.trim(),
      });

      push({
        title: "Tentativa interrompida",
        description: "Motivo registrado na auditoria. Você pode iniciar nova tentativa.",
        variant: "default",
      });

      setInterruptModalOpen(false);
      setInterruptReason("");
      queryClient.invalidateQueries({ queryKey: ["executions", test.id] });
    } catch (err) {
      push({
        title: "Erro ao interromper",
        description: err instanceof ApiError ? err.message : "Erro na operação.",
        variant: "destructive",
      });
    } finally {
      setIsInterrupting(false);
    }
  }

  function handleImport(execution: TestExecution) {
    if (onImportToReport) {
      onImportToReport(execution);
      push({
        title: "Dados carregados para formalização",
        description: `Resultado e condições da Execução #${execution.execution_number} preenchidos no laudo.`,
        variant: "success",
      });
      onOpenChange(false);
    }
  }

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader className="border-b border-border pb-4">
            <div className="flex items-center justify-between gap-4">
              <div>
                <div className="flex items-center gap-2">
                  <FlaskConical className="h-5 w-5 text-primary" />
                  <DialogTitle className="text-lg">Bancada Analítica de Execução</DialogTitle>
                </div>
                <DialogDescription className="mt-1 text-xs">
                  {sampleCode ? <span className="font-semibold text-foreground">{sampleCode} · </span> : null}
                  {test.name} {test.method ? `(${test.method})` : ""}
                </DialogDescription>
              </div>
              <div className="flex items-center gap-2">
                <span className="rounded border border-border bg-muted/40 px-2 py-1 text-xs font-mono">
                  Limites: {test.lower_limit !== null ? Number(test.lower_limit) : "—"} a{" "}
                  {test.upper_limit !== null ? Number(test.upper_limit) : "—"} {test.unit}
                </span>
              </div>
            </div>

            {/* Abas */}
            <div className="mt-4 flex gap-2 border-b border-border/50 pb-1">
              <Button
                variant={activeTab === "bench" ? "default" : "ghost"}
                size="sm"
                onClick={() => setActiveTab("bench")}
              >
                <Play className="mr-1.5 h-3.5 w-3.5" />
                Bancada Ativa
                {activeExecution ? (
                  <span className="ml-1.5 rounded-full bg-emerald-500/20 px-1.5 py-0.2 text-[10px] text-emerald-700">
                    Em execução
                  </span>
                ) : null}
              </Button>
              <Button
                variant={activeTab === "history" ? "default" : "ghost"}
                size="sm"
                onClick={() => setActiveTab("history")}
              >
                <Clock className="mr-1.5 h-3.5 w-3.5" />
                Histórico de Tentativas ({executions.length})
              </Button>
            </div>
          </DialogHeader>

          {activeTab === "bench" ? (
            <div className="py-2 space-y-6">
              {activeExecution ? (
                /* PAINEL DA EXECUÇÃO ATIVA */
                <div className="space-y-5 rounded-lg border border-primary/30 bg-primary/[0.02] p-4 shadow-sm">
                  <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border pb-3">
                    <div className="flex items-center gap-2">
                      <span className="flex h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse" />
                      <span className="font-semibold text-sm">
                        {activeExecution.attempt_label} (Execução #{activeExecution.execution_number})
                      </span>
                      <span className="rounded bg-primary/10 px-2 py-0.5 text-xs text-primary font-medium">
                        EM ANDAMENTO
                      </span>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      Iniciado em {formatDateTime(activeExecution.started_at)}
                    </div>
                  </div>

                  {/* Condições Ambientais da Execução */}
                  <div>
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2 flex items-center gap-1.5">
                      <Thermometer className="h-3.5 w-3.5 text-primary" />
                      Condições Ambientais na Bancada (ALCOA+)
                    </h4>
                    <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                      <div>
                        <Label className="text-xs flex items-center gap-1">
                          <Thermometer className="h-3 w-3" /> Temperatura (°C)
                        </Label>
                        <Input
                          type="number"
                          step="0.1"
                          value={execTemp}
                          onChange={(e) => setExecTemp(e.target.value)}
                          placeholder="23.0"
                          className="mt-1 h-9 font-mono text-sm"
                        />
                      </div>
                      <div>
                        <Label className="text-xs flex items-center gap-1">
                          <Droplets className="h-3 w-3" /> Umidade Relativa (% UR)
                        </Label>
                        <Input
                          type="number"
                          step="0.1"
                          value={execHumidity}
                          onChange={(e) => setExecHumidity(e.target.value)}
                          placeholder="55.0"
                          className="mt-1 h-9 font-mono text-sm"
                        />
                      </div>
                      <div>
                        <Label className="text-xs flex items-center gap-1">
                          <Gauge className="h-3 w-3" /> Pressão (hPa)
                        </Label>
                        <Input
                          type="number"
                          step="0.1"
                          value={execPressure}
                          onChange={(e) => setExecPressure(e.target.value)}
                          placeholder="1013.2"
                          className="mt-1 h-9 font-mono text-sm"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Pontos de Leitura e Dados Brutos */}
                  <div className="border-t border-border pt-4">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                        <Sigma className="h-3.5 w-3.5 text-primary" />
                        Leituras Brutas do Instrumento ({test.unit})
                      </h4>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={handleAddReadingPoint}
                        className="h-7 text-xs"
                      >
                        <Plus className="mr-1 h-3 w-3" /> Adicionar Ponto
                      </Button>
                    </div>

                    <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                      {readings.map((reading) => (
                        <div key={reading.id} className="flex items-center gap-2">
                          <Input
                            value={reading.name}
                            onChange={(e) => handleReadingChange(reading.id, "name", e.target.value)}
                            placeholder="Identificador do ponto"
                            className="h-8 text-xs max-w-[180px]"
                          />
                          <Input
                            value={reading.value}
                            onChange={(e) => handleReadingChange(reading.id, "value", e.target.value)}
                            placeholder={`Valor medido em ${test.unit}`}
                            className="h-8 text-xs font-mono"
                          />
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={() => handleRemoveReadingPoint(reading.id)}
                            className="h-8 w-8 p-0 text-muted-foreground hover:text-rose-600"
                            disabled={readings.length <= 1}
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
                        </div>
                      ))}
                    </div>

                    {calculatedAverage !== null ? (
                      <div className="mt-3 flex items-center justify-between rounded-md bg-muted/40 px-3 py-2 text-xs">
                        <span className="text-muted-foreground">
                          Média aritmética dos pontos: <strong className="font-mono text-foreground">{calculatedAverage.toFixed(4)} {test.unit}</strong>
                        </span>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={handleApplyAverage}
                          className="h-6 text-xs text-primary hover:underline"
                        >
                          Usar como Resultado Final
                        </Button>
                      </div>
                    ) : null}
                  </div>

                  {/* Fechamento da Execução */}
                  <div className="border-t border-border pt-4 space-y-3">
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                      Consolidação da Tentativa
                    </h4>
                    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                      <div>
                        <Label className="text-xs">Valor do Resultado ({test.unit})</Label>
                        <Input
                          value={execResultVal}
                          onChange={(e) => setExecResultVal(e.target.value)}
                          placeholder="Ex.: 12.45"
                          className="mt-1 h-9 font-semibold font-mono"
                        />
                      </div>
                      <div>
                        <Label className="text-xs">Desfecho Preliminar *</Label>
                        <Select
                          value={execOutcome}
                          onValueChange={(val) => setExecOutcome(val as TestOutcome)}
                        >
                          <SelectTrigger className="mt-1 h-9 text-xs">
                            <SelectValue placeholder="Selecione desfecho" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="APROVADO">APROVADO</SelectItem>
                            <SelectItem value="REPROVADO">REPROVADO</SelectItem>
                            <SelectItem value="INCONCLUSIVO">INCONCLUSIVO</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>

                    <div>
                      <Label className="text-xs">Observações da Bancada</Label>
                      <Textarea
                        rows={2}
                        value={execNotes}
                        onChange={(e) => setExecNotes(e.target.value)}
                        placeholder="Comportamento do espécime, anomalias visuais ou comentários técnicos..."
                        className="mt-1 text-xs"
                      />
                    </div>
                  </div>

                  {/* Ações da Execução Ativa */}
                  <div className="flex flex-wrap items-center justify-between gap-2 border-t border-border pt-3">
                    <Button
                      type="button"
                      variant="destructive"
                      size="sm"
                      onClick={() => setInterruptModalOpen(true)}
                    >
                      <Pause className="mr-1.5 h-3.5 w-3.5" />
                      Interromper Tentativa
                    </Button>

                    <div className="flex items-center gap-2">
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={handleSaveReadings}
                        disabled={isSavingReadings || isCompleting}
                      >
                        {isSavingReadings ? <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" /> : null}
                        Salvar Leituras
                      </Button>

                      <Button
                        type="button"
                        size="sm"
                        onClick={handleCompleteExecution}
                        disabled={isCompleting || isSavingReadings}
                      >
                        {isCompleting ? <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" /> : <CheckCircle2 className="mr-1.5 h-3.5 w-3.5" />}
                        Concluir Execução
                      </Button>
                    </div>
                  </div>
                </div>
              ) : (
                /* FORMULÁRIO DE INÍCIO DE NOVA EXECUÇÃO */
                <form onSubmit={handleStartExecution} className="space-y-4 rounded-lg border border-border p-4 bg-muted/10">
                  <div>
                    <h3 className="text-sm font-semibold flex items-center gap-2">
                      <Play className="h-4 w-4 text-primary" />
                      Iniciar Nova Tentativa de Execução na Bancada
                    </h3>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      Vincule o instrumento metrológico rastreado e registre as condições ambientais iniciais conforme ISO/IEC 17025.
                    </p>
                  </div>

                  {/* Seleção do Equipamento Metrológico */}
                  <div>
                    <Label className="text-xs flex items-center gap-1.5">
                      <Wrench className="h-3.5 w-3.5 text-primary" />
                      Instrumento Metrológico / Equipamento *
                    </Label>
                    <Select value={startEquipmentId} onValueChange={setStartEquipmentId}>
                      <SelectTrigger className="mt-1 text-xs">
                        <SelectValue placeholder="Selecione o equipamento metrológico" />
                      </SelectTrigger>
                      <SelectContent>
                        {equipmentList.map((eq) => (
                          <SelectItem key={eq.id} value={eq.id}>
                            <div className="flex items-center gap-2">
                              <span className="font-mono font-medium">{eq.code}</span>
                              <span>— {eq.name}</span>
                              <span
                                className={`text-[10px] px-1.5 py-0.5 rounded font-semibold ${
                                  eq.calibration_status === "CALIBRADO"
                                    ? "bg-emerald-100 text-emerald-800"
                                    : eq.calibration_status === "VENCIDO"
                                      ? "bg-rose-100 text-rose-800"
                                      : "bg-amber-100 text-amber-800"
                                }`}
                              >
                                {eq.calibration_status}
                              </span>
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Alerta Metrológico se vencido */}
                  {isEquipmentExpired ? (
                    <div className="rounded-md border border-rose-300 bg-rose-50 p-3 text-xs text-rose-900 flex items-start gap-2">
                      <AlertTriangle className="h-4 w-4 shrink-0 text-rose-600 mt-0.5" />
                      <div>
                        <p className="font-semibold">Bloqueio Metrológico Ativo</p>
                        <p className="text-rose-800/90 mt-0.5">
                          Este instrumento ({selectedEquipment?.code}) está com a calibração vencida. A execução não poderá ser iniciada sem aferição prévia.
                        </p>
                      </div>
                    </div>
                  ) : isEquipmentInMaintenance ? (
                    <div className="rounded-md border border-amber-300 bg-amber-50 p-3 text-xs text-amber-900 flex items-start gap-2">
                      <AlertTriangle className="h-4 w-4 shrink-0 text-amber-600 mt-0.5" />
                      <div>
                        <p className="font-semibold">Instrumento em Manutenção</p>
                        <p className="text-amber-800/90 mt-0.5">
                          Este equipamento está indisponível para ensaios regulatórios no momento.
                        </p>
                      </div>
                    </div>
                  ) : null}

                  {/* Condições Iniciais */}
                  <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                    <div>
                      <Label className="text-xs">Temperatura Inicial (°C)</Label>
                      <Input
                        type="number"
                        step="0.1"
                        value={startTemp}
                        onChange={(e) => setStartTemp(e.target.value)}
                        placeholder="23.0"
                        className="mt-1 h-9 text-xs font-mono"
                      />
                    </div>
                    <div>
                      <Label className="text-xs">Umidade Relativa (% UR)</Label>
                      <Input
                        type="number"
                        step="0.1"
                        value={startHumidity}
                        onChange={(e) => setStartHumidity(e.target.value)}
                        placeholder="55.0"
                        className="mt-1 h-9 text-xs font-mono"
                      />
                    </div>
                    <div>
                      <Label className="text-xs">Pressão Atmosférica (hPa)</Label>
                      <Input
                        type="number"
                        step="0.1"
                        value={startPressure}
                        onChange={(e) => setStartPressure(e.target.value)}
                        placeholder="1013.2"
                        className="mt-1 h-9 text-xs font-mono"
                      />
                    </div>
                  </div>

                  <div>
                    <Label className="text-xs">Observações Iniciais</Label>
                    <Textarea
                      rows={2}
                      value={startNotes}
                      onChange={(e) => setStartNotes(e.target.value)}
                      placeholder="Ex.: Lote preparado conforme procedimento operacional padrão..."
                      className="mt-1 text-xs"
                    />
                  </div>

                  <div className="flex justify-end pt-2">
                    <Button
                      type="submit"
                      disabled={isStarting || isEquipmentExpired || isEquipmentInMaintenance}
                    >
                      {isStarting ? <Loader2 className="mr-1.5 h-4 w-4 animate-spin" /> : <Play className="mr-1.5 h-4 w-4" />}
                      Iniciar Tentativa de Execução
                    </Button>
                  </div>
                </form>
              )}
            </div>
          ) : (
            /* HISTÓRICO DE TENTATIVAS */
            <div className="py-2 space-y-4">
              {executions.length === 0 ? (
                <div className="rounded-lg border border-dashed border-border p-8 text-center text-muted-foreground">
                  <FlaskConical className="mx-auto h-8 w-8 opacity-40 mb-2" />
                  <p className="text-sm font-semibold">Nenhuma execução registrada</p>
                  <p className="text-xs mt-1">Inicie a primeira tentativa na aba Bancada Ativa.</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {executions.map((exec) => (
                    <div
                      key={exec.id}
                      className="rounded-lg border border-border bg-card p-4 transition-all hover:border-primary/40 shadow-sm"
                    >
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-sm">
                              {exec.attempt_label} (Tentativa #{exec.execution_number})
                            </span>
                            <span
                              className={`text-[10px] px-2 py-0.5 rounded font-semibold ${
                                exec.status === "CONCLUIDA"
                                  ? "bg-emerald-100 text-emerald-800"
                                  : exec.status === "EM_ANDAMENTO"
                                    ? "bg-blue-100 text-blue-800"
                                    : exec.status === "INTERROMPIDA"
                                      ? "bg-amber-100 text-amber-800"
                                      : "bg-rose-100 text-rose-800"
                              }`}
                            >
                              {exec.status}
                            </span>
                            {exec.outcome ? (
                              <span
                                className={`text-[10px] px-2 py-0.5 rounded font-bold ${
                                  exec.outcome === "APROVADO"
                                    ? "bg-emerald-600 text-white"
                                    : exec.outcome === "REPROVADO"
                                      ? "bg-rose-600 text-white"
                                      : "bg-amber-600 text-white"
                                }`}
                              >
                                {exec.outcome}
                              </span>
                            ) : null}
                          </div>
                          <p className="text-xs text-muted-foreground mt-1">
                            Executado por {exec.executed_by?.full_name ?? "Técnico"} · Início: {formatDateTime(exec.started_at)}
                            {exec.finished_at ? ` · Fim: ${formatDateTime(exec.finished_at)}` : ""}
                          </p>
                        </div>

                        {/* Botão Importar para o Laudo */}
                        {exec.status === "CONCLUIDA" && onImportToReport ? (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleImport(exec)}
                            className="text-xs"
                          >
                            <FileCheck2 className="mr-1.5 h-3.5 w-3.5 text-primary" />
                            Preencher Laudo
                          </Button>
                        ) : null}
                      </div>

                      {/* Métricas e leituras */}
                      <div className="mt-3 grid grid-cols-2 gap-2 text-xs sm:grid-cols-4 bg-muted/20 p-2.5 rounded">
                        <div>
                          <span className="text-muted-foreground block text-[10px] uppercase">Resultado</span>
                          <span className="font-mono font-semibold text-sm">
                            {exec.result_value !== null ? `${Number(exec.result_value)} ${test.unit}` : "—"}
                          </span>
                        </div>
                        <div>
                          <span className="text-muted-foreground block text-[10px] uppercase">Ambiente</span>
                          <span className="font-mono text-xs">
                            {exec.temperature_celsius ? `${exec.temperature_celsius}°C` : "—"} /{" "}
                            {exec.humidity_percent ? `${exec.humidity_percent}%` : "—"}
                          </span>
                        </div>
                        <div>
                          <span className="text-muted-foreground block text-[10px] uppercase">Pressão</span>
                          <span className="font-mono text-xs">
                            {exec.pressure_hpa ? `${exec.pressure_hpa} hPa` : "—"}
                          </span>
                        </div>
                        <div>
                          <span className="text-muted-foreground block text-[10px] uppercase">Pontos Lidos</span>
                          <span className="font-mono text-xs">
                            {Object.keys(exec.raw_data || {}).length} medições
                          </span>
                        </div>
                      </div>

                      {/* Motivo de interrupção se houver */}
                      {exec.interruption_reason ? (
                        <div className="mt-2.5 rounded border border-amber-200 bg-amber-50/70 p-2 text-xs text-amber-900">
                          <strong>Motivo da interrupção (ALCOA+):</strong> {exec.interruption_reason}
                        </div>
                      ) : null}

                      {/* Observações da execução */}
                      {exec.notes ? (
                        <p className="mt-2 text-xs text-muted-foreground">
                          <strong>Notas:</strong> {exec.notes}
                        </p>
                      ) : null}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          <DialogFooter className="border-t border-border pt-3">
            <Button variant="ghost" size="sm" onClick={() => onOpenChange(false)}>
              Fechar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* MODAL DE CONFIRMAÇÃO DE INTERRUPÇÃO */}
      <Dialog open={interruptModalOpen} onOpenChange={setInterruptModalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <div className="flex items-center gap-2 text-rose-600">
              <AlertTriangle className="h-5 w-5" />
              <DialogTitle className="text-base">Interromper Tentativa de Ensaio</DialogTitle>
            </div>
            <DialogDescription className="text-xs">
              Conforme as diretrizes de integridade de dados (ALCOA+), a tentativa interrompida não será apagada e permanecerá registrada na auditoria.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-3 py-2">
            <div>
              <Label className="text-xs">Motivo Técnico da Interrupção *</Label>
              <Textarea
                rows={3}
                value={interruptReason}
                onChange={(e) => setInterruptReason(e.target.value)}
                placeholder="Ex.: Oscilação brusca de tensão na bancada / falha no posicionamento do transdutor..."
                className="mt-1 text-xs"
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setInterruptModalOpen(false)}
              disabled={isInterrupting}
            >
              Cancelar
            </Button>
            <Button
              variant="destructive"
              size="sm"
              onClick={handleConfirmInterrupt}
              disabled={isInterrupting || !interruptReason.trim()}
            >
              {isInterrupting ? <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" /> : null}
              Confirmar Interrupção
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
