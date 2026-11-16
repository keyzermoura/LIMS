import * as React from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Activity,
  Calculator,
  CheckCircle2,
  FileSignature,
  Loader2,
  Plus,
  Scale,
  ShieldAlert,
  ShieldCheck,
  Sigma,
  Trash2,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
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
import {
  ApiError,
  api,
  equipmentApi,
  methodsApi,
  uncertaintyApi,
} from "@/lib/api";
import type {
  ConformityStatus,
  DecisionRuleType,
  LabTest,
  LaboratoryEquipment,
  Page,
  TestMethod,
  UncertaintyBudget,
  UncertaintyCalculation,
  UncertaintyComponentIn,
  UncertaintyDistribution,
  UncertaintySourceType,
} from "@/lib/types";
import { formatDateTime } from "@/lib/utils";

const RULE_LABELS: Record<DecisionRuleType, string> = {
  SIMPLE_ACCEPTANCE: "Aceitação Simples (w = 0, Risco Compartilhado)",
  GUARD_BAND_CONSERVATIVE: "Faixa de Guarda Conservadora (Binária Estreita)",
  GUARD_BAND_NON_BINARY: "Faixa de Guarda Não-Binária (4 Estados ILAC-G8)",
};

const CONFORMITY_BADGE: Record<
  ConformityStatus,
  { label: string; variant: "success" | "warning" | "destructive" }
> = {
  CONFORME: { label: "Conforme (Pass)", variant: "success" },
  CONFORME_CONDICIONAL: { label: "Conforme Condicional", variant: "warning" },
  NAO_CONFORME_CONDICIONAL: { label: "Não Conforme Condicional", variant: "warning" },
  NAO_CONFORME: { label: "Não Conforme (Fail)", variant: "destructive" },
};

const DISTRIBUTION_LABELS: Record<UncertaintyDistribution, string> = {
  NORMAL: "Normal (k = 2 ou 1)",
  RECTANGULAR: "Retangular (√3)",
  TRIANGULAR: "Triangular (√6)",
  U_SHAPED: "Forma em U (√2)",
};

interface EditableComponent {
  id: string;
  name: string;
  symbol: string;
  source_type: UncertaintySourceType;
  distribution: UncertaintyDistribution;
  half_width: string;
  sensitivity_coefficient: string;
  degrees_of_freedom: string;
}

const DEFAULT_COMPONENTS: EditableComponent[] = [
  {
    id: "cal",
    name: "Certificado de Calibração do Instrumento",
    symbol: "u_cal",
    source_type: "TYPE_B",
    distribution: "NORMAL",
    half_width: "1.20",
    sensitivity_coefficient: "1.0",
    degrees_of_freedom: "50",
  },
  {
    id: "res",
    name: "Resolução do Mostrador Digital",
    symbol: "u_res",
    source_type: "TYPE_B",
    distribution: "RECTANGULAR",
    half_width: "0.05",
    sensitivity_coefficient: "1.0",
    degrees_of_freedom: "",
  },
  {
    id: "drift",
    name: "Deriva Térmica e Estabilidade",
    symbol: "u_drv",
    source_type: "TYPE_B",
    distribution: "RECTANGULAR",
    half_width: "0.40",
    sensitivity_coefficient: "1.0",
    degrees_of_freedom: "",
  },
];

export function UncertaintyPage() {
  const { push } = useToast();
  const queryClient = useQueryClient();

  // Vínculos opcionais com o LIMS
  const [selectedTestId, setSelectedTestId] = React.useState<string>("NONE");
  const [selectedMethodId, setSelectedMethodId] = React.useState<string>("NONE");
  const [selectedEquipmentId, setSelectedEquipmentId] = React.useState<string>("NONE");

  // Parâmetros de medição
  const [unit, setUnit] = React.useState("uA");
  const [measuredValueStr, setMeasuredValueStr] = React.useState("98.50");
  const [readingsStr, setReadingsStr] = React.useState(
    "98.40, 98.55, 98.48, 98.60, 98.47",
  );
  const [lowerLimitStr, setLowerLimitStr] = React.useState("0.00");
  const [upperLimitStr, setUpperLimitStr] = React.useState("100.00");
  const [decisionRule, setDecisionRule] = React.useState<DecisionRuleType>(
    "GUARD_BAND_NON_BINARY",
  );
  const [guardBandMultStr, setGuardBandMultStr] = React.useState("1.000");
  const [confidenceLevelStr, setConfidenceLevelStr] = React.useState("95.45");
  const [notes, setNotes] = React.useState("");

  // Fontes de incerteza
  const [components, setComponents] = React.useState<EditableComponent[]>(
    DEFAULT_COMPONENTS,
  );

  // Resultado simulado
  const [simulation, setSimulation] = React.useState<UncertaintyCalculation | null>(
    null,
  );
  const [isSimulating, setIsSimulating] = React.useState(false);

  // Modal de salvamento com assinatura eletrônica
  const [saveDialogOpen, setSaveDialogOpen] = React.useState(false);
  const [signaturePassword, setSignaturePassword] = React.useState("");
  const [isSaving, setIsSaving] = React.useState(false);

  // Dados auxiliares do LIMS
  const { data: budgets = [], isLoading: loadingBudgets } = useQuery<
    UncertaintyBudget[]
  >({
    queryKey: ["uncertainty-budgets"],
    queryFn: () => uncertaintyApi.listBudgets(),
  });

  const { data: methods = [] } = useQuery<TestMethod[]>({
    queryKey: ["methods"],
    queryFn: () => methodsApi.list(undefined, true),
  });

  const { data: equipmentList = [] } = useQuery<LaboratoryEquipment[]>({
    queryKey: ["equipment"],
    queryFn: () => equipmentApi.list(undefined, true),
  });

  const { data: testsPage } = useQuery<Page<LabTest>>({
    queryKey: ["tests-all-uncertainty"],
    queryFn: () => api.get<Page<LabTest>>("/tests?size=100"),
  });
  const tests = testsPage?.items ?? [];

  function handleSelectTest(testId: string) {
    setSelectedTestId(testId);
    if (testId === "NONE") return;
    const found = tests.find((t) => t.id === testId);
    if (!found) return;
    setUnit(found.unit || "UN");
    if (found.result_value !== null && found.result_value !== undefined) {
      setMeasuredValueStr(String(found.result_value));
    }
    setLowerLimitStr(
      found.lower_limit !== null && found.lower_limit !== undefined
        ? String(found.lower_limit)
        : "",
    );
    setUpperLimitStr(
      found.upper_limit !== null && found.upper_limit !== undefined
        ? String(found.upper_limit)
        : "",
    );
    if (found.method_id) setSelectedMethodId(found.method_id);
    if (found.equipment_id) setSelectedEquipmentId(found.equipment_id);
  }

  function parseReadings(): number[] {
    return readingsStr
      .split(/[\s,;]+/)
      .map((s) => s.trim())
      .filter(Boolean)
      .map((s) => Number(s))
      .filter((n) => Number.isFinite(n));
  }

  function buildComponentPayload(): UncertaintyComponentIn[] {
    return components
      .filter((c) => c.name.trim().length >= 2 && Number.isFinite(Number(c.half_width)))
      .map((c) => ({
        name: c.name.trim(),
        symbol: c.symbol.trim() || null,
        source_type: c.source_type,
        distribution: c.distribution,
        half_width: Math.max(0, Number(c.half_width)),
        sensitivity_coefficient: Math.max(
          0.0001,
          Number(c.sensitivity_coefficient) || 1.0,
        ),
        degrees_of_freedom: c.degrees_of_freedom.trim()
          ? Math.max(1, parseInt(c.degrees_of_freedom, 10))
          : null,
      }));
  }

  async function runSimulation() {
    setIsSimulating(true);
    try {
      const readings = parseReadings();
      const parsedMeasured = measuredValueStr.trim()
        ? Number(measuredValueStr)
        : null;
      const result = await uncertaintyApi.simulate({
        unit: unit.trim() || "UN",
        measured_value:
          parsedMeasured !== null && Number.isFinite(parsedMeasured)
            ? parsedMeasured
            : null,
        repeatability_readings: readings,
        lower_limit:
          lowerLimitStr.trim() && Number.isFinite(Number(lowerLimitStr))
            ? Number(lowerLimitStr)
            : null,
        upper_limit:
          upperLimitStr.trim() && Number.isFinite(Number(upperLimitStr))
            ? Number(upperLimitStr)
            : null,
        components: buildComponentPayload(),
        confidence_level: Number(confidenceLevelStr) || 95.45,
        guard_band_multiplier: Number(guardBandMultStr) || 0,
        decision_rule: decisionRule,
      });
      setSimulation(result);
    } catch (err) {
      push({
        title: "Erro no cálculo de incerteza",
        description:
          err instanceof ApiError ? err.message : "Verifique os valores informados.",
        variant: "destructive",
      });
    } finally {
      setIsSimulating(false);
    }
  }

  async function handleSaveBudget(e: React.FormEvent) {
    e.preventDefault();
    setIsSaving(true);
    try {
      let signatureToken: string | undefined;
      if (signaturePassword.trim()) {
        let entityType = "UncertaintyBudget";
        let entityId = "";
        let action = "CREATE";
        if (selectedTestId !== "NONE") {
          entityType = "LabTest";
          entityId = selectedTestId;
          action = "UPDATE";
        } else if (selectedMethodId !== "NONE") {
          entityType = "TestMethod";
          entityId = selectedMethodId;
          action = "UPDATE";
        } else {
          const me = await api.get<{ id: string }>("/auth/me");
          entityId = me.id;
        }
        const sig = await api.post<{ token: string }>("/auth/sign", {
          password: signaturePassword,
          entity_type: entityType,
          entity_id: entityId,
          action,
          meaning: "VERIFICACAO",
          reason:
            "Registro formal do orçamento de incerteza metrológica GUM e declaração de conformidade ILAC-G8.",
        });
        signatureToken = sig.token;
      }

      const readings = parseReadings();
      const parsedMeasured = measuredValueStr.trim()
        ? Number(measuredValueStr)
        : null;

      await uncertaintyApi.createBudget(
        {
          unit: unit.trim() || "UN",
          measured_value:
            parsedMeasured !== null && Number.isFinite(parsedMeasured)
              ? parsedMeasured
              : null,
          repeatability_readings: readings,
          lower_limit:
            lowerLimitStr.trim() && Number.isFinite(Number(lowerLimitStr))
              ? Number(lowerLimitStr)
              : null,
          upper_limit:
            upperLimitStr.trim() && Number.isFinite(Number(upperLimitStr))
              ? Number(upperLimitStr)
              : null,
          components: buildComponentPayload(),
          confidence_level: Number(confidenceLevelStr) || 95.45,
          guard_band_multiplier: Number(guardBandMultStr) || 0,
          decision_rule: decisionRule,
          lab_test_id: selectedTestId !== "NONE" ? selectedTestId : null,
          method_id: selectedMethodId !== "NONE" ? selectedMethodId : null,
          equipment_id: selectedEquipmentId !== "NONE" ? selectedEquipmentId : null,
          notes: notes.trim() || null,
        },
        signatureToken,
      );

      push({
        title: "Orçamento GUM registrado",
        description: "Incerteza metrológica salva e vinculada à trilha de auditoria.",
      });
      setSaveDialogOpen(false);
      setSignaturePassword("");
      queryClient.invalidateQueries({ queryKey: ["uncertainty-budgets"] });
    } catch (err) {
      push({
        title: "Falha ao registrar orçamento",
        description: err instanceof ApiError ? err.message : "Erro ao salvar.",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  }

  function addComponent() {
    setComponents((prev) => [
      ...prev,
      {
        id: `comp-${Date.now()}`,
        name: "Nova Fonte de Incerteza",
        symbol: `u_${prev.length + 1}`,
        source_type: "TYPE_B",
        distribution: "RECTANGULAR",
        half_width: "0.10",
        sensitivity_coefficient: "1.0",
        degrees_of_freedom: "",
      },
    ]);
  }

  function updateComponent(
    id: string,
    field: keyof EditableComponent,
    value: string,
  ) {
    setComponents((prev) =>
      prev.map((c) => (c.id === id ? { ...c, [field]: value } : c)),
    );
  }

  function removeComponent(id: string) {
    setComponents((prev) => prev.filter((c) => c.id !== id));
  }

  // Estatísticas dos orçamentos gravados
  const totalBudgets = budgets.length;
  const totalConforme = budgets.filter(
    (b) => b.conformity_status === "CONFORME",
  ).length;
  const totalGuardZone = budgets.filter(
    (b) =>
      b.conformity_status === "CONFORME_CONDICIONAL" ||
      b.conformity_status === "NAO_CONFORME_CONDICIONAL",
  ).length;

  return (
    <div className="space-y-6">
      {/* Cabeçalho e KPIs */}
      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardContent className="flex items-center gap-4 pt-6">
            <span className="flex h-11 w-11 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Sigma className="h-5 w-5" />
            </span>
            <div>
              <p className="text-xs font-medium text-muted-foreground">
                Orçamentos GUM Registrados
              </p>
              <p className="text-2xl font-bold tabular-nums">{totalBudgets}</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-4 pt-6">
            <span className="flex h-11 w-11 items-center justify-center rounded-lg bg-emerald-50 text-emerald-700">
              <ShieldCheck className="h-5 w-5" />
            </span>
            <div>
              <p className="text-xs font-medium text-muted-foreground">
                Conformes (Fora de Risco)
              </p>
              <p className="text-2xl font-bold tabular-nums text-emerald-700">
                {totalConforme}
              </p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-4 pt-6">
            <span className="flex h-11 w-11 items-center justify-center rounded-lg bg-amber-50 text-amber-700">
              <ShieldAlert className="h-5 w-5" />
            </span>
            <div>
              <p className="text-xs font-medium text-muted-foreground">
                Em Zona de Guarda ILAC-G8
              </p>
              <p className="text-2xl font-bold tabular-nums text-amber-700">
                {totalGuardZone}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Área principal: Simulador & Configurador GUM */}
      <div className="grid gap-6 xl:grid-cols-12">
        <Card className="xl:col-span-7">
          <CardHeader className="border-b border-border pb-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Calculator className="h-4 w-4 text-primary" />
                  Motor de Incerteza GUM (JCGM 100:2008) & Faixa de Guarda ILAC-G8
                </CardTitle>
                <CardDescription className="mt-1">
                  Combine repetibilidade experimental (Tipo A) e fontes de calibração/resolução (Tipo B).
                </CardDescription>
              </div>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={runSimulation}
                  disabled={isSimulating}
                >
                  {isSimulating ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Activity className="mr-2 h-4 w-4" />
                  )}
                  Calcular GUM
                </Button>
                <Button
                  type="button"
                  onClick={() => setSaveDialogOpen(true)}
                  disabled={isSimulating}
                >
                  <FileSignature className="mr-2 h-4 w-4" />
                  Registrar & Assinar
                </Button>
              </div>
            </div>
          </CardHeader>

          <CardContent className="space-y-5 pt-5">
            {/* Vínculo opcional com ensaio */}
            <div className="grid gap-4 sm:grid-cols-3">
              <div className="space-y-1.5">
                <Label>Ensaio Vinculado (Opcional)</Label>
                <Select value={selectedTestId} onValueChange={handleSelectTest}>
                  <SelectTrigger>
                    <SelectValue placeholder="Selecione um ensaio" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="NONE">Simulação avulsa</SelectItem>
                    {tests.map((t) => (
                      <SelectItem key={t.id} value={t.id}>
                        {t.name} ({t.unit})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-1.5">
                <Label>Método Analítico</Label>
                <Select value={selectedMethodId} onValueChange={setSelectedMethodId}>
                  <SelectTrigger>
                    <SelectValue placeholder="Método" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="NONE">Nenhum</SelectItem>
                    {methods.map((m) => (
                      <SelectItem key={m.id} value={m.id}>
                        {m.code} — {m.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-1.5">
                <Label>Equipamento Principal</Label>
                <Select
                  value={selectedEquipmentId}
                  onValueChange={setSelectedEquipmentId}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Instrumento" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="NONE">Nenhum</SelectItem>
                    {equipmentList.map((eq) => (
                      <SelectItem key={eq.id} value={eq.id}>
                        {eq.code} — {eq.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Grandezas e Limites */}
            <div className="grid gap-4 sm:grid-cols-4">
              <div className="space-y-1.5">
                <Label>Valor Medido (y)</Label>
                <Input
                  type="number"
                  step="any"
                  value={measuredValueStr}
                  onChange={(e) => setMeasuredValueStr(e.target.value)}
                  placeholder="Ex: 98.50"
                />
              </div>
              <div className="space-y-1.5">
                <Label>Unidade</Label>
                <Input
                  value={unit}
                  onChange={(e) => setUnit(e.target.value)}
                  placeholder="uA, mV, g..."
                />
              </div>
              <div className="space-y-1.5">
                <Label>Limite Inferior (LSL)</Label>
                <Input
                  type="number"
                  step="any"
                  value={lowerLimitStr}
                  onChange={(e) => setLowerLimitStr(e.target.value)}
                  placeholder="Opcional"
                />
              </div>
              <div className="space-y-1.5">
                <Label>Limite Superior (USL)</Label>
                <Input
                  type="number"
                  step="any"
                  value={upperLimitStr}
                  onChange={(e) => setUpperLimitStr(e.target.value)}
                  placeholder="Opcional"
                />
              </div>
            </div>

            {/* Leituras de Repetibilidade Tipo A */}
            <div className="space-y-1.5">
              <Label>
                Leituras Experimentais de Repetibilidade — Tipo A (separadas por vírgula)
              </Label>
              <Input
                value={readingsStr}
                onChange={(e) => setReadingsStr(e.target.value)}
                placeholder="Ex: 98.40, 98.55, 98.48, 98.60, 98.47"
              />
            </div>

            {/* Regra de Decisão ILAC-G8 */}
            <div className="grid gap-4 sm:grid-cols-3">
              <div className="space-y-1.5 sm:col-span-2">
                <Label>Regra de Decisão Metrológica (ILAC-G8:09/2019)</Label>
                <Select
                  value={decisionRule}
                  onValueChange={(v) => setDecisionRule(v as DecisionRuleType)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(RULE_LABELS).map(([key, label]) => (
                      <SelectItem key={key} value={key}>
                        {label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div className="space-y-1.5">
                  <Label>Fator Guarda (w/U)</Label>
                  <Input
                    type="number"
                    step="0.1"
                    min="0"
                    value={guardBandMultStr}
                    onChange={(e) => setGuardBandMultStr(e.target.value)}
                  />
                </div>
                <div className="space-y-1.5">
                  <Label>Confiança (%)</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={confidenceLevelStr}
                    onChange={(e) => setConfidenceLevelStr(e.target.value)}
                  />
                </div>
              </div>
            </div>

            {/* Componentes de Incerteza */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label className="text-sm font-semibold">
                  Fontes de Incerteza Tipo B / Adicionais
                </Label>
                <Button type="button" size="sm" variant="outline" onClick={addComponent}>
                  <Plus className="mr-1.5 h-3.5 w-3.5" />
                  Adicionar Fonte
                </Button>
              </div>

              <div className="space-y-2.5">
                {components.map((comp) => (
                  <div
                    key={comp.id}
                    className="grid items-end gap-2 rounded-lg border border-border bg-muted/20 p-3 sm:grid-cols-12"
                  >
                    <div className="space-y-1 sm:col-span-4">
                      <Label className="text-[11px]">Descrição da Fonte</Label>
                      <Input
                        value={comp.name}
                        onChange={(e) => updateComponent(comp.id, "name", e.target.value)}
                      />
                    </div>
                    <div className="space-y-1 sm:col-span-3">
                      <Label className="text-[11px]">Distribuição</Label>
                      <Select
                        value={comp.distribution}
                        onValueChange={(v) =>
                          updateComponent(comp.id, "distribution", v)
                        }
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {Object.entries(DISTRIBUTION_LABELS).map(([k, lbl]) => (
                            <SelectItem key={k} value={k}>
                              {lbl}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-1 sm:col-span-2">
                      <Label className="text-[11px]">Semi-amplit. (a)</Label>
                      <Input
                        type="number"
                        step="any"
                        min="0"
                        value={comp.half_width}
                        onChange={(e) =>
                          updateComponent(comp.id, "half_width", e.target.value)
                        }
                      />
                    </div>
                    <div className="space-y-1 sm:col-span-2">
                      <Label className="text-[11px]">GL (v_i)</Label>
                      <Input
                        type="number"
                        min="1"
                        placeholder="∞"
                        value={comp.degrees_of_freedom}
                        onChange={(e) =>
                          updateComponent(
                            comp.id,
                            "degrees_of_freedom",
                            e.target.value,
                          )
                        }
                      />
                    </div>
                    <div className="flex justify-end sm:col-span-1">
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        onClick={() => removeComponent(comp.id)}
                        title="Remover fonte"
                      >
                        <Trash2 className="h-4 w-4 text-muted-foreground hover:text-destructive" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Painel de Resultados GUM & Parecer ILAC-G8 */}
        <Card className="xl:col-span-5">
          <CardHeader className="border-b border-border pb-4">
            <CardTitle className="flex items-center gap-2 text-base">
              <Scale className="h-4 w-4 text-primary" />
              Resultado Consolidado & Declaração ISO 17025 §7.8.6
            </CardTitle>
            <CardDescription>
              Parâmetros calculados pelo motor metrológico em tempo real.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-5 pt-5">
            {!simulation ? (
              <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border py-16 text-center">
                <Sigma className="h-9 w-9 text-muted-foreground/40" />
                <p className="mt-3 text-sm font-medium">
                  Pronto para simular a incerteza expandida
                </p>
                <p className="mt-1 max-w-xs text-xs text-muted-foreground">
                  Clique em &ldquo;Calcular GUM&rdquo; para gerar o balanço de incertezas e avaliar a zona de guarda ILAC-G8.
                </p>
              </div>
            ) : (
              <>
                <div className="rounded-lg border border-border bg-muted/30 p-4">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                      Expressão da Medição
                    </span>
                    <Badge
                      variant={
                        CONFORMITY_BADGE[simulation.conformity_status].variant
                      }
                    >
                      {CONFORMITY_BADGE[simulation.conformity_status].label}
                    </Badge>
                  </div>
                  <p className="mt-2 font-mono text-lg font-bold text-foreground">
                    {simulation.formatted_result}
                  </p>
                  <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
                    {simulation.conformity_statement}
                  </p>
                </div>

                {/* Grade de Indicadores Técnicos */}
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div className="rounded-md border border-border p-3">
                    <span className="text-muted-foreground">
                      Incerteza Combinada (u_c)
                    </span>
                    <p className="mt-1 font-mono text-sm font-semibold">
                      {Number(simulation.combined_uncertainty).toFixed(4)}{" "}
                      {simulation.unit}
                    </p>
                  </div>
                  <div className="rounded-md border border-border p-3">
                    <span className="text-muted-foreground">
                      Incerteza Expandida (U)
                    </span>
                    <p className="mt-1 font-mono text-sm font-semibold text-primary">
                      ± {Number(simulation.expanded_uncertainty).toFixed(4)}{" "}
                      {simulation.unit}
                    </p>
                  </div>
                  <div className="rounded-md border border-border p-3">
                    <span className="text-muted-foreground">
                      Fator k / GL Efetivos (ν_eff)
                    </span>
                    <p className="mt-1 font-mono text-sm font-semibold">
                      k = {Number(simulation.coverage_factor).toFixed(3)} · ν ={" "}
                      {simulation.effective_df ?? "∞"}
                    </p>
                  </div>
                  <div className="rounded-md border border-border p-3">
                    <span className="text-muted-foreground">
                      Faixa de Guarda (w)
                    </span>
                    <p className="mt-1 font-mono text-sm font-semibold">
                      {Number(simulation.guard_band_width).toFixed(4)}{" "}
                      {simulation.unit}
                    </p>
                  </div>
                </div>

                {/* Faixa de Aceitação Guard-Banded */}
                {(simulation.lower_acceptance_limit !== null ||
                  simulation.upper_acceptance_limit !== null) && (
                  <div className="rounded-md border border-border bg-background p-3 text-xs">
                    <p className="font-semibold text-foreground">
                      Intervalo de Aceitação Efetivo (com Guarda ILAC-G8):
                    </p>
                    <p className="mt-1 font-mono text-muted-foreground">
                      [
                      {simulation.lower_acceptance_limit !== null
                        ? Number(simulation.lower_acceptance_limit).toFixed(4)
                        : "-∞"}
                      {" ; "}
                      {simulation.upper_acceptance_limit !== null
                        ? Number(simulation.upper_acceptance_limit).toFixed(4)
                        : "+∞"}
                      ] {simulation.unit}
                    </p>
                  </div>
                )}

                {/* Pareto de Contribuições (%) */}
                <div className="space-y-2.5">
                  <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Contribuição Relativa na Variância Total (%)
                  </p>
                  {simulation.components.map((c, idx) => (
                    <div key={`${c.name}-${idx}`} className="space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <span className="truncate pr-2 font-medium">
                          {c.name} ({c.source_type === "TYPE_A" ? "Tipo A" : "Tipo B"})
                        </span>
                        <span className="font-mono text-muted-foreground">
                          u = {Number(c.standard_uncertainty).toFixed(4)} ·{" "}
                          {Number(c.weight_percent).toFixed(1)}%
                        </span>
                      </div>
                      <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                        <div
                          className="h-full rounded-full bg-primary transition-all"
                          style={{
                            width: `${Math.min(100, Math.max(2, Number(c.weight_percent)))}%`,
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Histórico de Orçamentos Registrados */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            Histórico Auditado de Orçamentos de Incerteza
          </CardTitle>
          <CardDescription>
            Orçamentos persistidos vinculados aos ensaios e incorporados automaticamente nos laudos oficiais.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loadingBudgets ? (
            <div className="flex items-center justify-center py-8 text-sm text-muted-foreground">
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Carregando orçamentos...
            </div>
          ) : budgets.length === 0 ? (
            <p className="py-8 text-center text-sm text-muted-foreground">
              Nenhum orçamento de incerteza registrado até o momento.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-left text-xs">
                <thead>
                  <tr className="border-b border-border text-muted-foreground">
                    <th className="py-2.5 pr-4 font-semibold">Resultado ± U</th>
                    <th className="py-2.5 pr-4 font-semibold">Ensaio / Método</th>
                    <th className="py-2.5 pr-4 font-semibold">Regra ILAC-G8</th>
                    <th className="py-2.5 pr-4 font-semibold">Conformidade</th>
                    <th className="py-2.5 pr-4 font-semibold">Responsável</th>
                    <th className="py-2.5 font-semibold">Data</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {budgets.map((b) => (
                    <tr key={b.id} className="hover:bg-muted/30">
                      <td className="py-3 pr-4 font-mono font-semibold">
                        {b.formatted_result}
                      </td>
                      <td className="py-3 pr-4">
                        <div className="font-medium">
                          {b.test_name ?? "Simulação de Referência"}
                        </div>
                        <div className="text-[11px] text-muted-foreground">
                          {b.method_code ?? "Sem método"} ·{" "}
                          {b.equipment_code ?? "Sem instrumento"}
                        </div>
                      </td>
                      <td className="py-3 pr-4 text-muted-foreground">
                        {b.decision_rule} (w = {Number(b.guard_band_width).toFixed(3)})
                      </td>
                      <td className="py-3 pr-4">
                        <Badge variant={CONFORMITY_BADGE[b.conformity_status].variant}>
                          {CONFORMITY_BADGE[b.conformity_status].label}
                        </Badge>
                      </td>
                      <td className="py-3 pr-4">
                        <div className="flex items-center gap-1.5">
                          {b.signature_id ? (
                            <CheckCircle2
                              className="h-3.5 w-3.5 text-emerald-600"
                              aria-label="Assinado eletronicamente"
                            />
                          ) : null}
                          <span>{b.calculated_by_name ?? "Analista"}</span>
                        </div>
                      </td>
                      <td className="py-3 text-muted-foreground">
                        {formatDateTime(b.created_at)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Modal de Confirmação e Assinatura Part 11 */}
      <Dialog open={saveDialogOpen} onOpenChange={setSaveDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Registrar Orçamento de Incerteza GUM</DialogTitle>
            <DialogDescription>
              Salva o balanço completo na base auditada. Informe sua senha para aplicar
              assinatura eletrônica (21 CFR Part 11) ou deixe em branco para registro técnico simples.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSaveBudget} className="space-y-4">
            <div className="space-y-1.5">
              <Label>Notas / Observações Técnicas</Label>
              <Textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Condições ambientais ou referências de certificados utilizados..."
              />
            </div>
            <div className="space-y-1.5">
              <Label>Senha para Assinatura Eletrônica (Opcional)</Label>
              <Input
                type="password"
                value={signaturePassword}
                onChange={(e) => setSignaturePassword(e.target.value)}
                placeholder="Reautenticação Part 11"
              />
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setSaveDialogOpen(false)}
              >
                Cancelar
              </Button>
              <Button type="submit" disabled={isSaving}>
                {isSaving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                Confirmar Registro
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
