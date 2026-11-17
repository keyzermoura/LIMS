import * as React from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertTriangle,
  Beaker,
  Calendar,
  CheckCircle2,
  Clock,
  FileCheck,
  Filter,
  Flame,
  Layers,
  Loader2,
  Plus,
  RefreshCw,
  Search,
  ShieldAlert,
  Tag,
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
import { reagentsApi, ApiError } from "@/lib/api";
import type {
  Reagent,
  ReagentBatch,
  ReagentBatchCreatePayload,
  ReagentBatchStatus,
  ReagentCreatePayload,
  ReagentGrade,
  ReagentType,
} from "@/lib/types";
import { cn } from "@/lib/utils";

const REAGENT_TYPE_LABELS: Record<ReagentType, string> = {
  REAGENT: "Reagente Analítico",
  PRIMARY_STANDARD_CRM: "Padrão Primário (CRM)",
  SECONDARY_STANDARD: "Padrão Secundário",
  SOLVENT: "Solvente",
  INDICATOR: "Indicador / Tampão",
};

const BATCH_STATUS_LABELS: Record<ReagentBatchStatus, { label: string; color: string }> = {
  AVAILABLE: { label: "Disponível", color: "bg-emerald-50 text-emerald-700 border-emerald-200" },
  IN_USE: { label: "Em Uso", color: "bg-blue-50 text-blue-700 border-blue-200" },
  EXPIRED: { label: "Vencido (Bloqueado)", color: "bg-rose-50 text-rose-700 border-rose-200" },
  DEPLETED: { label: "Esgotado", color: "bg-slate-100 text-slate-600 border-slate-200" },
  QUARANTINE: { label: "Quarentena", color: "bg-amber-50 text-amber-700 border-amber-200" },
};

export function ReagentsPage() {
  const { user } = useAuth();
  const { push } = useToast();
  const queryClient = useQueryClient();

  const [activeTab, setActiveTab] = React.useState<"reagents" | "batches">("batches");
  const [typeFilter, setTypeFilter] = React.useState<string>("TODOS");
  const [search, setSearch] = React.useState("");
  const [availableOnly, setAvailableOnly] = React.useState(false);

  // Modais
  const [createReagentOpen, setCreateReagentOpen] = React.useState(false);
  const [createBatchOpen, setCreateBatchOpen] = React.useState(false);
  const [selectedReagentForBatch, setSelectedReagentForBatch] = React.useState<string>("");

  // Queries
  const reagentsQuery = useQuery({
    queryKey: ["reagents", typeFilter, search],
    queryFn: () =>
      reagentsApi.list({
        reagent_type: typeFilter === "TODOS" ? undefined : typeFilter,
        search: search.trim() || undefined,
      }),
  });

  const batchesQuery = useQuery({
    queryKey: ["reagent-batches", availableOnly],
    queryFn: () => reagentsApi.listBatches({ available_only: availableOnly }),
  });

  const reagents = reagentsQuery.data ?? [];
  const batches = batchesQuery.data ?? [];

  // KPIs
  const totalReagents = reagents.length;
  const totalCRMs = reagents.filter((r) => r.reagent_type === "PRIMARY_STANDARD_CRM").length;
  const availableBatches = batches.filter((b) => b.is_usable).length;
  const expiredBatches = batches.filter((b) => b.is_expired || b.status === "EXPIRED").length;

  return (
    <div className="space-y-6">
      {/* HEADER */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] font-bold uppercase tracking-wider text-primary bg-primary/10 px-2 py-0.5 rounded">
              ISO/IEC 17025:2017 §6.4 & §6.5
            </span>
            <span className="text-xs text-muted-foreground">· Almoxarifado Analítico</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Reagentes e Padrões Analíticos (CRMs)
          </h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Rastreabilidade metrológica de materiais de referência e intertravamento de insumos de bancada.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {["ADMIN", "TECNICO", "FISCAL"].includes(user?.role ?? "") && (
            <>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCreateReagentOpen(true)}
                className="gap-1.5"
              >
                <Plus className="h-4 w-4" />
                Novo Reagente
              </Button>
              <Button
                size="sm"
                onClick={() => {
                  if (reagents.length > 0) {
                    setSelectedReagentForBatch(reagents[0].id);
                  }
                  setCreateBatchOpen(true);
                }}
                className="gap-1.5"
              >
                <Layers className="h-4 w-4" />
                Entrada de Lote
              </Button>
            </>
          )}
          <Button
            variant="ghost"
            size="icon"
            onClick={() => {
              reagentsQuery.refetch();
              batchesQuery.refetch();
            }}
            title="Atualizar dados"
          >
            <RefreshCw className={cn("h-4 w-4", (reagentsQuery.isFetching || batchesQuery.isFetching) && "animate-spin")} />
          </Button>
        </div>
      </div>

      {/* KPIS */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription className="text-xs">Catálogo de Insumos</CardDescription>
            <CardTitle className="text-2xl font-bold flex items-center justify-between">
              <span>{totalReagents}</span>
              <Beaker className="h-5 w-5 text-indigo-500 opacity-80" />
            </CardTitle>
          </CardHeader>
          <CardContent className="text-[11px] text-muted-foreground">
            Reagentes químicos e solventes cadastrados
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription className="text-xs">Padrões Primários (CRM)</CardDescription>
            <CardTitle className="text-2xl font-bold flex items-center justify-between text-indigo-700">
              <span>{totalCRMs}</span>
              <FileCheck className="h-5 w-5 text-indigo-600 opacity-80" />
            </CardTitle>
          </CardHeader>
          <CardContent className="text-[11px] text-muted-foreground">
            Materiais de referência certificados (MRC)
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription className="text-xs">Lotes Prontos para Uso</CardDescription>
            <CardTitle className="text-2xl font-bold flex items-center justify-between text-emerald-700">
              <span>{availableBatches}</span>
              <CheckCircle2 className="h-5 w-5 text-emerald-600 opacity-80" />
            </CardTitle>
          </CardHeader>
          <CardContent className="text-[11px] text-muted-foreground">
            Dentro da validade e com saldo disponível
          </CardContent>
        </Card>

        <Card className={cn(expiredBatches > 0 && "border-rose-300 bg-rose-50/30")}>
          <CardHeader className="pb-2">
            <CardDescription className="text-xs">Lotes Vencidos / Bloqueados</CardDescription>
            <CardTitle className="text-2xl font-bold flex items-center justify-between text-rose-700">
              <span>{expiredBatches}</span>
              <ShieldAlert className="h-5 w-5 text-rose-600 opacity-80" />
            </CardTitle>
          </CardHeader>
          <CardContent className="text-[11px] text-muted-foreground">
            Intertravados contra uso em bancada
          </CardContent>
        </Card>
      </div>

      {/* ABAS & FILTROS */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b pb-3">
        <div className="flex items-center gap-2">
          <Button
            variant={activeTab === "batches" ? "default" : "outline"}
            size="sm"
            onClick={() => setActiveTab("batches")}
            className="text-xs"
          >
            <Layers className="h-3.5 w-3.5 mr-1.5" />
            Lotes & Estoque de Bancada ({batches.length})
          </Button>
          <Button
            variant={activeTab === "reagents" ? "default" : "outline"}
            size="sm"
            onClick={() => setActiveTab("reagents")}
            className="text-xs"
          >
            <Beaker className="h-3.5 w-3.5 mr-1.5" />
            Catálogo Mestre ({reagents.length})
          </Button>
        </div>

        <div className="flex items-center gap-2">
          {activeTab === "reagents" ? (
            <>
              <div className="relative w-48">
                <Search className="h-3.5 w-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Buscar código, nome..."
                  className="h-8 pl-8 text-xs"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </div>
              <Select value={typeFilter} onValueChange={setTypeFilter}>
                <SelectTrigger className="h-8 text-xs w-44">
                  <SelectValue placeholder="Tipo de Insumo" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="TODOS">Todos os Tipos</SelectItem>
                  <SelectItem value="PRIMARY_STANDARD_CRM">Padrão Primário (CRM)</SelectItem>
                  <SelectItem value="REAGENT">Reagente Analítico</SelectItem>
                  <SelectItem value="SOLVENT">Solvente</SelectItem>
                  <SelectItem value="SECONDARY_STANDARD">Padrão Secundário</SelectItem>
                  <SelectItem value="INDICATOR">Indicador / Tampão</SelectItem>
                </SelectContent>
              </Select>
            </>
          ) : (
            <Button
              variant={availableOnly ? "secondary" : "outline"}
              size="sm"
              onClick={() => setAvailableOnly(!availableOnly)}
              className="text-xs h-8"
            >
              <Filter className="h-3.5 w-3.5 mr-1.5" />
              {availableOnly ? "Apenas Disponíveis (Ativo)" : "Filtrar Apenas Disponíveis"}
            </Button>
          )}
        </div>
      </div>

      {/* CONTEÚDO DA ABA 1: LOTES E ESTOQUE FÍSICO */}
      {activeTab === "batches" && (
        <div className="space-y-3">
          {batchesQuery.isLoading ? (
            <div className="p-8 text-center text-sm text-muted-foreground">
              <Loader2 className="h-6 w-6 animate-spin mx-auto mb-2 text-primary" />
              Carregando lotes de insumos analíticos...
            </div>
          ) : batches.length === 0 ? (
            <div className="border border-dashed rounded-lg p-12 text-center text-sm text-muted-foreground">
              Nenhum lote físico cadastrado ou compatível com os filtros atuais.
            </div>
          ) : (
            <div className="border rounded-lg overflow-hidden bg-white shadow-sm">
              <table className="w-full text-xs text-left">
                <thead className="bg-muted/50 border-b font-medium text-muted-foreground">
                  <tr>
                    <th className="py-2.5 px-3">Lote / Fabricante</th>
                    <th className="py-2.5 px-3">Reagente / Insumo</th>
                    <th className="py-2.5 px-3">Validade</th>
                    <th className="py-2.5 px-3">Saldo Disponível</th>
                    <th className="py-2.5 px-3">Certificado CRM</th>
                    <th className="py-2.5 px-3">Status de Bancada</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {batches.map((batch) => {
                    const statusConfig = BATCH_STATUS_LABELS[batch.status] ?? {
                      label: batch.status,
                      color: "bg-slate-100 text-slate-700",
                    };
                    const isNearExpiry = !batch.is_expired && new Date(batch.expiration_date).getTime() - Date.now() < 30 * 86400000;

                    return (
                      <tr key={batch.id} className={cn("hover:bg-muted/30 transition-colors", batch.is_expired && "bg-rose-50/30")}>
                        <td className="py-3 px-3">
                          <div className="font-mono font-bold text-foreground">{batch.lot_number}</div>
                          <div className="text-[11px] text-muted-foreground">{batch.manufacturer}</div>
                        </td>
                        <td className="py-3 px-3">
                          <div className="font-semibold text-foreground">
                            {/* Buscar nome do reagente se carregado */}
                            {batch.reagent_id}
                          </div>
                          {batch.catalog_number && (
                            <div className="text-[10px] text-muted-foreground font-mono">Cat: {batch.catalog_number}</div>
                          )}
                        </td>
                        <td className="py-3 px-3">
                          <div className={cn("font-medium", batch.is_expired ? "text-rose-700 font-bold" : isNearExpiry ? "text-amber-700 font-bold" : "text-foreground")}>
                            {batch.expiration_date}
                          </div>
                          {batch.is_expired ? (
                            <span className="text-[10px] text-rose-600 font-semibold block">Vencido</span>
                          ) : isNearExpiry ? (
                            <span className="text-[10px] text-amber-600 font-semibold block">Vence em &lt;30d</span>
                          ) : null}
                        </td>
                        <td className="py-3 px-3">
                          <div className="font-bold text-foreground">
                            {batch.current_quantity.toFixed(2)} <span className="text-muted-foreground font-normal">{batch.unit}</span>
                          </div>
                          <div className="text-[10px] text-muted-foreground">
                            Inicial: {batch.initial_quantity} {batch.unit}
                          </div>
                        </td>
                        <td className="py-3 px-3">
                          {batch.certificate_number ? (
                            <div>
                              <span className="font-mono text-indigo-700 font-bold block">{batch.certificate_number}</span>
                              {batch.uncertainty_value && (
                                <span className="text-[10px] text-muted-foreground">U = ±{batch.uncertainty_value} (k={batch.k_factor ?? 2})</span>
                              )}
                            </div>
                          ) : (
                            <span className="text-muted-foreground text-[11px]">N/A</span>
                          )}
                        </td>
                        <td className="py-3 px-3">
                          <span className={cn("px-2 py-0.5 rounded-full text-[10px] font-bold border", statusConfig.color)}>
                            {statusConfig.label}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* CONTEÚDO DA ABA 2: CATÁLOGO DE REAGENTES */}
      {activeTab === "reagents" && (
        <div className="space-y-3">
          {reagentsQuery.isLoading ? (
            <div className="p-8 text-center text-sm text-muted-foreground">
              <Loader2 className="h-6 w-6 animate-spin mx-auto mb-2 text-primary" />
              Carregando catálogo de reagentes...
            </div>
          ) : reagents.length === 0 ? (
            <div className="border border-dashed rounded-lg p-12 text-center text-sm text-muted-foreground">
              Nenhum reagente encontrado no catálogo mestre.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {reagents.map((reagent) => (
                <Card key={reagent.id} className="hover:shadow-md transition-shadow">
                  <CardHeader className="pb-2">
                    <div className="flex items-start justify-between gap-2">
                      <span className="font-mono text-xs font-bold bg-muted px-2 py-0.5 rounded">
                        {reagent.code}
                      </span>
                      <span className={cn("text-[10px] font-bold px-2 py-0.5 rounded-full border", reagent.reagent_type === "PRIMARY_STANDARD_CRM" ? "bg-indigo-50 text-indigo-700 border-indigo-200" : "bg-slate-50 text-slate-700 border-slate-200")}>
                        {REAGENT_TYPE_LABELS[reagent.reagent_type] ?? reagent.reagent_type}
                      </span>
                    </div>
                    <CardTitle className="text-sm font-bold text-foreground mt-1.5 leading-snug">
                      {reagent.name}
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="text-xs space-y-1.5 text-muted-foreground">
                    {reagent.chemical_formula && (
                      <div className="flex justify-between">
                        <span>Fórmula:</span>
                        <span className="font-mono text-foreground font-medium">{reagent.chemical_formula}</span>
                      </div>
                    )}
                    {reagent.cas_number && (
                      <div className="flex justify-between">
                        <span>CAS:</span>
                        <span className="font-mono text-foreground">{reagent.cas_number}</span>
                      </div>
                    )}
                    <div className="flex justify-between">
                      <span>Grau de Pureza:</span>
                      <span className="font-semibold text-foreground">{reagent.grade}</span>
                    </div>
                    {(reagent.storage_temperature_min !== null || reagent.storage_temperature_max !== null) && (
                      <div className="flex justify-between">
                        <span>Conservação:</span>
                        <span className="text-foreground">
                          {reagent.storage_temperature_min ?? "-"}ºC a {reagent.storage_temperature_max ?? "-"}ºC
                        </span>
                      </div>
                    )}
                    {reagent.hazard_classification && (
                      <div className="pt-1 border-t text-[11px] text-amber-700 flex items-center gap-1">
                        <Flame className="h-3 w-3 shrink-0" />
                        <span className="truncate">{reagent.hazard_classification}</span>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* MODAL: NOVO REAGENTE */}
      <CreateReagentModal
        open={createReagentOpen}
        onOpenChange={setCreateReagentOpen}
        onSuccess={() => {
          reagentsQuery.refetch();
          push({ title: "Reagente Cadastrado", message: "Insumo adicionado ao catálogo com sucesso.", variant: "success" });
        }}
      />

      {/* MODAL: ENTRADA DE LOTE */}
      <CreateBatchModal
        open={createBatchOpen}
        onOpenChange={setCreateBatchOpen}
        reagents={reagents}
        initialReagentId={selectedReagentForBatch}
        onSuccess={() => {
          batchesQuery.refetch();
          push({ title: "Lote Recebido", message: "Lote físico registrado no estoque do laboratório.", variant: "success" });
        }}
      />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Componentes Modais
// ---------------------------------------------------------------------------

function CreateReagentModal({
  open,
  onOpenChange,
  onSuccess,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => void;
}) {
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const [code, setCode] = React.useState("");
  const [name, setName] = React.useState("");
  const [chemicalFormula, setChemicalFormula] = React.useState("");
  const [casNumber, setCasNumber] = React.useState("");
  const [reagentType, setReagentType] = React.useState<ReagentType>("REAGENT");
  const [grade, setGrade] = React.useState<ReagentGrade>("PA");
  const [tempMin, setTempMin] = React.useState("");
  const [tempMax, setTempMax] = React.useState("");
  const [hazard, setHazard] = React.useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await reagentsApi.create({
        code: code.trim().toUpperCase(),
        name: name.trim(),
        chemical_formula: chemicalFormula.trim() || undefined,
        cas_number: casNumber.trim() || undefined,
        reagent_type: reagentType,
        grade,
        storage_temperature_min: tempMin ? parseFloat(tempMin) : undefined,
        storage_temperature_max: tempMax ? parseFloat(tempMax) : undefined,
        hazard_classification: hazard.trim() || undefined,
      });
      onOpenChange(false);
      onSuccess();
    } catch (err: any) {
      setError(err?.message ?? "Falha ao cadastrar reagente.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Novo Reagente ou Padrão Analítico</DialogTitle>
          <DialogDescription>
            Cadastro no catálogo mestre para controle metrológico e de validade.
          </DialogDescription>
        </DialogHeader>

        {error && (
          <div className="p-2.5 rounded bg-rose-50 border border-rose-200 text-xs text-rose-800">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-3 py-2 text-xs">
          <div className="grid grid-cols-2 gap-2">
            <div className="space-y-1">
              <Label htmlFor="rea-code" className="text-xs">Código Único</Label>
              <Input
                id="rea-code"
                placeholder="Ex: REA-001"
                className="font-mono text-xs uppercase"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                required
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="rea-type" className="text-xs">Tipo de Insumo</Label>
              <Select value={reagentType} onValueChange={(v) => setReagentType(v as ReagentType)}>
                <SelectTrigger id="rea-type" className="text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="REAGENT">Reagente Analítico</SelectItem>
                  <SelectItem value="PRIMARY_STANDARD_CRM">Padrão Primário (CRM)</SelectItem>
                  <SelectItem value="SECONDARY_STANDARD">Padrão Secundário</SelectItem>
                  <SelectItem value="SOLVENT">Solvente</SelectItem>
                  <SelectItem value="INDICATOR">Indicador / Tampão</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-1">
            <Label htmlFor="rea-name" className="text-xs">Nome Químico / Descritivo</Label>
            <Input
              id="rea-name"
              placeholder="Ex: Acetonitrila Grau HPLC"
              className="text-xs"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div className="space-y-1">
              <Label htmlFor="rea-formula" className="text-xs">Fórmula Molecular</Label>
              <Input
                id="rea-formula"
                placeholder="Ex: CH3CN"
                className="font-mono text-xs"
                value={chemicalFormula}
                onChange={(e) => setChemicalFormula(e.target.value)}
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="rea-cas" className="text-xs">Número CAS</Label>
              <Input
                id="rea-cas"
                placeholder="Ex: 75-05-8"
                className="font-mono text-xs"
                value={casNumber}
                onChange={(e) => setCasNumber(e.target.value)}
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-2">
            <div className="space-y-1">
              <Label htmlFor="rea-grade" className="text-xs">Grau</Label>
              <Select value={grade} onValueChange={(v) => setGrade(v as ReagentGrade)}>
                <SelectTrigger id="rea-grade" className="text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="PA">PA</SelectItem>
                  <SelectItem value="HPLC">HPLC</SelectItem>
                  <SelectItem value="USP">USP</SelectItem>
                  <SelectItem value="ANALYTICAL">Analítico</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1">
              <Label htmlFor="rea-tmin" className="text-xs">Temp Mín (ºC)</Label>
              <Input
                id="rea-tmin"
                type="number"
                step="0.1"
                placeholder="-20"
                className="text-xs"
                value={tempMin}
                onChange={(e) => setTempMin(e.target.value)}
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="rea-tmax" className="text-xs">Temp Máx (ºC)</Label>
              <Input
                id="rea-tmax"
                type="number"
                step="0.1"
                placeholder="25"
                className="text-xs"
                value={tempMax}
                onChange={(e) => setTempMax(e.target.value)}
              />
            </div>
          </div>

          <div className="space-y-1">
            <Label htmlFor="rea-hazard" className="text-xs">Classificação de Risco</Label>
            <Input
              id="rea-hazard"
              placeholder="Ex: Líquido inflamável / Armazenar em armário corta-fogo"
              className="text-xs"
              value={hazard}
              onChange={(e) => setHazard(e.target.value)}
            />
          </div>

          <DialogFooter className="pt-2">
            <Button type="button" variant="outline" size="sm" onClick={() => onOpenChange(false)}>
              Cancelar
            </Button>
            <Button type="submit" size="sm" disabled={loading || !code || !name}>
              {loading && <Loader2 className="h-3.5 w-3.5 animate-spin mr-1.5" />}
              Salvar Reagente
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function CreateBatchModal({
  open,
  onOpenChange,
  reagents,
  initialReagentId,
  onSuccess,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  reagents: Reagent[];
  initialReagentId?: string;
  onSuccess: () => void;
}) {
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const [reagentId, setReagentId] = React.useState(initialReagentId ?? "");
  const [lotNumber, setLotNumber] = React.useState("");
  const [manufacturer, setManufacturer] = React.useState("");
  const [catalogNumber, setCatalogNumber] = React.useState("");
  const [expirationDate, setExpirationDate] = React.useState("");
  const [initialQuantity, setInitialQuantity] = React.useState("");
  const [unit, setUnit] = React.useState("g");
  const [certNumber, setCertNumber] = React.useState("");
  const [uncertainty, setUncertainty] = React.useState("");
  const [kFactor, setKFactor] = React.useState("2.0");
  const [notes, setNotes] = React.useState("");

  React.useEffect(() => {
    if (initialReagentId) {
      setReagentId(initialReagentId);
    } else if (reagents.length > 0 && !reagentId) {
      setReagentId(reagents[0].id);
    }
  }, [initialReagentId, reagents]);

  const selectedReagent = reagents.find((r) => r.id === reagentId);
  const isCRM = selectedReagent?.reagent_type === "PRIMARY_STANDARD_CRM";

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!reagentId) return;
    setLoading(true);
    setError(null);
    try {
      await reagentsApi.createBatch(reagentId, {
        lot_number: lotNumber.trim(),
        manufacturer: manufacturer.trim(),
        catalog_number: catalogNumber.trim() || undefined,
        expiration_date: expirationDate,
        initial_quantity: parseFloat(initialQuantity),
        unit,
        certificate_number: certNumber.trim() || undefined,
        uncertainty_value: uncertainty ? parseFloat(uncertainty) : undefined,
        k_factor: kFactor ? parseFloat(kFactor) : 2.0,
        notes: notes.trim() || undefined,
      });
      onOpenChange(false);
      onSuccess();
    } catch (err: any) {
      setError(err?.message ?? "Falha ao registrar lote.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Entrada de Lote Físico de Insumo</DialogTitle>
          <DialogDescription>
            Recebimento de lote com controle de prazo de validade e certificado CRM.
          </DialogDescription>
        </DialogHeader>

        {error && (
          <div className="p-2.5 rounded bg-rose-50 border border-rose-200 text-xs text-rose-800">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-3 py-2 text-xs">
          <div className="space-y-1">
            <Label htmlFor="batch-reagent" className="text-xs">Reagente / Padrão Vinculado</Label>
            <Select value={reagentId} onValueChange={setReagentId}>
              <SelectTrigger id="batch-reagent" className="text-xs">
                <SelectValue placeholder="Selecione o reagente" />
              </SelectTrigger>
              <SelectContent>
                {reagents.map((r) => (
                  <SelectItem key={r.id} value={r.id}>
                    [{r.code}] {r.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div className="space-y-1">
              <Label htmlFor="batch-lot" className="text-xs">Número do Lote</Label>
              <Input
                id="batch-lot"
                placeholder="Ex: LOT-2026-X4"
                className="font-mono text-xs"
                value={lotNumber}
                onChange={(e) => setLotNumber(e.target.value)}
                required
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="batch-mfg" className="text-xs">Fabricante</Label>
              <Input
                id="batch-mfg"
                placeholder="Ex: Sigma-Aldrich / Merck"
                className="text-xs"
                value={manufacturer}
                onChange={(e) => setManufacturer(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div className="space-y-1">
              <Label htmlFor="batch-exp" className="text-xs">Data de Validade</Label>
              <Input
                id="batch-exp"
                type="date"
                className="text-xs"
                value={expirationDate}
                onChange={(e) => setExpirationDate(e.target.value)}
                required
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="batch-cat" className="text-xs">Código Catálogo</Label>
              <Input
                id="batch-cat"
                placeholder="Ex: SIGMA-34856"
                className="font-mono text-xs"
                value={catalogNumber}
                onChange={(e) => setCatalogNumber(e.target.value)}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div className="space-y-1">
              <Label htmlFor="batch-qtd" className="text-xs">Quantidade Recebida</Label>
              <Input
                id="batch-qtd"
                type="number"
                step="0.01"
                placeholder="Ex: 500.0"
                className="text-xs"
                value={initialQuantity}
                onChange={(e) => setInitialQuantity(e.target.value)}
                required
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="batch-unit" className="text-xs">Unidade</Label>
              <Select value={unit} onValueChange={setUnit}>
                <SelectTrigger id="batch-unit" className="text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="g">Gramas (g)</SelectItem>
                  <SelectItem value="mg">Miligramas (mg)</SelectItem>
                  <SelectItem value="mL">Mililitros (mL)</SelectItem>
                  <SelectItem value="L">Litros (L)</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* CAMPOS ESPECÍFICOS DE CRM */}
          {isCRM && (
            <div className="p-2.5 rounded border border-indigo-200 bg-indigo-50/50 space-y-2">
              <div className="font-semibold text-indigo-900 text-[11px] flex items-center gap-1.5">
                <FileCheck className="h-3.5 w-3.5 text-indigo-600" />
                Dados do Certificado Metrológico (CRM - ISO 17025 §6.5)
              </div>
              <div className="space-y-1">
                <Label htmlFor="batch-cert" className="text-[11px]">Nº do Certificado CRM</Label>
                <Input
                  id="batch-cert"
                  placeholder="Ex: CERT-INMETRO-2026-99"
                  className="font-mono text-xs bg-white"
                  value={certNumber}
                  onChange={(e) => setCertNumber(e.target.value)}
                />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div className="space-y-1">
                  <Label htmlFor="batch-unc" className="text-[11px]">Incerteza Expandida U</Label>
                  <Input
                    id="batch-unc"
                    type="number"
                    step="0.0001"
                    placeholder="Ex: 0.005"
                    className="text-xs bg-white font-mono"
                    value={uncertainty}
                    onChange={(e) => setUncertainty(e.target.value)}
                  />
                </div>
                <div className="space-y-1">
                  <Label htmlFor="batch-k" className="text-[11px]">Fator k</Label>
                  <Input
                    id="batch-k"
                    type="number"
                    step="0.1"
                    placeholder="2.0"
                    className="text-xs bg-white font-mono"
                    value={kFactor}
                    onChange={(e) => setKFactor(e.target.value)}
                  />
                </div>
              </div>
            </div>
          )}

          <div className="space-y-1">
            <Label htmlFor="batch-notes" className="text-xs">Observações / Armazenamento</Label>
            <Textarea
              id="batch-notes"
              placeholder="Ex: Frasco lacrado. Armazenar em dissecador à temperatura ambiente."
              className="text-xs"
              rows={2}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
          </div>

          <DialogFooter className="pt-2">
            <Button type="button" variant="outline" size="sm" onClick={() => onOpenChange(false)}>
              Cancelar
            </Button>
            <Button
              type="submit"
              size="sm"
              disabled={loading || !reagentId || !lotNumber || !expirationDate || !initialQuantity}
            >
              {loading && <Loader2 className="h-3.5 w-3.5 animate-spin mr-1.5" />}
              Confirmar Entrada
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
