import * as React from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertTriangle,
  Calendar,
  CheckCircle2,
  Gauge,
  Loader2,
  Plus,
  RefreshCw,
  ShieldAlert,
  Wrench,
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
import { useAuth } from "@/hooks/use-auth";
import { equipmentApi, ApiError } from "@/lib/api";
import type {
  EquipmentCalibrationPayload,
  EquipmentCalibrationStatus,
  EquipmentCreatePayload,
  LaboratoryEquipment,
} from "@/lib/types";
import { formatDateTime } from "@/lib/utils";

export function EquipmentPage() {
  const { user } = useAuth();
  const { push } = useToast();
  const queryClient = useQueryClient();

  const [statusFilter, setStatusFilter] = React.useState<string>("TODOS");
  const [createModalOpen, setCreateModalOpen] = React.useState(false);
  const [calibrateModalOpen, setCalibrateModalOpen] = React.useState(false);
  const [selectedEquipment, setSelectedEquipment] = React.useState<LaboratoryEquipment | null>(null);

  // Form states - Create
  const [createForm, setCreateForm] = React.useState<EquipmentCreatePayload>({
    code: "",
    name: "",
    equipment_type: "",
    manufacturer: "",
    model: "",
    serial_number: "",
    location: "Laboratório Central",
    calibration_status: "CALIBRADO",
    certificate_number: "",
    calibration_agency: "",
    notes: "",
  });
  const [lastCalibDate, setLastCalibDate] = React.useState("");
  const [dueCalibDate, setDueCalibDate] = React.useState("");
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  // Form states - Calibrate
  const [calibForm, setCalibForm] = React.useState<EquipmentCalibrationPayload>({
    last_calibration_at: "",
    calibration_due_date: "",
    certificate_number: "",
    calibration_agency: "",
    calibration_status: "CALIBRADO",
    notes: "",
  });

  const { data: equipmentList = [], isLoading, refetch } = useQuery({
    queryKey: ["equipment", statusFilter],
    queryFn: () =>
      equipmentApi.list(statusFilter === "TODOS" ? undefined : statusFilter),
  });

  const canWrite = user?.role === "ADMIN" || user?.role === "FISCAL" || user?.role === "TECNICO";

  async function handleCreateEquipment(e: React.FormEvent) {
    e.preventDefault();
    if (!createForm.code.trim() || !createForm.name.trim()) {
      push({
        title: "Campos obrigatórios",
        description: "Código e nome do equipamento são obrigatórios.",
        variant: "destructive",
      });
      return;
    }

    setIsSubmitting(true);
    try {
      await equipmentApi.create({
        ...createForm,
        last_calibration_at: lastCalibDate ? new Date(lastCalibDate).toISOString() : null,
        calibration_due_date: dueCalibDate ? new Date(dueCalibDate).toISOString() : null,
      });
      push({
        title: "Equipamento cadastrado",
        description: `Instrumento ${createForm.code} adicionado com sucesso.`,
      });
      setCreateModalOpen(false);
      setCreateForm({
        code: "",
        name: "",
        equipment_type: "",
        manufacturer: "",
        model: "",
        serial_number: "",
        location: "Laboratório Central",
        calibration_status: "CALIBRADO",
        certificate_number: "",
        calibration_agency: "",
        notes: "",
      });
      setLastCalibDate("");
      setDueCalibDate("");
      queryClient.invalidateQueries({ queryKey: ["equipment"] });
    } catch (err) {
      push({
        title: "Erro ao cadastrar",
        description: err instanceof ApiError ? err.message : "Falha na comunicação.",
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleCalibrate(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedEquipment) return;
    if (!calibForm.last_calibration_at || !calibForm.calibration_due_date || !calibForm.certificate_number) {
      push({
        title: "Campos obrigatórios",
        description: "Preencha datas e número do certificado de calibração.",
        variant: "destructive",
      });
      return;
    }

    setIsSubmitting(true);
    try {
      await equipmentApi.calibrate(selectedEquipment.id, {
        ...calibForm,
        last_calibration_at: new Date(calibForm.last_calibration_at).toISOString(),
        calibration_due_date: new Date(calibForm.calibration_due_date).toISOString(),
      });
      push({
        title: "Calibração registrada",
        description: `Certificado ${calibForm.certificate_number} vinculado com sucesso.`,
      });
      setCalibrateModalOpen(false);
      setSelectedEquipment(null);
      queryClient.invalidateQueries({ queryKey: ["equipment"] });
    } catch (err) {
      push({
        title: "Erro na calibração",
        description: err instanceof ApiError ? err.message : "Falha ao registrar calibração.",
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  }

  function openCalibrateModal(eq: LaboratoryEquipment) {
    setSelectedEquipment(eq);
    const today = new Date().toISOString().split("T")[0];
    const nextYear = new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString().split("T")[0];
    setCalibForm({
      last_calibration_at: today,
      calibration_due_date: nextYear,
      certificate_number: "",
      calibration_agency: "Laboratório RBC Acreditado",
      calibration_status: "CALIBRADO",
      notes: "",
    });
    setCalibrateModalOpen(true);
  }

  const expiredCount = equipmentList.filter((e) => !e.is_calibration_valid).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <Gauge className="h-6 w-6 text-primary" />
            Controle Metrológico de Equipamentos
          </h1>
          <p className="text-sm text-muted-foreground">
            Rastreabilidade de instrumentos, bloqueio automático por vencimento de calibração e conformidade ISO/IEC 17025.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" onClick={() => refetch()} className="gap-2">
            <RefreshCw className="h-4 w-4" />
            Atualizar
          </Button>
          {canWrite ? (
            <Button size="sm" onClick={() => setCreateModalOpen(true)} className="gap-2">
              <Plus className="h-4 w-4" />
              Novo Instrumento
            </Button>
          ) : null}
        </div>
      </div>

      {/* Alerta de bloqueio metrológico se houver vencidos */}
      {expiredCount > 0 ? (
        <div className="flex items-start gap-3 rounded-lg border border-rose-300 bg-rose-50 p-4 text-rose-900 shadow-sm">
          <ShieldAlert className="h-5 w-5 text-rose-600 mt-0.5 shrink-0" />
          <div className="text-sm">
            <p className="font-semibold">
              Atenção Metrológica: {expiredCount} instrumento(s) com calibração vencida ou irregular!
            </p>
            <p className="text-rose-800">
              O sistema LIMS bloqueia automaticamente a abertura de novas execuções de ensaio com instrumentos vencidos para garantir a validade jurídica dos laudos periciais.
            </p>
          </div>
        </div>
      ) : null}

      {/* Filtros */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <Label className="text-xs font-medium text-muted-foreground">Filtrar Situação:</Label>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-48 h-8 text-xs">
                  <SelectValue placeholder="Status da calibração" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="TODOS">Todos os instrumentos</SelectItem>
                  <SelectItem value="CALIBRADO">Apenas Calibrados</SelectItem>
                  <SelectItem value="VENCIDO">Apenas Vencidos</SelectItem>
                  <SelectItem value="EM_MANUTENCAO">Em Manutenção</SelectItem>
                  <SelectItem value="NAO_APLICAVEL">Não Aplicável</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="text-xs text-muted-foreground ml-auto">
              Total de instrumentos listados: <strong className="text-foreground">{equipmentList.length}</strong>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Lista de Instrumentos */}
      {isLoading ? (
        <div className="flex items-center justify-center p-12 text-muted-foreground">
          <Loader2 className="h-6 w-6 animate-spin text-primary mr-2" />
          Carregando parque metrológico…
        </div>
      ) : equipmentList.length === 0 ? (
        <Card className="p-8 text-center text-muted-foreground">
          Nenhum equipamento cadastrado com o filtro selecionado.
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {equipmentList.map((eq) => {
            const isInvalid = !eq.is_calibration_valid;
            return (
              <Card
                key={eq.id}
                className={`relative flex flex-col justify-between transition-shadow hover:shadow-md ${
                  isInvalid ? "border-rose-300 bg-rose-50/20" : ""
                }`}
              >
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <span className="text-xs font-mono font-bold text-muted-foreground">
                        {eq.code}
                      </span>
                      <CardTitle className="text-base font-semibold leading-tight mt-0.5">
                        {eq.name}
                      </CardTitle>
                      <CardDescription className="text-xs">
                        {eq.equipment_type || "Instrumento analítico"} • {eq.manufacturer || "Fabricante não inf."}
                      </CardDescription>
                    </div>
                    <StatusBadge status={eq.calibration_status} kind="equipment" />
                  </div>
                </CardHeader>

                <CardContent className="space-y-3 pb-3 text-xs">
                  <div className="grid grid-cols-2 gap-2 border-y border-border/60 py-2">
                    <div>
                      <span className="text-muted-foreground block text-[10px] uppercase tracking-wide">
                        Série / Modelo
                      </span>
                      <span className="font-medium text-foreground">
                        {eq.serial_number || "S/N"} {eq.model ? `(${eq.model})` : ""}
                      </span>
                    </div>
                    <div>
                      <span className="text-muted-foreground block text-[10px] uppercase tracking-wide">
                        Localização
                      </span>
                      <span className="font-medium text-foreground">{eq.location || "Laboratório"}</span>
                    </div>
                  </div>

                  <div className="rounded-md bg-muted/40 p-2 space-y-1">
                    <div className="flex justify-between items-center">
                      <span className="text-muted-foreground">Última Calibração:</span>
                      <span className="font-medium">
                        {eq.last_calibration_at ? formatDateTime(eq.last_calibration_at) : "Pendente"}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-muted-foreground">Validade Metrológica:</span>
                      <span className={`font-semibold ${isInvalid ? "text-rose-600 font-bold" : "text-emerald-700"}`}>
                        {eq.calibration_due_date ? formatDateTime(eq.calibration_due_date) : "Sem data"}
                      </span>
                    </div>
                    {eq.certificate_number ? (
                      <div className="flex justify-between items-center pt-1 border-t border-border/40 text-[11px]">
                        <span className="text-muted-foreground">Certificado:</span>
                        <span className="font-mono text-foreground font-medium">{eq.certificate_number}</span>
                      </div>
                    ) : null}
                  </div>

                  {isInvalid ? (
                    <div className="flex items-center gap-1.5 text-xs text-rose-700 font-medium bg-rose-100/80 px-2 py-1 rounded">
                      <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
                      Uso bloqueado no ensaio (Calibração Expirada)
                    </div>
                  ) : null}
                </CardContent>

                <div className="border-t border-border/60 p-3 pt-2 flex justify-end">
                  {canWrite ? (
                    <Button
                      variant={isInvalid ? "default" : "outline"}
                      size="sm"
                      onClick={() => openCalibrateModal(eq)}
                      className={`text-xs gap-1.5 h-8 ${isInvalid ? "bg-rose-600 hover:bg-rose-700 text-white" : ""}`}
                    >
                      <Wrench className="h-3.5 w-3.5" />
                      {isInvalid ? "Recalibrar Instrumento" : "Nova Calibração"}
                    </Button>
                  ) : null}
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Modal de Cadastro de Equipamento */}
      <Dialog open={createModalOpen} onOpenChange={setCreateModalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Cadastrar Novo Equipamento</DialogTitle>
            <DialogDescription>
              Registre instrumentos analíticos sujeitos a controle metrológico.
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleCreateEquipment} className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label htmlFor="code" className="text-xs">Código Tombamento *</Label>
                <Input
                  id="code"
                  placeholder="EQ-MULT-001"
                  value={createForm.code}
                  onChange={(e) => setCreateForm({ ...createForm, code: e.target.value })}
                  className="h-8 text-xs uppercase"
                  required
                />
              </div>
              <div>
                <Label htmlFor="type" className="text-xs">Tipo do Instrumento</Label>
                <Input
                  id="type"
                  placeholder="Multímetro / Termopar"
                  value={createForm.equipment_type || ""}
                  onChange={(e) => setCreateForm({ ...createForm, equipment_type: e.target.value })}
                  className="h-8 text-xs"
                />
              </div>
            </div>

            <div>
              <Label htmlFor="name" className="text-xs">Nome / Descrição Oficial *</Label>
              <Input
                id="name"
                placeholder="Ex: Multímetro Digital de Bancada 6.5 Dígitos"
                value={createForm.name}
                onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
                className="h-8 text-xs"
                required
              />
            </div>

            <div className="grid grid-cols-3 gap-2">
              <div>
                <Label htmlFor="manuf" className="text-xs">Fabricante</Label>
                <Input
                  id="manuf"
                  placeholder="Fluke / Chroma"
                  value={createForm.manufacturer || ""}
                  onChange={(e) => setCreateForm({ ...createForm, manufacturer: e.target.value })}
                  className="h-8 text-xs"
                />
              </div>
              <div>
                <Label htmlFor="model" className="text-xs">Modelo</Label>
                <Input
                  id="model"
                  placeholder="8846A"
                  value={createForm.model || ""}
                  onChange={(e) => setCreateForm({ ...createForm, model: e.target.value })}
                  className="h-8 text-xs"
                />
              </div>
              <div>
                <Label htmlFor="serial" className="text-xs">Nº de Série</Label>
                <Input
                  id="serial"
                  placeholder="SN-12345"
                  value={createForm.serial_number || ""}
                  onChange={(e) => setCreateForm({ ...createForm, serial_number: e.target.value })}
                  className="h-8 text-xs"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 pt-1 border-t border-border">
              <div>
                <Label htmlFor="last_calib" className="text-xs">Data da Calibração</Label>
                <Input
                  id="last_calib"
                  type="date"
                  value={lastCalibDate}
                  onChange={(e) => setLastCalibDate(e.target.value)}
                  className="h-8 text-xs"
                />
              </div>
              <div>
                <Label htmlFor="due_calib" className="text-xs">Vencimento da Calibração</Label>
                <Input
                  id="due_calib"
                  type="date"
                  value={dueCalibDate}
                  onChange={(e) => setDueCalibDate(e.target.value)}
                  className="h-8 text-xs"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label htmlFor="cert" className="text-xs">Certificado Nº</Label>
                <Input
                  id="cert"
                  placeholder="CAL-2026-001"
                  value={createForm.certificate_number || ""}
                  onChange={(e) => setCreateForm({ ...createForm, certificate_number: e.target.value })}
                  className="h-8 text-xs"
                />
              </div>
              <div>
                <Label htmlFor="agency" className="text-xs">Laboratório Calibrador</Label>
                <Input
                  id="agency"
                  placeholder="Rede RBC Inmetro"
                  value={createForm.calibration_agency || ""}
                  onChange={(e) => setCreateForm({ ...createForm, calibration_agency: e.target.value })}
                  className="h-8 text-xs"
                />
              </div>
            </div>

            <DialogFooter className="pt-2">
              <Button type="button" variant="outline" size="sm" onClick={() => setCreateModalOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" size="sm" disabled={isSubmitting}>
                {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                Salvar Instrumento
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Modal de Registro de Calibração */}
      <Dialog open={calibrateModalOpen} onOpenChange={setCalibrateModalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Registrar Calibração Metrológica</DialogTitle>
            <DialogDescription>
              Instrumento: <strong className="text-foreground">{selectedEquipment?.code}</strong> ({selectedEquipment?.name})
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleCalibrate} className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label htmlFor="c_last" className="text-xs">Data da Realização *</Label>
                <Input
                  id="c_last"
                  type="date"
                  value={calibForm.last_calibration_at}
                  onChange={(e) => setCalibForm({ ...calibForm, last_calibration_at: e.target.value })}
                  className="h-8 text-xs"
                  required
                />
              </div>
              <div>
                <Label htmlFor="c_due" className="text-xs">Próximo Vencimento *</Label>
                <Input
                  id="c_due"
                  type="date"
                  value={calibForm.calibration_due_date}
                  onChange={(e) => setCalibForm({ ...calibForm, calibration_due_date: e.target.value })}
                  className="h-8 text-xs"
                  required
                />
              </div>
            </div>

            <div>
              <Label htmlFor="c_cert" className="text-xs">Número do Certificado RBC *</Label>
              <Input
                id="c_cert"
                placeholder="Ex: CAL-2026-98765-RBC"
                value={calibForm.certificate_number}
                onChange={(e) => setCalibForm({ ...calibForm, certificate_number: e.target.value })}
                className="h-8 text-xs"
                required
              />
            </div>

            <div>
              <Label htmlFor="c_agency" className="text-xs">Órgão / Laboratório Acreditado *</Label>
              <Input
                id="c_agency"
                placeholder="Ex: Lab Metrologia Acreditado Cgcre/Inmetro Nº 123"
                value={calibForm.calibration_agency}
                onChange={(e) => setCalibForm({ ...calibForm, calibration_agency: e.target.value })}
                className="h-8 text-xs"
                required
              />
            </div>

            <div>
              <Label htmlFor="c_notes" className="text-xs">Observações / Incerteza de Medição</Label>
              <Textarea
                id="c_notes"
                placeholder="Incerteza expandida U = 0.05 mA para k=2..."
                value={calibForm.notes || ""}
                onChange={(e) => setCalibForm({ ...calibForm, notes: e.target.value })}
                className="text-xs min-h-[60px]"
              />
            </div>

            <DialogFooter className="pt-2">
              <Button type="button" variant="outline" size="sm" onClick={() => setCalibrateModalOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" size="sm" disabled={isSubmitting}>
                {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                Confirmar Calibração
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
