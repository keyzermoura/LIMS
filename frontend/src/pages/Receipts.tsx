import * as React from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Boxes,
  FileCheck2,
  FolderSync,
  History,
  Loader2,
  PackageCheck,
  Plus,
  RefreshCw,
  Search,
  ShieldAlert,
  ShieldCheck,
  UserCheck,
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
import { useESignature } from "@/hooks/use-esignature";
import { useAuth } from "@/hooks/use-auth";
import { api, ApiError } from "@/lib/api";
import type {
  ChecklistAnswer,
  ChecklistTemplate,
  ConferenceStatus,
  CustodyEventBrief,
  CustodyObject,
  Page,
  Receipt,
  ReceiptDecisionEnum,
  ReceiptItem,
  Solicitation,
  UserBrief,
} from "@/lib/types";
import { formatDateTime } from "@/lib/utils";

export function ReceiptsPage() {
  const { user } = useAuth();
  const { push } = useToast();
  const { requestSignature } = useESignature();
  const queryClient = useQueryClient();
  const [searchParams, setSearchParams] = useSearchParams();

  const [search, setSearch] = React.useState("");
  const [statusFilter, setStatusFilter] = React.useState<string>("ALL");
  const [page, setPage] = React.useState(1);

  // Seleção e Modais
  const [selectedReceipt, setSelectedReceipt] = React.useState<Receipt | null>(null);
  const [createReceiptOpen, setCreateReceiptOpen] = React.useState(false);
  const [submitting, setSubmitting] = React.useState(false);

  // Submissão de novo Recebimento
  const [selectedSolicitationId, setSelectedSolicitationId] = React.useState<string>("");
  const [arrivalLocation, setArrivalLocation] = React.useState(
    "Setor de Triagem e Amostragem - Sala 104",
  );
  const [externalProtocol, setExternalProtocol] = React.useState("");
  const [deliveryMethod, setDeliveryMethod] = React.useState("CORREIOS_SEDEX");
  const [packagingCondition, setPackagingCondition] = React.useState("LACRADO_INTEGRO");
  const [receiptNotes, setReceiptNotes] = React.useState("");

  // Modal Checklist
  const [activeChecklistItem, setActiveChecklistItem] = React.useState<ReceiptItem | null>(
    null,
  );
  const [checklistTemplate, setChecklistTemplate] =
    React.useState<ChecklistTemplate | null>(null);
  const [checklistAnswers, setChecklistAnswers] = React.useState<
    Record<string, { result: "CONFORME" | "NAO_CONFORME" | "NAO_APLICA"; justification: string }>
  >({});
  const [presentedQuantity, setPresentedQuantity] = React.useState<number>(1);
  const [presentationStatus, setPresentationStatus] = React.useState<
    "PRESENTED" | "ABSENT" | "DAMAGED"
  >("PRESENTED");

  // Modal Decisão Técnica
  const [decisionItem, setDecisionItem] = React.useState<ReceiptItem | null>(null);
  const [decisionValue, setDecisionValue] =
    React.useState<ReceiptDecisionEnum>("ACCEPTED");
  const [decisionJustification, setDecisionJustification] = React.useState("");

  // Modal Transferência de Custódia
  const [transferObject, setTransferObject] = React.useState<CustodyObject | null>(null);
  const [toCustodianId, setToCustodianId] = React.useState("");
  const [toLocation, setToLocation] = React.useState("");
  const [transferReason, setTransferReason] = React.useState("");

  // Modal Aceite Técnico
  const [acceptanceObject, setAcceptanceObject] = React.useState<CustodyObject | null>(
    null,
  );
  const [acceptanceLocation, setAcceptanceLocation] = React.useState(
    "Almoxarifado Central / Prateleira B3",
  );
  const [acceptanceNotes, setAcceptanceNotes] = React.useState("");

  // Modal Histórico de Custódia
  const [historyObject, setHistoryObject] = React.useState<CustodyObject | null>(null);
  const [historyEvents, setHistoryEvents] = React.useState<CustodyEventBrief[]>([]);
  const [loadingHistory, setLoadingHistory] = React.useState(false);

  // Lista de Usuários para transferência
  const { data: usersList } = useQuery<UserBrief[]>({
    queryKey: ["users"],
    queryFn: () => api.get<UserBrief[]>("/users"),
  });

  // Solicitações Elegíveis para Recebimento (SUBMITTED e sem recebimento)
  const { data: eligibleSolicitations } = useQuery<Page<Solicitation>>({
    queryKey: ["solicitations-eligible"],
    queryFn: () => api.get<Page<Solicitation>>("/solicitations?status=SUBMITTED&size=50"),
  });

  // Query principal de Recebimentos
  const {
    data: receiptsData,
    isLoading,
    isFetching,
    refetch,
  } = useQuery<Page<Receipt>>({
    queryKey: ["receipts", statusFilter, search, page],
    queryFn: () => {
      const params = new URLSearchParams();
      if (statusFilter !== "ALL") params.append("status", statusFilter);
      if (search.trim()) params.append("search", search.trim());
      params.append("page", String(page));
      params.append("size", "15");
      return api.get<Page<Receipt>>(`/receipts?${params.toString()}`);
    },
  });

  // Carrega template de checklist inicial
  React.useEffect(() => {
    api
      .get<ChecklistTemplate[]>("/checklists/templates")
      .then((templates) => {
        if (templates && templates.length > 0) {
          setChecklistTemplate(templates[0]);
        }
      })
      .catch(() => {});
  }, []);

  // Seleciona solicitação passada via query string
  React.useEffect(() => {
    const solId = searchParams.get("solicitation");
    if (solId) {
      setSelectedSolicitationId(solId);
      setCreateReceiptOpen(true);
    }
  }, [searchParams]);

  const canWrite =
    user?.role === "ADMIN" ||
    user?.role === "FISCAL" ||
    user?.role === "TECNICO" ||
    user?.role === "CUSTODIANTE";

  // Criação de Recebimento
  async function handleCreateReceipt(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedSolicitationId) {
      push({
        title: "Seleção necessária",
        description: "Selecione uma solicitação submetida para criar o recebimento.",
        variant: "warning",
      });
      return;
    }

    try {
      setSubmitting(true);
      const payload = {
        arrival_location: arrivalLocation.trim() || null,
        external_protocol: externalProtocol.trim() || null,
        delivery_method: deliveryMethod.trim() || null,
        packaging_condition: packagingCondition.trim() || null,
        notes: receiptNotes.trim() || null,
      };

      const created = await api.post<Receipt>(
        `/solicitations/${selectedSolicitationId}/receipt`,
        payload,
      );

      push({
        title: "Recebimento Formalizado",
        description: `Recebimento ${created.receipt_number} cadastrado. Pré-amostras geradas sob controle.`,
        variant: "success",
      });
      setCreateReceiptOpen(false);
      setSelectedSolicitationId("");
      setSearchParams({});
      await queryClient.invalidateQueries({ queryKey: ["receipts"] });
      await queryClient.invalidateQueries({ queryKey: ["solicitations-eligible"] });
      setSelectedReceipt(created);
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Erro ao criar recebimento.";
      push({ title: "Falha na criação", description: msg, variant: "destructive" });
    } finally {
      setSubmitting(false);
    }
  }

  // Abertura do Modal de Checklist para um Item
  async function openChecklistModal(item: ReceiptItem) {
    setActiveChecklistItem(item);
    setPresentedQuantity(item.presented_quantity || 1);
    setPresentationStatus(item.presentation_status || "PRESENTED");

    // Carrega respostas já cadastradas caso existam
    if (selectedReceipt) {
      try {
        const answers = await api.get<ChecklistAnswer[]>(
          `/receipts/${selectedReceipt.id}/items/${item.id}/checklist`,
        );
        const map: Record<
          string,
          { result: "CONFORME" | "NAO_CONFORME" | "NAO_APLICA"; justification: string }
        > = {};
        for (const a of answers) {
          map[a.criterion_id] = {
            result: a.result,
            justification: a.justification || "",
          };
        }
        setChecklistAnswers(map);
      } catch {
        setChecklistAnswers({});
      }
    }
  }

  // Atualiza resposta do checklist
  function handleAnswerCriterion(
    criterionId: string,
    result: "CONFORME" | "NAO_CONFORME" | "NAO_APLICA",
    justification?: string,
  ) {
    setChecklistAnswers((prev) => ({
      ...prev,
      [criterionId]: {
        result,
        justification: justification ?? prev[criterionId]?.justification ?? "",
      },
    }));
  }

  // Calcula resultado dinâmico do Checklist em tempo real
  function computePredictedConferenceStatus(): ConferenceStatus {
    if (!checklistTemplate) return "PENDENTE";
    let hasEliminatorioFail = false;
    let hasSaneavelFail = false;

    for (const c of checklistTemplate.criteria) {
      const ans = checklistAnswers[c.id];
      if (!ans) return "PENDENTE";
      if (ans.result === "NAO_CONFORME") {
        if (c.criterion_class === "ELIMINATORIO") hasEliminatorioFail = true;
        if (c.criterion_class === "SANEAVEL") hasSaneavelFail = true;
      }
    }

    if (hasEliminatorioFail) return "NAO_CONFORME";
    if (hasSaneavelFail) return "COM_RESSALVA";
    return "CONFORME";
  }

  // Submissão do Checklist
  async function handleSubmitChecklist(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedReceipt || !activeChecklistItem || !checklistTemplate) return;

    // Validação de justificativa obrigatória para não-conformidades
    for (const c of checklistTemplate.criteria) {
      const ans = checklistAnswers[c.id];
      if (!ans) {
        push({
          title: "Critério pendente",
          description: `Avalie o critério [${c.code}] ${c.description}.`,
          variant: "warning",
        });
        return;
      }
      if (ans.result === "NAO_CONFORME" && !ans.justification.trim()) {
        push({
          title: "Justificativa obrigatória",
          description: `Justifique o não atendimento ao critério [${c.code}].`,
          variant: "warning",
        });
        return;
      }
    }

    try {
      setSubmitting(true);
      const answersPayload = checklistTemplate.criteria.map((c) => ({
        criterion_id: c.id,
        result: checklistAnswers[c.id].result,
        justification: checklistAnswers[c.id].justification.trim() || null,
      }));

      // 1. Atualiza conferência preliminar de quantidade e apresentação se alterada
      await api.post(
        `/receipts/${selectedReceipt.id}/items/${activeChecklistItem.id}/conference`,
        {
          presentation_status: presentationStatus,
          presented_quantity: Number(presentedQuantity),
          conference_status: "PENDENTE",
          version: activeChecklistItem.version,
        },
      );

      // 2. Submete checklist formal
      const updatedItem = await api.post<ReceiptItem>(
        `/receipts/${selectedReceipt.id}/items/${activeChecklistItem.id}/checklist`,
        {
          template_id: checklistTemplate.id,
          answers: answersPayload,
        },
      );

      push({
        title: "Checklist Avaliado",
        description: `Conferência do item concluída com status: ${updatedItem.conference_status}.`,
        variant: "success",
      });

      // Atualiza estado local
      const refreshedReceipt = await api.get<Receipt>(
        `/receipts/${selectedReceipt.id}`,
      );
      setSelectedReceipt(refreshedReceipt);
      setActiveChecklistItem(null);
      await queryClient.invalidateQueries({ queryKey: ["receipts"] });
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Erro ao salvar checklist.";
      push({ title: "Falha na avaliação", description: msg, variant: "destructive" });
    } finally {
      setSubmitting(false);
    }
  }

  // Submissão da Decisão Técnica
  async function handleSubmitDecision(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedReceipt || !decisionItem) return;
    if (decisionJustification.trim().length < 5) {
      push({
        title: "Justificativa insuficiente",
        description: "A justificativa deve conter no mínimo 5 caracteres.",
        variant: "warning",
      });
      return;
    }

    try {
      setSubmitting(true);
      await api.post(
        `/receipts/${selectedReceipt.id}/items/${decisionItem.id}/decisions`,
        {
          decision: decisionValue,
          justification: decisionJustification.trim(),
        },
      );

      push({
        title: "Decisão Registrada",
        description:
          decisionValue === "ACCEPTED"
            ? "Item aceito formalmente para os trâmites laboratoriais."
            : "Decisão gravada. Processo encaminhado para Revisão da Coordenação (D10).",
        variant: "success",
      });

      const refreshed = await api.get<Receipt>(`/receipts/${selectedReceipt.id}`);
      setSelectedReceipt(refreshed);
      setDecisionItem(null);
      setDecisionJustification("");
      await queryClient.invalidateQueries({ queryKey: ["receipts"] });
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Erro ao gravar decisão.";
      push({ title: "Falha na decisão", description: msg, variant: "destructive" });
    } finally {
      setSubmitting(false);
    }
  }

  // Submissão de Transferência de Custódia
  async function handleTransferCustody(e: React.FormEvent) {
    e.preventDefault();
    if (!transferObject) return;
    if (!toCustodianId) {
      push({
        title: "Custodiante obrigatório",
        description: "Selecione o usuário receptor da custódia física.",
        variant: "warning",
      });
      return;
    }

    try {
      setSubmitting(true);
      // Solicita Assinatura Eletrônica regulatória (21 CFR Part 11 / ICP-Brasil)
      const token = await requestSignature({
        entityType: "CustodyObject",
        entityId: transferObject.id,
        action: "TRANSFER",
        meaning: "TRANSFERENCIA_DE_CUSTODIA",
        suggestedReason: transferReason || "Transferência de custódia física interna",
        recordLabel: `Objeto ${transferObject.object_code}`,
      });

      if (!token) {
        setSubmitting(false);
        return;
      }

      await api.post(
        `/custody/objects/${transferObject.id}/transfers`,
        {
          to_custodian_id: toCustodianId,
          to_location: toLocation.trim() || null,
          reason: transferReason.trim() || "Transferência de custódia interna",
          version: transferObject.version,
        },
        token,
      );

      push({
        title: "Custódia Transferida",
        description: `O objeto ${transferObject.object_code} foi transferido com registro assinado.`,
        variant: "success",
      });

      if (selectedReceipt) {
        const refreshed = await api.get<Receipt>(`/receipts/${selectedReceipt.id}`);
        setSelectedReceipt(refreshed);
      }
      setTransferObject(null);
      setToCustodianId("");
      setToLocation("");
      setTransferReason("");
      await queryClient.invalidateQueries({ queryKey: ["receipts"] });
    } catch (err) {
      const msg =
        err instanceof ApiError ? err.message : "Erro na transferência de custódia.";
      push({ title: "Falha na transferência", description: msg, variant: "destructive" });
    } finally {
      setSubmitting(false);
    }
  }

  // Formalização de Aceite Técnico
  async function handleAcceptCustodyObject(e: React.FormEvent) {
    e.preventDefault();
    if (!acceptanceObject) return;

    try {
      setSubmitting(true);
      const token = await requestSignature({
        entityType: "CustodyObject",
        entityId: acceptanceObject.id,
        action: "CREATE",
        meaning: "RESPONSABILIDADE_TECNICA",
        suggestedReason: "Aceite técnico e criação de amostra operacional LIMS",
        recordLabel: `Aceite do Objeto ${acceptanceObject.object_code}`,
      });

      if (!token) {
        setSubmitting(false);
        return;
      }

      const sample = await api.post(
        `/custody/objects/${acceptanceObject.id}/acceptance`,
        {
          decision: "ACCEPTED",
          storage_location: acceptanceLocation.trim(),
          notes: acceptanceNotes.trim() || null,
          version: acceptanceObject.version,
        },
        token,
      );

      push({
        title: "Aceite Técnico Concluído",
        description: `Objeto aceito. Amostra operacional gerada com sucesso!`,
        variant: "success",
      });

      if (selectedReceipt) {
        const refreshed = await api.get<Receipt>(`/receipts/${selectedReceipt.id}`);
        setSelectedReceipt(refreshed);
      }
      setAcceptanceObject(null);
      setAcceptanceNotes("");
      await queryClient.invalidateQueries({ queryKey: ["receipts"] });
    } catch (err) {
      const msg =
        err instanceof ApiError ? err.message : "Erro no aceite técnico do objeto.";
      push({ title: "Falha no aceite", description: msg, variant: "destructive" });
    } finally {
      setSubmitting(false);
    }
  }

  // Ver Histórico de Custódia do Objeto
  async function handleViewHistory(obj: CustodyObject) {
    setHistoryObject(obj);
    setLoadingHistory(true);
    try {
      const events = await api.get<CustodyEventBrief[]>(
        `/custody/objects/${obj.id}/history`,
      );
      setHistoryEvents(events);
    } catch {
      setHistoryEvents([]);
    } finally {
      setLoadingHistory(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Recebimento Físico & Pré-Amostra
          </h1>
          <p className="text-sm text-muted-foreground">
            Formalização de chegada física, pré-amostras sob custódia, conferência
            regulatória e aceite operacional.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            disabled={isFetching}
          >
            <RefreshCw
              className={`mr-2 h-4 w-4 ${isFetching ? "animate-spin" : ""}`}
            />
            Atualizar
          </Button>
          {canWrite && (
            <Button size="sm" onClick={() => setCreateReceiptOpen(true)}>
              <Plus className="mr-2 h-4 w-4" />
              Registrar Chegada Física
            </Button>
          )}
        </div>
      </div>

      {/* Filter bar */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col gap-4 md:flex-row md:items-center">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Buscar por código de recebimento (ex: REC-2026-00001) ou protocolo…"
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setPage(1);
                }}
                className="pl-9"
              />
            </div>
            <div className="w-full md:w-56">
              <Select
                value={statusFilter}
                onValueChange={(val) => {
                  setStatusFilter(val);
                  setPage(1);
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">Todos os status</SelectItem>
                  <SelectItem value="DRAFT">Rascunho</SelectItem>
                  <SelectItem value="EM_CONFERENCIA">Em Conferência</SelectItem>
                  <SelectItem value="CONCLUIDO">Concluído</SelectItem>
                  <SelectItem value="CANCELADO">Cancelado</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* List */}
      <Card>
        <CardHeader className="border-b pb-4">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg">Recebimentos Físicos</CardTitle>
              <CardDescription>
                {receiptsData?.total ?? 0} lote(s) recebido(s) no protocolo
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex h-48 items-center justify-center">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : !receiptsData?.items.length ? (
            <div className="flex flex-col items-center justify-center py-12 text-center text-muted-foreground">
              <PackageCheck className="h-10 w-10 text-muted-foreground/60 mb-3" />
              <p className="text-sm font-medium">Nenhum recebimento registrado.</p>
              <p className="text-xs">
                Formalize a chegada física vinculando uma solicitação submetida.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-muted/50 text-xs uppercase text-muted-foreground">
                  <tr>
                    <th className="px-4 py-3 font-semibold">Recebimento</th>
                    <th className="px-4 py-3 font-semibold">Chegada em</th>
                    <th className="px-4 py-3 font-semibold">Local de Entrada</th>
                    <th className="px-4 py-3 font-semibold">Transporte / Protocolo</th>
                    <th className="px-4 py-3 font-semibold text-center">Itens</th>
                    <th className="px-4 py-3 font-semibold">Status</th>
                    <th className="px-4 py-3 font-semibold text-right">Ação</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {receiptsData.items.map((r) => (
                    <tr
                      key={r.id}
                      className="hover:bg-muted/30 transition-colors cursor-pointer"
                      onClick={() => setSelectedReceipt(r)}
                    >
                      <td className="px-4 py-3 font-semibold font-mono text-primary">
                        {r.receipt_number}
                      </td>
                      <td className="px-4 py-3 text-xs text-muted-foreground whitespace-nowrap">
                        {formatDateTime(r.arrived_at)}
                      </td>
                      <td className="px-4 py-3 text-xs font-medium">
                        {r.arrival_location || "—"}
                      </td>
                      <td className="px-4 py-3 text-xs text-muted-foreground">
                        <div>{r.delivery_method || "—"}</div>
                        <div className="font-mono text-[11px] text-muted-foreground">
                          {r.external_protocol ? `Prot: ${r.external_protocol}` : ""}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className="inline-flex items-center justify-center rounded-full bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-800">
                          {r.items.length}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <StatusBadge status={r.status} kind="receipt" />
                      </td>
                      <td
                        className="px-4 py-3 text-right"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setSelectedReceipt(r)}
                        >
                          Conferir
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Modal / Drawer: Detalhes do Recebimento e Conferência */}
      <Dialog
        open={Boolean(selectedReceipt)}
        onOpenChange={(open) => !open && setSelectedReceipt(null)}
      >
        <DialogContent className="max-w-4xl max-h-[92vh] overflow-y-auto">
          {selectedReceipt && (
            <div className="space-y-6">
              <DialogHeader>
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <DialogTitle className="text-xl font-bold font-mono">
                      {selectedReceipt.receipt_number}
                    </DialogTitle>
                    <DialogDescription>
                      Chegada em {formatDateTime(selectedReceipt.arrived_at)} ·{" "}
                      {selectedReceipt.arrival_location}
                    </DialogDescription>
                  </div>
                  <StatusBadge
                    status={selectedReceipt.status}
                    kind="receipt"
                    className="text-xs"
                  />
                </div>
              </DialogHeader>

              {/* Informações de Transporte e Condição */}
              <div className="grid grid-cols-3 gap-3 rounded-lg border p-3 bg-muted/20 text-xs">
                <div>
                  <span className="text-muted-foreground">Transportador / Método:</span>
                  <p className="font-semibold">{selectedReceipt.delivery_method || "—"}</p>
                  <p className="font-mono text-[11px] text-muted-foreground">
                    {selectedReceipt.external_protocol || "Sem protocolo rastreador"}
                  </p>
                </div>
                <div>
                  <span className="text-muted-foreground">Condição da Embalagem:</span>
                  <p className="font-semibold">
                    {selectedReceipt.packaging_condition || "—"}
                  </p>
                </div>
                <div>
                  <span className="text-muted-foreground">Recebido por:</span>
                  <p className="font-semibold">
                    {selectedReceipt.received_by?.full_name || "—"}
                  </p>
                </div>
              </div>

              {/* Lista de Itens Recebidos e Pré-Amostras */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-bold text-foreground uppercase tracking-wide">
                    Itens e Objetos de Pré-Custódia ({selectedReceipt.items.length})
                  </h3>
                </div>

                <div className="space-y-3">
                  {selectedReceipt.items.map((item) => (
                    <div
                      key={item.id}
                      className="rounded-lg border p-4 space-y-3 bg-card"
                    >
                      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b pb-2">
                        <div>
                          <div className="font-semibold text-base text-foreground">
                            {item.solicitation_item?.product_name || "Item sem nome"}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            Fabricante: {item.solicitation_item?.manufacturer || "—"} ·{" "}
                            Modelo: {item.solicitation_item?.model || "—"} · Lote:{" "}
                            {item.solicitation_item?.lot_number || "—"} · S/N:{" "}
                            {item.solicitation_item?.serial_number || "—"}
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <StatusBadge
                            status={item.conference_status}
                            kind="conference"
                            className="text-xs"
                          />
                          {item.decision && (
                            <StatusBadge
                              status={item.decision}
                              kind="decision"
                              className="text-xs"
                            />
                          )}
                        </div>
                      </div>

                      {/* Quantidades e Ações de Conferência */}
                      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 text-xs bg-muted/20 p-2.5 rounded">
                        <div className="flex items-center gap-4">
                          <div>
                            <span className="text-muted-foreground">Qtd. Declarada: </span>
                            <span className="font-bold">
                              {item.solicitation_item?.declared_quantity || 1}{" "}
                              {item.solicitation_item?.unit_of_measure || "UN"}
                            </span>
                          </div>
                          <div>
                            <span className="text-muted-foreground">Qtd. Apresentada: </span>
                            <span className="font-bold text-primary">
                              {item.presented_quantity}{" "}
                              {item.solicitation_item?.unit_of_measure || "UN"}
                            </span>
                          </div>
                        </div>

                        {canWrite && (
                          <div className="flex items-center gap-2">
                            <Button
                              variant="outline"
                              size="sm"
                              className="h-8 text-xs"
                              onClick={() => openChecklistModal(item)}
                            >
                              <FileCheck2 className="mr-1.5 h-3.5 w-3.5 text-primary" />
                              Conferência & Checklist
                            </Button>
                            <Button
                              variant="secondary"
                              size="sm"
                              className="h-8 text-xs"
                              onClick={() => {
                                setDecisionItem(item);
                                setDecisionValue(
                                  item.conference_status === "NAO_CONFORME"
                                    ? "REJECTED"
                                    : item.conference_status === "COM_RESSALVA"
                                      ? "PENDING"
                                      : "ACCEPTED",
                                );
                                setDecisionJustification("");
                              }}
                            >
                              <UserCheck className="mr-1.5 h-3.5 w-3.5 text-primary" />
                              Decisão Técnica
                            </Button>
                          </div>
                        )}
                      </div>

                      {/* Lista de Objetos de Custódia vinculados ao item */}
                      <div className="space-y-1.5 pt-1">
                        <span className="text-[11px] font-semibold uppercase text-muted-foreground">
                          Objetos sob Custódia Física de Pré-Amostra:
                        </span>
                        <div className="rounded border divide-y overflow-hidden text-xs">
                          {item.custody_objects.map((obj) => (
                            <div
                              key={obj.id}
                              className="p-2.5 flex flex-col md:flex-row md:items-center justify-between gap-2 bg-background hover:bg-muted/10 transition-colors"
                            >
                              <div className="flex items-center gap-2.5">
                                <Boxes className="h-4 w-4 text-primary shrink-0" />
                                <div>
                                  <div className="font-mono font-bold text-foreground">
                                    {obj.object_code}
                                  </div>
                                  <div className="text-[11px] text-muted-foreground">
                                    Local: {obj.current_location || "—"} · Custodiante:{" "}
                                    {obj.current_custodian?.full_name || "—"}
                                  </div>
                                </div>
                              </div>

                              <div className="flex items-center gap-2 shrink-0">
                                <StatusBadge
                                  status={obj.status}
                                  kind="custody_object"
                                  className="text-[10px]"
                                />

                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="h-7 px-2 text-[11px]"
                                  title="Ver Trilha de Custódia"
                                  onClick={() => handleViewHistory(obj)}
                                >
                                  <History className="h-3.5 w-3.5" />
                                </Button>

                                {canWrite && obj.status !== "ACEITO" && (
                                  <>
                                    <Button
                                      variant="outline"
                                      size="sm"
                                      className="h-7 px-2 text-[11px]"
                                      onClick={() => {
                                        setTransferObject(obj);
                                        setToLocation(obj.current_location || "");
                                        setTransferReason("");
                                      }}
                                    >
                                      <FolderSync className="mr-1 h-3 w-3" />
                                      Transferir
                                    </Button>

                                    <Button
                                      variant="default"
                                      size="sm"
                                      className="h-7 px-2 text-[11px]"
                                      onClick={() => {
                                        setAcceptanceObject(obj);
                                        setAcceptanceLocation(
                                          obj.current_location ||
                                            "Almoxarifado Central / Prateleira B3",
                                        );
                                        setAcceptanceNotes("");
                                      }}
                                    >
                                      <ShieldCheck className="mr-1 h-3 w-3" />
                                      Aceite Técnico
                                    </Button>
                                  </>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Modal: Novo Recebimento Físico */}
      <Dialog open={createReceiptOpen} onOpenChange={setCreateReceiptOpen}>
        <DialogContent className="max-w-xl">
          <DialogHeader>
            <DialogTitle>Formalizar Chegada Física de Lote</DialogTitle>
            <DialogDescription>
              Vincule a solicitação submetida e registre a entrada das caixas no
              protocolo.
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleCreateReceipt} className="space-y-4">
            <div className="space-y-1">
              <Label>Solicitação de Origem (SEFI) *</Label>
              <Select
                value={selectedSolicitationId}
                onValueChange={setSelectedSolicitationId}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Selecione a demanda submetida…" />
                </SelectTrigger>
                <SelectContent>
                  {eligibleSolicitations?.items
                    .filter((s) => !s.has_receipt)
                    .map((s) => (
                      <SelectItem key={s.id} value={s.id}>
                        {s.solicitation_number} — {s.requester_name} (
                        {s.items.length} item(ns))
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label htmlFor="rec-loc">Local de Entrada no Laboratório</Label>
                <Input
                  id="rec-loc"
                  value={arrivalLocation}
                  onChange={(e) => setArrivalLocation(e.target.value)}
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="rec-prot">Protocolo / Rastreio Externo</Label>
                <Input
                  id="rec-prot"
                  placeholder="Ex: BR123456789XX"
                  value={externalProtocol}
                  onChange={(e) => setExternalProtocol(e.target.value)}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label>Método de Entrega / Transportadora</Label>
                <Select value={deliveryMethod} onValueChange={setDeliveryMethod}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="CORREIOS_SEDEX">Correios (Sedex)</SelectItem>
                    <SelectItem value="TRANSPORTADORA_ESPECIAL">
                      Transportadora Especializada
                    </SelectItem>
                    <SelectItem value="ENTREGA_DIRETA_FISCAL">
                      Entrega Direta pelo Fiscal Sanitário
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1">
                <Label>Condição Inicial da Embalagem</Label>
                <Select
                  value={packagingCondition}
                  onValueChange={setPackagingCondition}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="LACRADO_INTEGRO">
                      Lacrado e Íntegro
                    </SelectItem>
                    <SelectItem value="AVARIADO_VIOLADO">
                      Avariado / Lacre Rompido
                    </SelectItem>
                    <SelectItem value="SEM_LACRE">Sem Lacre</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-1">
              <Label htmlFor="rec-notes">Observações do Protocolo</Label>
              <Textarea
                id="rec-notes"
                rows={2}
                placeholder="Observações de temperatura, integridade das caixas, etc."
                value={receiptNotes}
                onChange={(e) => setReceiptNotes(e.target.value)}
              />
            </div>

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setCreateReceiptOpen(false)}
              >
                Cancelar
              </Button>
              <Button type="submit" disabled={submitting}>
                {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Registrar Chegada
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Modal: Conferência Física & Checklist */}
      <Dialog
        open={Boolean(activeChecklistItem)}
        onOpenChange={(open) => !open && setActiveChecklistItem(null)}
      >
        <DialogContent className="max-w-3xl max-h-[92vh] overflow-y-auto">
          {activeChecklistItem && checklistTemplate && (
            <form onSubmit={handleSubmitChecklist} className="space-y-5">
              <DialogHeader>
                <DialogTitle>Conferência Física & Checklist Regulatório</DialogTitle>
                <DialogDescription>
                  {activeChecklistItem.solicitation_item?.product_name} · Template:{" "}
                  {checklistTemplate.name} ({checklistTemplate.code})
                </DialogDescription>
              </DialogHeader>

              {/* Quantidade Apresentada */}
              <div className="grid grid-cols-2 gap-3 p-3 rounded-lg border bg-muted/20">
                <div className="space-y-1">
                  <Label>Apresentação Física</Label>
                  <Select
                    value={presentationStatus}
                    onValueChange={(val: "PRESENTED" | "ABSENT" | "DAMAGED") =>
                      setPresentationStatus(val)
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="PRESENTED">Dispositivo Apresentado</SelectItem>
                      <SelectItem value="ABSENT">Não Apresentado / Ausente</SelectItem>
                      <SelectItem value="DAMAGED">Apresentado com Avaria</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1">
                  <Label>Quantidade Física Conferida</Label>
                  <Input
                    type="number"
                    min="0"
                    required
                    value={presentedQuantity}
                    onChange={(e) => setPresentedQuantity(Number(e.target.value))}
                  />
                </div>
              </div>

              {/* Critérios do Checklist */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-semibold uppercase text-muted-foreground">
                    Critérios de Verificação Física
                  </h4>
                  <div className="flex items-center gap-1.5 text-xs">
                    <span className="text-muted-foreground">Status calculado:</span>
                    <StatusBadge
                      status={computePredictedConferenceStatus()}
                      kind="conference"
                      className="text-xs"
                    />
                  </div>
                </div>

                <div className="space-y-3">
                  {checklistTemplate.criteria.map((c) => {
                    const ans = checklistAnswers[c.id] || {
                      result: "CONFORME",
                      justification: "",
                    };
                    const isEliminatorio = c.criterion_class === "ELIMINATORIO";

                    return (
                      <div
                        key={c.id}
                        className={`p-3 rounded-lg border space-y-2 ${
                          ans.result === "NAO_CONFORME"
                            ? isEliminatorio
                              ? "border-rose-300 bg-rose-50/40"
                              : "border-amber-300 bg-amber-50/40"
                            : "bg-background"
                        }`}
                      >
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                          <div className="flex items-start gap-2">
                            <span className="font-mono text-xs font-bold text-foreground">
                              [{c.code}]
                            </span>
                            <div>
                              <p className="text-xs font-medium text-foreground">
                                {c.description}
                              </p>
                              <div className="flex items-center gap-2 mt-0.5">
                                <StatusBadge
                                  status={c.criterion_class}
                                  kind="criterion_class"
                                  className="text-[10px]"
                                />
                                {c.is_mandatory && (
                                  <span className="text-[10px] text-rose-600 font-semibold">
                                    Obrigatório
                                  </span>
                                )}
                              </div>
                            </div>
                          </div>

                          <div className="flex items-center gap-1 shrink-0">
                            <button
                              type="button"
                              className={`px-2.5 py-1 text-xs rounded border transition-colors ${
                                ans.result === "CONFORME"
                                  ? "bg-emerald-600 text-white border-emerald-600"
                                  : "bg-muted/50 hover:bg-muted text-muted-foreground border-border"
                              }`}
                              onClick={() =>
                                handleAnswerCriterion(c.id, "CONFORME")
                              }
                            >
                              Atende
                            </button>
                            <button
                              type="button"
                              className={`px-2.5 py-1 text-xs rounded border transition-colors ${
                                ans.result === "NAO_CONFORME"
                                  ? "bg-rose-600 text-white border-rose-600"
                                  : "bg-muted/50 hover:bg-muted text-muted-foreground border-border"
                              }`}
                              onClick={() =>
                                handleAnswerCriterion(c.id, "NAO_CONFORME")
                              }
                            >
                              Não Atende
                            </button>
                            <button
                              type="button"
                              className={`px-2.5 py-1 text-xs rounded border transition-colors ${
                                ans.result === "NAO_APLICA"
                                  ? "bg-slate-700 text-white border-slate-700"
                                  : "bg-muted/50 hover:bg-muted text-muted-foreground border-border"
                              }`}
                              onClick={() =>
                                handleAnswerCriterion(c.id, "NAO_APLICA")
                              }
                            >
                              N/A
                            </button>
                          </div>
                        </div>

                        {ans.result === "NAO_CONFORME" && (
                          <div className="space-y-1 pt-1">
                            <Label className="text-[11px] text-rose-700 font-semibold">
                              Justificativa da Não-Conformidade (Obrigatória) *
                            </Label>
                            <Input
                              required
                              placeholder="Descreva o motivo da inconformidade física/documental..."
                              value={ans.justification}
                              onChange={(e) =>
                                handleAnswerCriterion(
                                  c.id,
                                  "NAO_CONFORME",
                                  e.target.value,
                                )
                              }
                            />
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>

              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setActiveChecklistItem(null)}
                >
                  Cancelar
                </Button>
                <Button type="submit" disabled={submitting}>
                  {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  Salvar Avaliação
                </Button>
              </DialogFooter>
            </form>
          )}
        </DialogContent>
      </Dialog>

      {/* Modal: Decisão Técnica Formalizada */}
      <Dialog
        open={Boolean(decisionItem)}
        onOpenChange={(open) => !open && setDecisionItem(null)}
      >
        <DialogContent className="max-w-md">
          {decisionItem && (
            <form onSubmit={handleSubmitDecision} className="space-y-4">
              <DialogHeader>
                <DialogTitle>Decisão Técnica de Recebimento</DialogTitle>
                <DialogDescription>
                  Formalize a deliberação técnica para o item{" "}
                  {decisionItem.solicitation_item?.product_name}.
                </DialogDescription>
              </DialogHeader>

              <div className="space-y-1">
                <Label>Decisão *</Label>
                <Select
                  value={decisionValue}
                  onValueChange={(val: ReceiptDecisionEnum) => setDecisionValue(val)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ACCEPTED">Aceitar Amostra</SelectItem>
                    <SelectItem value="PENDING">
                      Pendente de Revisão da Coordenação
                    </SelectItem>
                    <SelectItem value="REJECTED">Rejeitar Amostra</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {decisionValue !== "ACCEPTED" && (
                <div className="p-3 rounded-lg border border-amber-200 bg-amber-50/70 text-xs text-amber-900 flex items-start gap-2">
                  <ShieldAlert className="h-4 w-4 shrink-0 mt-0.5 text-amber-700" />
                  <p>
                    <strong>Atenção Regulatória (D10):</strong> Itens com pendência
                    ou rejeição abrem automaticamente uma{" "}
                    <em>Revisão da Coordenação</em>. O coordenador que deliberar
                    deve ser diferente do técnico emissor (segregação de funções).
                  </p>
                </div>
              )}

              <div className="space-y-1">
                <Label htmlFor="dec-just">Justificativa Técnica *</Label>
                <Textarea
                  id="dec-just"
                  required
                  rows={3}
                  placeholder="Fundamente os aspectos técnicos, normativos ou regulatórios da decisão..."
                  value={decisionJustification}
                  onChange={(e) => setDecisionJustification(e.target.value)}
                />
              </div>

              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setDecisionItem(null)}
                >
                  Cancelar
                </Button>
                <Button type="submit" disabled={submitting}>
                  {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  Gravar Decisão
                </Button>
              </DialogFooter>
            </form>
          )}
        </DialogContent>
      </Dialog>

      {/* Modal: Transferência de Custódia */}
      <Dialog
        open={Boolean(transferObject)}
        onOpenChange={(open) => !open && setTransferObject(null)}
      >
        <DialogContent className="max-w-md">
          {transferObject && (
            <form onSubmit={handleTransferCustody} className="space-y-4">
              <DialogHeader>
                <DialogTitle>Transferência de Custódia</DialogTitle>
                <DialogDescription>
                  Transferir responsabilidade física do objeto{" "}
                  {transferObject.object_code}. Requer assinatura eletrônica.
                </DialogDescription>
              </DialogHeader>

              <div className="space-y-1">
                <Label>Novo Custodiante *</Label>
                <Select value={toCustodianId} onValueChange={setToCustodianId}>
                  <SelectTrigger>
                    <SelectValue placeholder="Selecione o destinatário…" />
                  </SelectTrigger>
                  <SelectContent>
                    {usersList?.map((u) => (
                      <SelectItem key={u.id} value={u.id}>
                        {u.full_name} ({u.role})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-1">
                <Label htmlFor="to-loc">Novo Local de Armazenamento</Label>
                <Input
                  id="to-loc"
                  placeholder="Ex: Sala de Ensaios Elétricos - Bancada 2"
                  value={toLocation}
                  onChange={(e) => setToLocation(e.target.value)}
                />
              </div>

              <div className="space-y-1">
                <Label htmlFor="trans-reason">Motivo da Transferência *</Label>
                <Input
                  id="trans-reason"
                  required
                  placeholder="Ex: Encaminhamento para ensaios mecânicos"
                  value={transferReason}
                  onChange={(e) => setTransferReason(e.target.value)}
                />
              </div>

              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setTransferObject(null)}
                >
                  Cancelar
                </Button>
                <Button type="submit" disabled={submitting}>
                  {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  Assinar e Transferir
                </Button>
              </DialogFooter>
            </form>
          )}
        </DialogContent>
      </Dialog>

      {/* Modal: Aceite Técnico Operacional */}
      <Dialog
        open={Boolean(acceptanceObject)}
        onOpenChange={(open) => !open && setAcceptanceObject(null)}
      >
        <DialogContent className="max-w-md">
          {acceptanceObject && (
            <form onSubmit={handleAcceptCustodyObject} className="space-y-4">
              <DialogHeader>
                <DialogTitle>Aceite Técnico e Entrada Operacional</DialogTitle>
                <DialogDescription>
                  Conclui a fase pré-amostra do objeto {acceptanceObject.object_code}{" "}
                  e gera a amostra oficial no inventário analítico. Requer assinatura
                  eletrônica.
                </DialogDescription>
              </DialogHeader>

              <div className="space-y-1">
                <Label htmlFor="acc-loc">Localização de Armazenamento Final *</Label>
                <Input
                  id="acc-loc"
                  required
                  value={acceptanceLocation}
                  onChange={(e) => setAcceptanceLocation(e.target.value)}
                />
              </div>

              <div className="space-y-1">
                <Label htmlFor="acc-notes">Notas / Observações Finais</Label>
                <Textarea
                  id="acc-notes"
                  rows={2}
                  placeholder="Observações complementares de aceite técnico..."
                  value={acceptanceNotes}
                  onChange={(e) => setAcceptanceNotes(e.target.value)}
                />
              </div>

              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setAcceptanceObject(null)}
                >
                  Cancelar
                </Button>
                <Button type="submit" disabled={submitting}>
                  {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  Assinar e Efetivar Aceite
                </Button>
              </DialogFooter>
            </form>
          )}
        </DialogContent>
      </Dialog>

      {/* Modal: Histórico de Custódia (Trilha Append-Only) */}
      <Dialog
        open={Boolean(historyObject)}
        onOpenChange={(open) => !open && setHistoryObject(null)}
      >
        <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
          {historyObject && (
            <div className="space-y-4">
              <DialogHeader>
                <DialogTitle>Trilha de Custódia — {historyObject.object_code}</DialogTitle>
                <DialogDescription>
                  Eventos auditáveis e imutáveis registrados para esta pré-amostra.
                </DialogDescription>
              </DialogHeader>

              {loadingHistory ? (
                <div className="flex h-32 items-center justify-center">
                  <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                </div>
              ) : !historyEvents.length ? (
                <p className="text-xs text-muted-foreground py-6 text-center">
                  Nenhum evento registrado ainda.
                </p>
              ) : (
                <div className="relative border-l-2 border-border ml-3 pl-4 space-y-4 text-xs">
                  {historyEvents.map((ev) => (
                    <div key={ev.id} className="relative">
                      <div className="absolute -left-[23px] top-1 h-3 w-3 rounded-full bg-primary" />
                      <div className="font-semibold text-foreground">
                        {ev.event_type} — {formatDateTime(ev.effective_at)}
                      </div>
                      <div className="text-muted-foreground mt-0.5">
                        {ev.reason}
                      </div>
                      <div className="text-[11px] text-muted-foreground mt-0.5">
                        De: {ev.from_custodian?.full_name || "Protocolo"} (
                        {ev.from_location || "—"}) → Para:{" "}
                        {ev.to_custodian?.full_name || "—"} ({ev.to_location || "—"})
                      </div>
                      <div className="text-[10px] text-muted-foreground font-mono mt-0.5">
                        Registrado por: {ev.registered_by?.full_name}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
