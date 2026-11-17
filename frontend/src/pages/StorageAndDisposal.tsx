import * as React from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  Boxes,
  CheckCircle2,
  FileCheck2,
  FileText,
  Flame,
  KeyRound,
  Lock,
  Plus,
  RefreshCw,
  Search,
  ShieldAlert,
  ShieldCheck,
  Snowflake,
  Thermometer,
  Trash2,
  Users,
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
import { useAuth } from "@/hooks/use-auth";
import { api, ApiError, storageApi } from "@/lib/api";
import type {
  DisposalMethod,
  RetentionStatus,
  RetentionType,
  SampleDisposalRecord,
  SampleRetention,
  SampleStorageMovement,
  StorageDashboardSummary,
  StorageLocation,
  StorageLocationType,
} from "@/lib/types";
import { formatDateTime } from "@/lib/utils";

const LOCATION_TYPE_LABELS: Record<StorageLocationType, string> = {
  ULTRA_FREEZER: "Ultra Freezer (-80°C)",
  COLD_CHAMBER: "Câmara Fria (2 a 8°C)",
  REFRIGERATOR: "Refrigerador de Bancada",
  CONTROLLED_ROOM: "Sala Climatizada (15 a 25°C)",
  DESICCATOR: "Dessecador sob Vácuo",
  HAZARDOUS_CABINET: "Armário de Inflamáveis / Perigosos",
};

const DISPOSAL_METHOD_LABELS: Record<DisposalMethod, string> = {
  INCINERACAO: "Incineração Térmica Controlada",
  AUTOCLAVAGEM: "Autoclavação e Descontaminação",
  DESCARTE_QUIMICO_ESPECIALIZADO: "Tratamento Químico Especializado",
  DEVOLUCAO_ORGAO_REGULADOR: "Devolução ao Órgão Regulador / ANVISA",
  RECICLAGEM_CONTROLADA: "Reciclagem e Descaracterização Industrial",
};

export function StorageAndDisposalPage() {
  const { user } = useAuth();
  const { push } = useToast();
  const queryClient = useQueryClient();

  const [activeTab, setActiveTab] = React.useState<"locations" | "retentions" | "movements" | "disposals">("locations");

  // Modais
  const [isLocationModalOpen, setIsLocationModalOpen] = React.useState(false);
  const [isRetentionModalOpen, setIsRetentionModalOpen] = React.useState(false);
  const [isMovementModalOpen, setIsMovementModalOpen] = React.useState(false);
  const [isDisposalModalOpen, setIsDisposalModalOpen] = React.useState(false);

  // Queries
  const { data: summary, isLoading: isLoadingSummary } = useQuery<StorageDashboardSummary>({
    queryKey: ["storage-summary"],
    queryFn: () => storageApi.getSummary(),
  });

  const { data: locations = [], isLoading: isLoadingLocations } = useQuery<StorageLocation[]>({
    queryKey: ["storage-locations"],
    queryFn: () => storageApi.listLocations(),
  });

  const { data: retentions = [], isLoading: isLoadingRetentions } = useQuery<SampleRetention[]>({
    queryKey: ["sample-retentions"],
    queryFn: () => storageApi.listRetentions(),
  });

  const { data: movements = [], isLoading: isLoadingMovements } = useQuery<SampleStorageMovement[]>({
    queryKey: ["sample-movements"],
    queryFn: () => storageApi.listMovements(),
  });

  const { data: disposals = [], isLoading: isLoadingDisposals } = useQuery<SampleDisposalRecord[]>({
    queryKey: ["sample-disposals"],
    queryFn: () => storageApi.listDisposals(),
  });

  // Query de usuários para a testemunha do descarte
  const { data: usersList = [] } = useQuery<any[]>({
    queryKey: ["users-for-witness"],
    queryFn: () => api.get<any[]>("/users"),
  });

  // Query de amostras para seleção
  const { data: samplesPage } = useQuery<any>({
    queryKey: ["samples-available"],
    queryFn: () => api.get<any>("/samples?page=1&size=100"),
  });
  const samplesList = samplesPage?.items || [];

  // Form State: Novo Local Físico
  const [locCode, setLocCode] = React.useState("");
  const [locName, setLocName] = React.useState("");
  const [locType, setLocType] = React.useState<StorageLocationType>("ULTRA_FREEZER");
  const [locRoom, setLocRoom] = React.useState("Laboratório Central");
  const [locTargetTemp, setLocTargetTemp] = React.useState(-80.0);
  const [locMinTemp, setLocMinTemp] = React.useState(-86.0);
  const [locMaxTemp, setLocMaxTemp] = React.useState(-70.0);
  const [locCapacity, setLocCapacity] = React.useState(100);
  const [isSubmittingLoc, setIsSubmittingLoc] = React.useState(false);

  // Form State: Nova Retenção de Contraprova
  const [retSampleId, setRetSampleId] = React.useState("");
  const [retLocationId, setRetLocationId] = React.useState("");
  const [retType, setRetType] = React.useState<RetentionType>("CONTRAPROVA_PERICIAL");
  const [retUntil, setRetUntil] = React.useState("");
  const [retQuantity, setRetQuantity] = React.useState(1.0);
  const [retUnit, setRetUnit] = React.useState("un");
  const [retSeal, setRetSeal] = React.useState("");
  const [retNotes, setRetNotes] = React.useState("");
  const [isSubmittingRet, setIsSubmittingRet] = React.useState(false);

  // Form State: Movimentação de Custódia
  const [movSampleId, setMovSampleId] = React.useState("");
  const [movToLocationId, setMovToLocationId] = React.useState("");
  const [movReason, setMovReason] = React.useState("");
  const [movTemp, setMovTemp] = React.useState<string>("");
  const [movNotes, setMovNotes] = React.useState("");
  const [isSubmittingMov, setIsSubmittingMov] = React.useState(false);

  // Form State: Descarte com Dupla Assinatura
  const [dispSampleId, setDispSampleId] = React.useState("");
  const [dispMethod, setDispMethod] = React.useState<DisposalMethod>("INCINERACAO");
  const [dispLicense, setDispLicense] = React.useState("");
  const [dispWasteCompany, setDispWasteCompany] = React.useState("");
  const [dispNotes, setDispNotes] = React.useState("");
  const [dispForceOverride, setDispForceOverride] = React.useState(false);

  // Dupla Autenticação 21 CFR Part 11
  const [primaryPassword, setPrimaryPassword] = React.useState("");
  const [primaryReason, setPrimaryReason] = React.useState("Execução do descarte técnico conforme POP ambiental");
  const [witnessId, setWitnessId] = React.useState("");
  const [witnessPassword, setWitnessPassword] = React.useState("");
  const [witnessReason, setWitnessReason] = React.useState("Testemunho formal e conferência física do descarte");
  const [isSubmittingDisposal, setIsSubmittingDisposal] = React.useState(false);

  // Handlers
  const handleCreateLocation = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setIsSubmittingLoc(true);
      await storageApi.createLocation({
        code: locCode.trim().toUpperCase(),
        name: locName.trim(),
        location_type: locType,
        room: locRoom.trim(),
        temperature_target_celsius: locTargetTemp,
        temperature_min_celsius: locMinTemp,
        temperature_max_celsius: locMaxTemp,
        capacity_units: locCapacity,
      });
      push({
        title: "Local Cadastrado",
        description: `Local ${locCode} registrado com sucesso na cadeia de custódia.`,
      });
      setIsLocationModalOpen(false);
      setLocCode("");
      setLocName("");
      queryClient.invalidateQueries({ queryKey: ["storage-locations"] });
      queryClient.invalidateQueries({ queryKey: ["storage-summary"] });
    } catch (err) {
      push({
        title: "Erro ao Cadastrar",
        description: err instanceof ApiError ? err.message : "Falha na requisição",
        variant: "destructive",
      });
    } finally {
      setIsSubmittingLoc(false);
    }
  };

  const handleCreateRetention = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!retSampleId || !retLocationId || !retUntil || !retSeal) {
      push({ title: "Campos Obrigatórios", description: "Preencha todos os campos do lacre e local.", variant: "destructive" });
      return;
    }
    try {
      setIsSubmittingRet(true);
      await storageApi.createRetention({
        sample_id: retSampleId,
        storage_location_id: retLocationId,
        retention_type: retType,
        retain_until: retUntil,
        quantity_retained: retQuantity,
        unit: retUnit,
        seal_number: retSeal.trim(),
        notes: retNotes || undefined,
      });
      push({
        title: "Contraprova Instituída",
        description: `Lacre ${retSeal} vinculado à amostra com guarda até ${retUntil}.`,
      });
      setIsRetentionModalOpen(false);
      setRetSeal("");
      setRetNotes("");
      queryClient.invalidateQueries({ queryKey: ["sample-retentions"] });
      queryClient.invalidateQueries({ queryKey: ["storage-summary"] });
      queryClient.invalidateQueries({ queryKey: ["storage-locations"] });
    } catch (err) {
      push({
        title: "Erro ao Reter Contraprova",
        description: err instanceof ApiError ? err.message : "Falha na requisição",
        variant: "destructive",
      });
    } finally {
      setIsSubmittingRet(false);
    }
  };

  const handleCreateMovement = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!movSampleId || !movToLocationId || !movReason) {
      push({ title: "Campos Obrigatórios", description: "Informe amostra, destino e motivo.", variant: "destructive" });
      return;
    }
    try {
      setIsSubmittingMov(true);
      const res = await storageApi.createMovement({
        sample_id: movSampleId,
        to_location_id: movToLocationId,
        reason: movReason,
        temperature_at_movement: movTemp ? parseFloat(movTemp) : undefined,
        notes: movNotes || undefined,
      });
      const hasAlert = res.notes?.includes("ALERTA DE EXCURSÃO TÉRMICA");
      push({
        title: hasAlert ? "Movimentação com Alerta Térmico" : "Movimentação Registrada",
        description: hasAlert
          ? "Atenção: Excursão térmica detectada e auditada na trilha ALCOA+!"
          : "Transferência física registrada com sucesso.",
        variant: hasAlert ? "destructive" : "success",
      });
      setIsMovementModalOpen(false);
      setMovReason("");
      setMovTemp("");
      setMovNotes("");
      queryClient.invalidateQueries({ queryKey: ["sample-movements"] });
      queryClient.invalidateQueries({ queryKey: ["storage-locations"] });
    } catch (err) {
      push({
        title: "Erro na Movimentação",
        description: err instanceof ApiError ? err.message : "Falha na requisição",
        variant: "destructive",
      });
    } finally {
      setIsSubmittingMov(false);
    }
  };

  const handleExecuteDisposal = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!dispSampleId || !witnessId || !primaryPassword || !witnessPassword) {
      push({
        title: "Dupla Assinatura Obrigatória",
        description: "Reautenticação do executor e da testemunha requerem senha (21 CFR Part 11).",
        variant: "destructive",
      });
      return;
    }
    if (witnessId === user?.id) {
      push({
        title: "Violação de Segregação",
        description: "O executor não pode testemunhar seu próprio ato de descarte.",
        variant: "destructive",
      });
      return;
    }

    try {
      setIsSubmittingDisposal(true);

      // 1. Emissão de Token 1: Executor
      const primSignRes = await api.post<{ token: string }>("/auth/sign", {
        password: primaryPassword,
        meaning: "EXECUCAO_DESCARTE",
        reason: primaryReason,
        entity_type: "DeviceSample",
        entity_id: dispSampleId,
        action: "CLOSE",
      });

      // 2. Emissão de Token 2: Testemunha (simula reautenticação da testemunha com sua credencial)
      // Para a testemunha, fazemos chamada direta ou login rápido
      const witnessUser = usersList.find((u) => u.id === witnessId);
      if (!witnessUser) throw new Error("Usuário testemunha não identificado");

      const witnessLoginRes = await api.login<{ access_token: string }>(
        witnessUser.username,
        witnessPassword
      );

      // Emite token com o JWT da testemunha
      const witnessSignRes = await fetch("/api/v1/auth/sign", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${witnessLoginRes.access_token}`,
        },
        body: JSON.stringify({
          password: witnessPassword,
          meaning: "TESTEMUNHA_DESCARTE",
          reason: witnessReason,
          entity_type: "DeviceSample",
          entity_id: dispSampleId,
          action: "CLOSE",
        }),
      });
      if (!witnessSignRes.ok) {
        const errJson = await witnessSignRes.json();
        throw new Error(errJson.detail || "Falha na assinatura da testemunha");
      }
      const witnessSignData = await witnessSignRes.json();

      // 3. Submissão do Termo de Descarte com os 2 Tokens
      const disposalRecord = await storageApi.executeDisposal({
        sample_id: dispSampleId,
        disposal_method: dispMethod,
        primary_esign_token: primSignRes.token,
        witness_id: witnessId,
        witness_esign_token: witnessSignData.token,
        environmental_license_number: dispLicense || undefined,
        waste_company_name: dispWasteCompany || undefined,
        notes: dispNotes || undefined,
        force_legal_override: dispForceOverride,
      });

      push({
        title: "Descarte Lavrado com Sucesso",
        description: `Manifesto ${disposalRecord.disposal_manifest_number} emitido com dupla assinatura eletrônica!`,
      });

      setIsDisposalModalOpen(false);
      setPrimaryPassword("");
      setWitnessPassword("");
      setDispLicense("");
      setDispWasteCompany("");
      setDispNotes("");
      setDispForceOverride(false);

      queryClient.invalidateQueries({ queryKey: ["sample-disposals"] });
      queryClient.invalidateQueries({ queryKey: ["sample-retentions"] });
      queryClient.invalidateQueries({ queryKey: ["storage-summary"] });
      queryClient.invalidateQueries({ queryKey: ["samples-available"] });
    } catch (err) {
      push({
        title: "Bloqueio de Descarte",
        description: err instanceof Error ? err.message : "Falha na validação 21 CFR Part 11",
        variant: "destructive",
      });
    } finally {
      setIsSubmittingDisposal(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Cabeçalho */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Cadeia Física, Contraprova e Descarte
          </h1>
          <p className="text-sm text-slate-500">
            Rastreabilidade térmica, guarda legal de contraprova pericial e descarte irreversível com dupla assinatura (ISO 17025 §7.4 e 21 CFR Part 11).
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" size="sm" onClick={() => setIsMovementModalOpen(true)}>
            <ArrowRight className="mr-2 h-4 w-4" />
            Movimentar Amostra
          </Button>
          <Button variant="outline" size="sm" onClick={() => setIsRetentionModalOpen(true)}>
            <Lock className="mr-2 h-4 w-4" />
            Reter Contraprova
          </Button>
          <Button size="sm" onClick={() => setIsDisposalModalOpen(true)} className="bg-red-600 hover:bg-red-700 text-white">
            <Trash2 className="mr-2 h-4 w-4" />
            Termo de Descarte (Part 11)
          </Button>
        </div>
      </div>

      {/* Cards de Resumo */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-slate-500">Locais Ativos</span>
            <div className="rounded-lg bg-blue-50 p-2 text-blue-600">
              <Thermometer className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900">
            {summary?.active_locations ?? 0}
            <span className="text-sm font-normal text-slate-500"> / {summary?.total_locations ?? 0}</span>
          </div>
          <p className="mt-1 text-xs text-slate-500">Câmaras frias e ultrafreezers monitorados</p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-slate-500">Contraprovas sob Guarda</span>
            <div className="rounded-lg bg-emerald-50 p-2 text-emerald-600">
              <Lock className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900">
            {summary?.active_retentions ?? 0}
          </div>
          <p className="mt-1 text-xs text-slate-500">Sob lacre inviolável pericial</p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-slate-500">Contraprovas Vencidas</span>
            <div className={`rounded-lg p-2 ${(summary?.expired_retentions ?? 0) > 0 ? "bg-amber-50 text-amber-600" : "bg-slate-50 text-slate-400"}`}>
              <AlertTriangle className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900">
            {summary?.expired_retentions ?? 0}
          </div>
          <p className="mt-1 text-xs text-slate-500">Aptas para lavratura de expurgo/descarte</p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-slate-500">Manifestos de Descarte</span>
            <div className="rounded-lg bg-purple-50 p-2 text-purple-600">
              <FileCheck2 className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900">
            {summary?.total_disposals ?? 0}
          </div>
          <p className="mt-1 text-xs text-slate-500">Com dupla assinatura eletrônica válida</p>
        </div>
      </div>

      {/* Navegação por Abas */}
      <div className="border-b border-slate-200">
        <nav className="flex space-x-8">
          <button
            onClick={() => setActiveTab("locations")}
            className={`flex items-center gap-2 border-b-2 py-4 text-sm font-medium transition-colors ${
              activeTab === "locations"
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700"
            }`}
          >
            <Boxes className="h-4 w-4" />
            Locais de Custódia e Freezers ({locations.length})
          </button>
          <button
            onClick={() => setActiveTab("retentions")}
            className={`flex items-center gap-2 border-b-2 py-4 text-sm font-medium transition-colors ${
              activeTab === "retentions"
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700"
            }`}
          >
            <Lock className="h-4 w-4" />
            Guarda de Contraprova ({retentions.length})
          </button>
          <button
            onClick={() => setActiveTab("movements")}
            className={`flex items-center gap-2 border-b-2 py-4 text-sm font-medium transition-colors ${
              activeTab === "movements"
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700"
            }`}
          >
            <ArrowRight className="h-4 w-4" />
            Histórico de Movimentações ({movements.length})
          </button>
          <button
            onClick={() => setActiveTab("disposals")}
            className={`flex items-center gap-2 border-b-2 py-4 text-sm font-medium transition-colors ${
              activeTab === "disposals"
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700"
            }`}
          >
            <Trash2 className="h-4 w-4" />
            Manifestos de Descarte ({disposals.length})
          </button>
        </nav>
      </div>

      {/* ABA 1: Locais Físicos */}
      {activeTab === "locations" && (
        <div className="space-y-4">
          <div className="flex justify-end">
            <Button onClick={() => setIsLocationModalOpen(true)} size="sm">
              <Plus className="mr-2 h-4 w-4" /> Novo Local Físico
            </Button>
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
            {locations.map((loc) => {
              const occupancyPct = Math.min(100, Math.round((loc.current_occupancy / loc.capacity_units) * 100));
              return (
                <div key={loc.id} className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm space-y-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-sm font-semibold text-slate-900">{loc.code}</span>
                        {loc.location_type === "ULTRA_FREEZER" ? (
                          <Snowflake className="h-4 w-4 text-cyan-600" />
                        ) : (
                          <Thermometer className="h-4 w-4 text-blue-600" />
                        )}
                      </div>
                      <h3 className="text-base font-medium text-slate-800">{loc.name}</h3>
                      <p className="text-xs text-slate-500">{LOCATION_TYPE_LABELS[loc.location_type]} • Sala: {loc.room}</p>
                    </div>
                    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                      loc.is_active ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-600"
                    }`}>
                      {loc.is_active ? "Ativo" : "Inativo"}
                    </span>
                  </div>

                  <div className="rounded-lg bg-slate-50 p-3 text-xs space-y-1">
                    <div className="flex justify-between text-slate-600">
                      <span>Setpoint Alvo:</span>
                      <span className="font-semibold text-slate-900">{loc.temperature_target_celsius}°C</span>
                    </div>
                    <div className="flex justify-between text-slate-600">
                      <span>Faixa Operacional:</span>
                      <span className="font-medium text-slate-800">{loc.temperature_min_celsius}°C a {loc.temperature_max_celsius}°C</span>
                    </div>
                    {loc.humidity_max_percent && (
                      <div className="flex justify-between text-slate-600">
                        <span>Umidade Máxima:</span>
                        <span className="font-medium text-slate-800">{loc.humidity_max_percent}%</span>
                      </div>
                    )}
                  </div>

                  {/* Barra de Ocupação */}
                  <div>
                    <div className="flex justify-between text-xs text-slate-500 mb-1">
                      <span>Ocupação ({loc.current_occupancy} de {loc.capacity_units})</span>
                      <span>{occupancyPct}%</span>
                    </div>
                    <div className="h-2 w-full rounded-full bg-slate-100 overflow-hidden">
                      <div
                        className={`h-full transition-all ${
                          occupancyPct > 90 ? "bg-red-500" : occupancyPct > 70 ? "bg-amber-500" : "bg-blue-600"
                        }`}
                        style={{ width: `${occupancyPct}%` }}
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ABA 2: Guarda de Contraprovas Periciais */}
      {activeTab === "retentions" && (
        <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
          <div className="border-b border-slate-200 bg-slate-50 px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-600">
            Amostras sob Guarda Legal e Lacre Inviolável (ISO 17025 §7.4)
          </div>
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-slate-500">Lacre Inviolável</th>
                <th className="px-4 py-3 text-left font-medium text-slate-500">Amostra / Produto</th>
                <th className="px-4 py-3 text-left font-medium text-slate-500">Local de Guarda</th>
                <th className="px-4 py-3 text-left font-medium text-slate-500">Qtd Retida</th>
                <th className="px-4 py-3 text-left font-medium text-slate-500">Guarda Até</th>
                <th className="px-4 py-3 text-left font-medium text-slate-500">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {retentions.map((ret) => (
                <tr key={ret.id} className="hover:bg-slate-50">
                  <td className="px-4 py-3 font-mono font-medium text-slate-900">
                    <div className="flex items-center gap-1.5">
                      <Lock className="h-3.5 w-3.5 text-blue-600" />
                      {ret.seal_number}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="font-medium text-slate-900">{ret.sample?.commercial_name}</div>
                    <div className="text-xs text-slate-500 font-mono">{ret.sample?.accession_number}</div>
                  </td>
                  <td className="px-4 py-3 text-slate-700">
                    {ret.storage_location?.code} ({ret.storage_location?.name})
                  </td>
                  <td className="px-4 py-3 text-slate-700">
                    {ret.quantity_retained} {ret.unit}
                  </td>
                  <td className="px-4 py-3">
                    <span className={ret.is_expired ? "font-semibold text-amber-600" : "text-slate-700"}>
                      {ret.retain_until}
                    </span>
                    {ret.is_expired && (
                      <span className="ml-2 inline-flex items-center rounded-full bg-amber-50 px-2 py-0.5 text-xs text-amber-700">
                        Expirada
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                      ret.status === "ACTIVE"
                        ? "bg-emerald-50 text-emerald-700"
                        : ret.status === "EXTENDED"
                        ? "bg-blue-50 text-blue-700"
                        : ret.status === "DISPOSED"
                        ? "bg-slate-100 text-slate-600"
                        : "bg-amber-50 text-amber-700"
                    }`}>
                      {ret.status}
                    </span>
                  </td>
                </tr>
              ))}
              {retentions.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-slate-400">
                    Nenhuma contraprova cadastrada no momento.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* ABA 3: Histórico de Movimentações */}
      {activeTab === "movements" && (
        <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
          <div className="border-b border-slate-200 bg-slate-50 px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-600">
            Cadeia de Custódia Física e Transferências
          </div>
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-slate-500">Data / Hora</th>
                <th className="px-4 py-3 text-left font-medium text-slate-500">Amostra</th>
                <th className="px-4 py-3 text-left font-medium text-slate-500">Origem → Destino</th>
                <th className="px-4 py-3 text-left font-medium text-slate-500">Temp. Medida</th>
                <th className="px-4 py-3 text-left font-medium text-slate-500">Responsável</th>
                <th className="px-4 py-3 text-left font-medium text-slate-500">Motivo / Notas</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {movements.map((mov) => {
                const hasExcursion = mov.notes?.includes("ALERTA DE EXCURSÃO TÉRMICA");
                return (
                  <tr key={mov.id} className={hasExcursion ? "bg-red-50/40 hover:bg-red-50/70" : "hover:bg-slate-50"}>
                    <td className="px-4 py-3 text-xs text-slate-600 font-mono">
                      {formatDateTime(mov.moved_at)}
                    </td>
                    <td className="px-4 py-3 font-medium text-slate-900">
                      {mov.sample?.accession_number}
                    </td>
                    <td className="px-4 py-3 text-slate-700">
                      {mov.from_location?.code || "Recepção Externa"} → <span className="font-semibold">{mov.to_location?.code}</span>
                    </td>
                    <td className="px-4 py-3">
                      {mov.temperature_at_movement !== null && mov.temperature_at_movement !== undefined ? (
                        <span className={`font-mono text-xs font-semibold ${hasExcursion ? "text-red-700" : "text-slate-800"}`}>
                          {mov.temperature_at_movement}°C
                        </span>
                      ) : (
                        <span className="text-slate-400 text-xs">Não informada</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-slate-600 text-xs">
                      {mov.moved_by?.full_name}
                    </td>
                    <td className="px-4 py-3 text-slate-700 text-xs">
                      <div>{mov.reason}</div>
                      {mov.notes && (
                        <div className={hasExcursion ? "font-semibold text-red-600 mt-0.5" : "text-slate-500 mt-0.5"}>
                          {mov.notes}
                        </div>
                      )}
                    </td>
                  </tr>
                );
              })}
              {movements.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-slate-400">
                    Nenhuma movimentação física registrada até o momento.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* ABA 4: Manifestos de Descarte */}
      {activeTab === "disposals" && (
        <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
          <div className="border-b border-slate-200 bg-slate-50 px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-600">
            Termos de Descarte Irreversível com Dupla Assinatura Eletrônica (21 CFR Part 11)
          </div>
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-slate-500">Manifesto</th>
                <th className="px-4 py-3 text-left font-medium text-slate-500">Amostra Expurga</th>
                <th className="px-4 py-3 text-left font-medium text-slate-500">Método de Destinação</th>
                <th className="px-4 py-3 text-left font-medium text-slate-500">Data / Hora</th>
                <th className="px-4 py-3 text-left font-medium text-slate-500">Executor (Assinante 1)</th>
                <th className="px-4 py-3 text-left font-medium text-slate-500">Testemunha / Fiscal (Assinante 2)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {disposals.map((disp) => (
                <tr key={disp.id} className="hover:bg-slate-50">
                  <td className="px-4 py-3 font-mono font-bold text-slate-900">
                    <div className="flex items-center gap-1.5">
                      <FileCheck2 className="h-4 w-4 text-emerald-600" />
                      {disp.disposal_manifest_number}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="font-medium text-slate-900">{disp.sample?.commercial_name}</div>
                    <div className="text-xs text-slate-500 font-mono">{disp.sample?.accession_number}</div>
                  </td>
                  <td className="px-4 py-3 text-slate-700">
                    {DISPOSAL_METHOD_LABELS[disp.disposal_method]}
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-600 font-mono">
                    {formatDateTime(disp.disposed_at)}
                  </td>
                  <td className="px-4 py-3 text-xs">
                    <div className="font-medium text-slate-900">{disp.disposed_by?.full_name}</div>
                    <span className="text-[10px] text-emerald-600 font-mono">Assinatura Certificada</span>
                  </td>
                  <td className="px-4 py-3 text-xs">
                    <div className="font-medium text-slate-900">{disp.witness?.full_name}</div>
                    <span className="text-[10px] text-emerald-600 font-mono">Assinatura Certificada</span>
                  </td>
                </tr>
              ))}
              {disposals.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-slate-400">
                    Nenhum termo de descarte lavrado no sistema.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* MODAL 1: Cadastro de Local Físico */}
      <Dialog open={isLocationModalOpen} onOpenChange={setIsLocationModalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Novo Local de Armazenamento</DialogTitle>
            <DialogDescription>
              Cadastre um freezer, câmara fria ou armário para controle térmico e ambiental.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreateLocation} className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label htmlFor="loc-code">Código Único</Label>
                <Input
                  id="loc-code"
                  placeholder="FRZ-80-01"
                  value={locCode}
                  onChange={(e) => setLocCode(e.target.value)}
                  required
                />
              </div>
              <div>
                <Label htmlFor="loc-type">Tipo de Local</Label>
                <Select value={locType} onValueChange={(v) => setLocType(v as StorageLocationType)}>
                  <SelectTrigger id="loc-type">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(LOCATION_TYPE_LABELS).map(([k, v]) => (
                      <SelectItem key={k} value={k}>
                        {v}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div>
              <Label htmlFor="loc-name">Nome Descritivo</Label>
              <Input
                id="loc-name"
                placeholder="Ultra Freezer Criobiologia Central"
                value={locName}
                onChange={(e) => setLocName(e.target.value)}
                required
              />
            </div>

            <div>
              <Label htmlFor="loc-room">Sala / Setor Físico</Label>
              <Input
                id="loc-room"
                placeholder="Sala 104 - Bloco B"
                value={locRoom}
                onChange={(e) => setLocRoom(e.target.value)}
                required
              />
            </div>

            <div className="grid grid-cols-3 gap-2">
              <div>
                <Label htmlFor="loc-target">Alvo (°C)</Label>
                <Input
                  id="loc-target"
                  type="number"
                  step="0.1"
                  value={locTargetTemp}
                  onChange={(e) => setLocTargetTemp(parseFloat(e.target.value))}
                  required
                />
              </div>
              <div>
                <Label htmlFor="loc-min">Mín (°C)</Label>
                <Input
                  id="loc-min"
                  type="number"
                  step="0.1"
                  value={locMinTemp}
                  onChange={(e) => setLocMinTemp(parseFloat(e.target.value))}
                  required
                />
              </div>
              <div>
                <Label htmlFor="loc-max">Máx (°C)</Label>
                <Input
                  id="loc-max"
                  type="number"
                  step="0.1"
                  value={locMaxTemp}
                  onChange={(e) => setLocMaxTemp(parseFloat(e.target.value))}
                  required
                />
              </div>
            </div>

            <div>
              <Label htmlFor="loc-cap">Capacidade (Unidades)</Label>
              <Input
                id="loc-cap"
                type="number"
                value={locCapacity}
                onChange={(e) => setLocCapacity(parseInt(e.target.value, 10))}
                required
              />
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsLocationModalOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" disabled={isSubmittingLoc}>
                {isSubmittingLoc ? "Gravando..." : "Salvar Local"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* MODAL 2: Instituir Contraprova Pericial */}
      <Dialog open={isRetentionModalOpen} onOpenChange={setIsRetentionModalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Guarda de Contraprova Pericial</DialogTitle>
            <DialogDescription>
              Vincula amostra sob lacre inviolável e data limite legal (ISO 17025 §7.4).
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreateRetention} className="space-y-4">
            <div>
              <Label htmlFor="ret-sample">Amostra</Label>
              <Select value={retSampleId} onValueChange={setRetSampleId}>
                <SelectTrigger id="ret-sample">
                  <SelectValue placeholder="Selecione a amostra..." />
                </SelectTrigger>
                <SelectContent>
                  {samplesList.map((s: any) => (
                    <SelectItem key={s.id} value={s.id}>
                      {s.accession_number} — {s.commercial_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="ret-loc">Local de Armazenamento</Label>
              <Select value={retLocationId} onValueChange={setRetLocationId}>
                <SelectTrigger id="ret-loc">
                  <SelectValue placeholder="Selecione o local físico..." />
                </SelectTrigger>
                <SelectContent>
                  {locations.filter((l) => l.is_active).map((l) => (
                    <SelectItem key={l.id} value={l.id}>
                      {l.code} — {l.name} ({l.temperature_target_celsius}°C)
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label htmlFor="ret-seal">Número do Lacre</Label>
                <Input
                  id="ret-seal"
                  placeholder="LACRE-INVIOLAVEL-2026"
                  value={retSeal}
                  onChange={(e) => setRetSeal(e.target.value)}
                  required
                />
              </div>
              <div>
                <Label htmlFor="ret-until">Guarda Legal Até</Label>
                <Input
                  id="ret-until"
                  type="date"
                  value={retUntil}
                  onChange={(e) => setRetUntil(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label htmlFor="ret-qty">Quantidade Retida</Label>
                <Input
                  id="ret-qty"
                  type="number"
                  step="0.01"
                  value={retQuantity}
                  onChange={(e) => setRetQuantity(parseFloat(e.target.value))}
                  required
                />
              </div>
              <div>
                <Label htmlFor="ret-unit">Unidade</Label>
                <Input
                  id="ret-unit"
                  value={retUnit}
                  onChange={(e) => setRetUnit(e.target.value)}
                  required
                />
              </div>
            </div>

            <div>
              <Label htmlFor="ret-notes">Observações Periciais</Label>
              <Textarea
                id="ret-notes"
                placeholder="Disposição conforme RDC 665/2022 Artigo 45..."
                value={retNotes}
                onChange={(e) => setRetNotes(e.target.value)}
              />
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsRetentionModalOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" disabled={isSubmittingRet}>
                {isSubmittingRet ? "Gravando..." : "Instituir Contraprova"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* MODAL 3: Movimentação Física */}
      <Dialog open={isMovementModalOpen} onOpenChange={setIsMovementModalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Movimentação Física de Custódia</DialogTitle>
            <DialogDescription>
              Transfere amostra entre locais com checagem de excursão térmica imediata.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreateMovement} className="space-y-4">
            <div>
              <Label htmlFor="mov-sample">Amostra</Label>
              <Select value={movSampleId} onValueChange={setMovSampleId}>
                <SelectTrigger id="mov-sample">
                  <SelectValue placeholder="Selecione a amostra..." />
                </SelectTrigger>
                <SelectContent>
                  {samplesList.map((s: any) => (
                    <SelectItem key={s.id} value={s.id}>
                      {s.accession_number} — {s.commercial_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="mov-to">Local de Destino</Label>
              <Select value={movToLocationId} onValueChange={setMovToLocationId}>
                <SelectTrigger id="mov-to">
                  <SelectValue placeholder="Selecione o local de destino..." />
                </SelectTrigger>
                <SelectContent>
                  {locations.filter((l) => l.is_active).map((l) => (
                    <SelectItem key={l.id} value={l.id}>
                      {l.code} — {l.name} (Faixa: {l.temperature_min_celsius}°C a {l.temperature_max_celsius}°C)
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="mov-temp">Temperatura Medida no Ato (°C)</Label>
              <Input
                id="mov-temp"
                type="number"
                step="0.1"
                placeholder="Ex: 4.5"
                value={movTemp}
                onChange={(e) => setMovTemp(e.target.value)}
              />
            </div>

            <div>
              <Label htmlFor="mov-reason">Motivo da Movimentação</Label>
              <Input
                id="mov-reason"
                placeholder="Entrada em refrigerador para início da bateria analítica"
                value={movReason}
                onChange={(e) => setMovReason(e.target.value)}
                required
              />
            </div>

            <div>
              <Label htmlFor="mov-notes">Notas / Condição Visual</Label>
              <Textarea
                id="mov-notes"
                placeholder="Amostra íntegra, embalagem lacrada..."
                value={movNotes}
                onChange={(e) => setMovNotes(e.target.value)}
              />
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsMovementModalOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" disabled={isSubmittingMov}>
                {isSubmittingMov ? "Processando..." : "Confirmar Movimentação"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* MODAL 4: Termo de Descarte com Dupla Assinatura Eletrônica (21 CFR Part 11) */}
      <Dialog open={isDisposalModalOpen} onOpenChange={setIsDisposalModalOpen}>
        <DialogContent className="max-w-xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-red-600">
              <ShieldAlert className="h-5 w-5" />
              Termo de Descarte com Dupla Assinatura (Part 11)
            </DialogTitle>
            <DialogDescription>
              O descarte é irreversível e exige autenticação e assinatura formal de dois operadores habilitados distintos (Executor e Testemunha da Qualidade).
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleExecuteDisposal} className="space-y-4">
            <div>
              <Label htmlFor="disp-sample">Amostra a Ser Descartada</Label>
              <Select value={dispSampleId} onValueChange={setDispSampleId}>
                <SelectTrigger id="disp-sample">
                  <SelectValue placeholder="Selecione a amostra..." />
                </SelectTrigger>
                <SelectContent>
                  {samplesList.filter((s: any) => s.status !== "DESCARTADO").map((s: any) => (
                    <SelectItem key={s.id} value={s.id}>
                      {s.accession_number} — {s.commercial_name} (Status: {s.status})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label htmlFor="disp-method">Método de Destinação</Label>
                <Select value={dispMethod} onValueChange={(v) => setDispMethod(v as DisposalMethod)}>
                  <SelectTrigger id="disp-method">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(DISPOSAL_METHOD_LABELS).map(([k, v]) => (
                      <SelectItem key={k} value={k}>
                        {v}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="disp-license">Licença Ambiental / Órgão</Label>
                <Input
                  id="disp-license"
                  placeholder="LO-IBAMA-2026-9812"
                  value={dispLicense}
                  onChange={(e) => setDispLicense(e.target.value)}
                />
              </div>
            </div>

            <div>
              <Label htmlFor="disp-company">Empresa de Destinação de Resíduos</Label>
              <Input
                id="disp-company"
                placeholder="Ecológica Tratamento de Resíduos Perigosos S/A"
                value={dispWasteCompany}
                onChange={(e) => setDispWasteCompany(e.target.value)}
              />
            </div>

            <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-xs text-red-900 space-y-2">
              <div className="flex items-center gap-1.5 font-semibold">
                <AlertCircle className="h-4 w-4 text-red-600" />
                Intertravamento Regulatório de Contraprova
              </div>
              <p>
                Amostras com contraprova ativa não podem ser expurgadas antes do prazo legal sem liberação formal e expressa.
              </p>
              <label className="flex items-center gap-2 cursor-pointer font-medium">
                <input
                  type="checkbox"
                  checked={dispForceOverride}
                  onChange={(e) => setDispForceOverride(e.target.checked)}
                  className="rounded text-red-600 focus:ring-red-500"
                />
                Autorização legal excepcional para expurgo de contraprova sob custódia
              </label>
            </div>

            {/* SEÇÃO 1: ASSINATURA ELETRÔNICA DO EXECUTOR */}
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 space-y-3">
              <div className="flex items-center gap-2 font-semibold text-xs text-slate-800">
                <KeyRound className="h-4 w-4 text-blue-600" />
                1. Reautenticação do Executor ({user?.full_name})
              </div>
              <div>
                <Label htmlFor="prim-pw" className="text-xs">Senha do Executor</Label>
                <Input
                  id="prim-pw"
                  type="password"
                  placeholder="Confirme sua senha de acesso"
                  value={primaryPassword}
                  onChange={(e) => setPrimaryPassword(e.target.value)}
                  required
                />
              </div>
              <div>
                <Label htmlFor="prim-reason" className="text-xs">Motivo Declarado</Label>
                <Input
                  id="prim-reason"
                  value={primaryReason}
                  onChange={(e) => setPrimaryReason(e.target.value)}
                  required
                />
              </div>
            </div>

            {/* SEÇÃO 2: ASSINATURA ELETRÔNICA DA TESTEMUNHA */}
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 space-y-3">
              <div className="flex items-center gap-2 font-semibold text-xs text-slate-800">
                <Users className="h-4 w-4 text-emerald-600" />
                2. Reautenticação da Testemunha / Fiscal da Qualidade
              </div>
              <div>
                <Label htmlFor="wit-user" className="text-xs">Selecionar Testemunha</Label>
                <Select value={witnessId} onValueChange={setWitnessId}>
                  <SelectTrigger id="wit-user">
                    <SelectValue placeholder="Selecione um fiscal ou técnico distinto..." />
                  </SelectTrigger>
                  <SelectContent>
                    {usersList.filter((u: any) => u.id !== user?.id).map((u: any) => (
                      <SelectItem key={u.id} value={u.id}>
                        {u.full_name} ({u.role}) — {u.email}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="wit-pw" className="text-xs">Senha da Testemunha</Label>
                <Input
                  id="wit-pw"
                  type="password"
                  placeholder="Senha do usuário testemunha"
                  value={witnessPassword}
                  onChange={(e) => setWitnessPassword(e.target.value)}
                  required
                />
              </div>
              <div>
                <Label htmlFor="wit-reason" className="text-xs">Motivo Declarado pela Testemunha</Label>
                <Input
                  id="wit-reason"
                  value={witnessReason}
                  onChange={(e) => setWitnessReason(e.target.value)}
                  required
                />
              </div>
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsDisposalModalOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" disabled={isSubmittingDisposal} className="bg-red-600 hover:bg-red-700 text-white">
                {isSubmittingDisposal ? "Autenticando Dupla Assinatura..." : "Lavrar Termo de Descarte"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
