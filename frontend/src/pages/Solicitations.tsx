import * as React from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowRight,
  CheckCircle2,
  FileText,
  Loader2,
  PackageOpen,
  Plus,
  RefreshCw,
  Search,
  Trash2,
  XCircle,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

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
import { api, ApiError } from "@/lib/api";
import type { Page, Solicitation } from "@/lib/types";
import { formatDate, formatDateTime } from "@/lib/utils";

interface ItemRowInput {
  product_name: string;
  category: string;
  manufacturer: string;
  model: string;
  serial_number: string;
  lot_number: string;
  declared_quantity: number;
  unit_of_measure: string;
  notes: string;
}

const DEFAULT_ITEM: ItemRowInput = {
  product_name: "",
  category: "DISPOSITIVO_MEDICO",
  manufacturer: "",
  model: "",
  serial_number: "",
  lot_number: "",
  declared_quantity: 1,
  unit_of_measure: "UN",
  notes: "",
};

export function SolicitationsPage() {
  const { user } = useAuth();
  const { push } = useToast();
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  const [search, setSearch] = React.useState("");
  const [statusFilter, setStatusFilter] = React.useState<string>("ALL");
  const [page, setPage] = React.useState(1);

  // Modais
  const [createOpen, setCreateOpen] = React.useState(false);
  const [detailItem, setDetailItem] = React.useState<Solicitation | null>(null);
  const [cancelModalOpen, setCancelModalOpen] = React.useState(false);
  const [cancelReason, setCancelReason] = React.useState("");
  const [submitting, setSubmitting] = React.useState(false);

  // Form de criação
  const [requesterName, setRequesterName] = React.useState("");
  const [requesterEmail, setRequesterEmail] = React.useState("");
  const [requesterDocument, setRequesterDocument] = React.useState("");
  const [requesterOrganization, setRequesterOrganization] = React.useState(
    "Gerência-Geral de Tecnologia em Serviços de Saúde (GGTES/Anvisa)",
  );
  const [purpose, setPurpose] = React.useState("");
  const [requestType, setRequestType] = React.useState("FISCALIZACAO");
  const [priority, setPriority] = React.useState("NORMAL");
  const [items, setItems] = React.useState<ItemRowInput[]>([{ ...DEFAULT_ITEM }]);

  const { data, isLoading, isFetching, refetch } = useQuery<Page<Solicitation>>({
    queryKey: ["solicitations", statusFilter, search, page],
    queryFn: () => {
      const params = new URLSearchParams();
      if (statusFilter !== "ALL") params.append("status", statusFilter);
      if (search.trim()) params.append("search", search.trim());
      params.append("page", String(page));
      params.append("size", "15");
      return api.get<Page<Solicitation>>(`/solicitations?${params.toString()}`);
    },
  });

  const canEdit =
    user?.role === "ADMIN" || user?.role === "FISCAL" || user?.role === "TECNICO";

  function handleAddItem() {
    setItems((prev) => [...prev, { ...DEFAULT_ITEM }]);
  }

  function handleRemoveItem(index: number) {
    if (items.length <= 1) {
      push({
        title: "Atenção",
        description: "A solicitação deve conter pelo menos 1 item.",
        variant: "warning",
      });
      return;
    }
    setItems((prev) => prev.filter((_, i) => i !== index));
  }

  function handleItemChange(
    index: number,
    field: keyof ItemRowInput,
    value: string | number,
  ) {
    setItems((prev) =>
      prev.map((item, i) => (i === index ? { ...item, [field]: value } : item)),
    );
  }

  function resetCreateForm() {
    setRequesterName("");
    setRequesterEmail("");
    setRequesterDocument("");
    setPurpose("");
    setRequestType("FISCALIZACAO");
    setPriority("NORMAL");
    setItems([{ ...DEFAULT_ITEM }]);
  }

  async function handleCreateSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!requesterName.trim()) {
      push({
        title: "Campo obrigatório",
        description: "Informe o nome do solicitante.",
        variant: "warning",
      });
      return;
    }

    for (let i = 0; i < items.length; i++) {
      if (!items[i].product_name.trim()) {
        push({
          title: "Item incompleto",
          description: `Informe o nome do produto no item #${i + 1}.`,
          variant: "warning",
        });
        return;
      }
    }

    try {
      setSubmitting(true);
      const payload = {
        requester_name: requesterName.trim(),
        requester_email: requesterEmail.trim() || null,
        requester_document: requesterDocument.trim() || null,
        requester_organization: requesterOrganization.trim() || null,
        purpose: purpose.trim() || null,
        request_type: requestType,
        priority,
        items: items.map((it) => ({
          product_name: it.product_name.trim(),
          category: it.category.trim() || null,
          manufacturer: it.manufacturer.trim() || null,
          model: it.model.trim() || null,
          serial_number: it.serial_number.trim() || null,
          lot_number: it.lot_number.trim() || null,
          declared_quantity: Number(it.declared_quantity) || 1,
          unit_of_measure: it.unit_of_measure.trim() || "UN",
          notes: it.notes.trim() || null,
        })),
      };

      const created = await api.post<Solicitation>("/solicitations", payload);
      push({
        title: "Solicitação cadastrada",
        description: `Demanda ${created.solicitation_number} criada com sucesso em Rascunho.`,
        variant: "success",
      });
      setCreateOpen(false);
      resetCreateForm();
      await queryClient.invalidateQueries({ queryKey: ["solicitations"] });
      setDetailItem(created);
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Erro ao criar solicitação.";
      push({ title: "Falha na criação", description: msg, variant: "destructive" });
    } finally {
      setSubmitting(false);
    }
  }

  async function handleSubmitSolicitation(solicitation: Solicitation) {
    try {
      setSubmitting(true);
      const updated = await api.post<Solicitation>(
        `/solicitations/${solicitation.id}/submit`,
        {
          version: solicitation.version,
          notes: "Submetido para conferência física de recebimento.",
        },
      );
      push({
        title: "Solicitação submetida",
        description: `A solicitação ${updated.solicitation_number} foi submetida e aguarda chegada física.`,
        variant: "success",
      });
      setDetailItem(updated);
      await queryClient.invalidateQueries({ queryKey: ["solicitations"] });
    } catch (err) {
      const msg =
        err instanceof ApiError ? err.message : "Erro ao submeter solicitação.";
      push({ title: "Falha no envio", description: msg, variant: "destructive" });
    } finally {
      setSubmitting(false);
    }
  }

  async function handleCancelSolicitation() {
    if (!detailItem) return;
    if (!cancelReason.trim()) {
      push({
        title: "Motivo obrigatório",
        description: "Informe a justificativa do cancelamento.",
        variant: "warning",
      });
      return;
    }

    try {
      setSubmitting(true);
      const params = new URLSearchParams({
        reason: cancelReason.trim(),
        version: String(detailItem.version),
      });
      const cancelled = await api.post<Solicitation>(
        `/solicitations/${detailItem.id}/cancel?${params.toString()}`,
      );
      push({
        title: "Solicitação cancelada",
        description: `Demanda ${cancelled.solicitation_number} cancelada.`,
        variant: "success",
      });
      setCancelModalOpen(false);
      setCancelReason("");
      setDetailItem(cancelled);
      await queryClient.invalidateQueries({ queryKey: ["solicitations"] });
    } catch (err) {
      const msg =
        err instanceof ApiError ? err.message : "Erro ao cancelar solicitação.";
      push({ title: "Falha no cancelamento", description: msg, variant: "destructive" });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Solicitações de Fiscalização (SEFI)
          </h1>
          <p className="text-sm text-muted-foreground">
            Cadastro de demandas formais, especificação de itens e controle de
            submissão regulatória.
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
          {canEdit && (
            <Button size="sm" onClick={() => setCreateOpen(true)}>
              <Plus className="mr-2 h-4 w-4" />
              Nova Solicitação
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
                placeholder="Buscar por código (ex: SOL-2026-00001) ou solicitante…"
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
                  <SelectItem value="SUBMITTED">Submetida</SelectItem>
                  <SelectItem value="CANCELLED">Cancelada</SelectItem>
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
              <CardTitle className="text-lg">Processos Cadastrados</CardTitle>
              <CardDescription>
                {data?.total ?? 0} solicitação(ões) encontrada(s)
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex h-48 items-center justify-center">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : !data?.items.length ? (
            <div className="flex flex-col items-center justify-center py-12 text-center text-muted-foreground">
              <FileText className="h-10 w-10 text-muted-foreground/60 mb-3" />
              <p className="text-sm font-medium">Nenhuma solicitação encontrada.</p>
              <p className="text-xs">
                Crie uma nova solicitação para iniciar o fluxo regulatório de
                pós-mercado.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-muted/50 text-xs uppercase text-muted-foreground">
                  <tr>
                    <th className="px-4 py-3 font-semibold">Código</th>
                    <th className="px-4 py-3 font-semibold">Solicitante</th>
                    <th className="px-4 py-3 font-semibold">Finalidade / Tipo</th>
                    <th className="px-4 py-3 font-semibold text-center">Itens</th>
                    <th className="px-4 py-3 font-semibold">Status</th>
                    <th className="px-4 py-3 font-semibold">Recebimento</th>
                    <th className="px-4 py-3 font-semibold">Data</th>
                    <th className="px-4 py-3 font-semibold text-right">Ação</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {data.items.map((item) => (
                    <tr
                      key={item.id}
                      className="hover:bg-muted/30 transition-colors cursor-pointer"
                      onClick={() => setDetailItem(item)}
                    >
                      <td className="px-4 py-3 font-semibold font-mono text-primary">
                        {item.solicitation_number}
                      </td>
                      <td className="px-4 py-3">
                        <div className="font-medium text-foreground">
                          {item.requester_name}
                        </div>
                        <div className="text-xs text-muted-foreground truncate max-w-xs">
                          {item.requester_organization || "—"}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-xs font-semibold px-2 py-0.5 rounded bg-muted">
                          {item.request_type}
                        </span>
                        <div className="text-xs text-muted-foreground truncate max-w-xs mt-0.5">
                          {item.purpose || "Sem finalidade especificada"}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className="inline-flex items-center justify-center rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-800">
                          {item.items.length}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <StatusBadge status={item.status} kind="solicitation" />
                      </td>
                      <td className="px-4 py-3">
                        {item.has_receipt ? (
                          <span className="inline-flex items-center gap-1 text-xs font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                            <CheckCircle2 className="h-3 w-3" />
                            Recebimento Vinculado
                          </span>
                        ) : item.status === "SUBMITTED" ? (
                          <span className="inline-flex items-center gap-1 text-xs font-medium text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200">
                            Aguardando Chegada
                          </span>
                        ) : (
                          <span className="text-xs text-muted-foreground">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-xs text-muted-foreground whitespace-nowrap">
                        {formatDate(item.created_at)}
                      </td>
                      <td
                        className="px-4 py-3 text-right"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setDetailItem(item)}
                        >
                          Detalhes
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

      {/* Modal: Detalhes da Solicitação */}
      <Dialog
        open={Boolean(detailItem)}
        onOpenChange={(open) => !open && setDetailItem(null)}
      >
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          {detailItem && (
            <div className="space-y-6">
              <DialogHeader>
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <DialogTitle className="text-xl font-bold font-mono">
                      {detailItem.solicitation_number}
                    </DialogTitle>
                    <DialogDescription>
                      Cadastrado em {formatDateTime(detailItem.created_at)} · Versão{" "}
                      {detailItem.version}
                    </DialogDescription>
                  </div>
                  <StatusBadge
                    status={detailItem.status}
                    kind="solicitation"
                    className="text-xs"
                  />
                </div>
              </DialogHeader>

              {/* Solicitante e Demanda */}
              <div className="grid grid-cols-2 gap-4 rounded-lg border p-4 bg-muted/20 text-sm">
                <div>
                  <span className="text-xs text-muted-foreground">Solicitante:</span>
                  <p className="font-semibold">{detailItem.requester_name}</p>
                  <p className="text-xs text-muted-foreground">
                    {detailItem.requester_email || "Sem e-mail informado"} ·{" "}
                    {detailItem.requester_document || "Sem documento"}
                  </p>
                </div>
                <div>
                  <span className="text-xs text-muted-foreground">
                    Órgão / Unidade:
                  </span>
                  <p className="font-medium">
                    {detailItem.requester_organization || "—"}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Tipo: {detailItem.request_type} · Prioridade:{" "}
                    {detailItem.priority}
                  </p>
                </div>
                <div className="col-span-2">
                  <span className="text-xs text-muted-foreground">
                    Finalidade / Motivação:
                  </span>
                  <p className="text-sm mt-0.5">
                    {detailItem.purpose || "Nenhuma observação informada."}
                  </p>
                </div>
              </div>

              {/* Tabela de Itens Declarados */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <h4 className="text-sm font-semibold text-foreground">
                    Itens e Dispositivos Declarados ({detailItem.items.length})
                  </h4>
                </div>
                <div className="rounded-md border overflow-hidden">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-muted font-semibold text-muted-foreground uppercase">
                      <tr>
                        <th className="px-3 py-2">#</th>
                        <th className="px-3 py-2">Dispositivo / Produto</th>
                        <th className="px-3 py-2">Fabricante / Modelo</th>
                        <th className="px-3 py-2">Série / Lote</th>
                        <th className="px-3 py-2 text-right">Qtd. Declarada</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                      {detailItem.items.map((it) => (
                        <tr key={it.id}>
                          <td className="px-3 py-2 font-mono text-muted-foreground">
                            {it.item_number}
                          </td>
                          <td className="px-3 py-2 font-medium text-foreground">
                            {it.product_name}
                            {it.category && (
                              <span className="ml-1 text-[10px] text-muted-foreground">
                                ({it.category})
                              </span>
                            )}
                          </td>
                          <td className="px-3 py-2 text-muted-foreground">
                            {it.manufacturer || "—"} / {it.model || "—"}
                          </td>
                          <td className="px-3 py-2 font-mono text-muted-foreground">
                            {it.serial_number ? `S/N: ${it.serial_number}` : ""}
                            {it.lot_number ? ` Lote: ${it.lot_number}` : ""}
                            {!it.serial_number && !it.lot_number ? "—" : ""}
                          </td>
                          <td className="px-3 py-2 text-right font-semibold">
                            {it.declared_quantity} {it.unit_of_measure}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Status Actions */}
              <div className="border-t pt-4">
                {detailItem.status === "DRAFT" && canEdit && (
                  <div className="flex items-center justify-between gap-2">
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => setCancelModalOpen(true)}
                      disabled={submitting}
                    >
                      <XCircle className="mr-2 h-4 w-4" />
                      Cancelar Solicitação
                    </Button>
                    <Button
                      size="sm"
                      onClick={() => handleSubmitSolicitation(detailItem)}
                      disabled={submitting}
                    >
                      {submitting ? (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      ) : (
                        <CheckCircle2 className="mr-2 h-4 w-4" />
                      )}
                      Submeter para Recebimento
                    </Button>
                  </div>
                )}

                {detailItem.status === "SUBMITTED" && (
                  <div className="rounded-lg border border-sky-200 bg-sky-50/50 p-4 flex flex-col sm:flex-row items-center justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <PackageOpen className="h-6 w-6 text-sky-700 shrink-0" />
                      <div>
                        <p className="text-sm font-semibold text-sky-950">
                          {detailItem.has_receipt
                            ? "Recebimento físico formalizado"
                            : "Solicitação submetida e aguardando chegada física"}
                        </p>
                        <p className="text-xs text-sky-800">
                          {detailItem.has_receipt
                            ? "Os objetos de pré-amostra já foram gerados e estão sob controle de custódia."
                            : "Formalize o recebimento no setor de protocolo assim que as caixas chegarem."}
                        </p>
                      </div>
                    </div>
                    {canEdit && (
                      <Button
                        size="sm"
                        className="shrink-0"
                        onClick={() => {
                          setDetailItem(null);
                          navigate(`/receipts?solicitation=${detailItem.id}`);
                        }}
                      >
                        {detailItem.has_receipt ? "Ver Recebimento" : "Formalizar Recebimento"}
                        <ArrowRight className="ml-2 h-4 w-4" />
                      </Button>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Modal: Nova Solicitação */}
      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Nova Solicitação de Fiscalização</DialogTitle>
            <DialogDescription>
              Cadastre os dados da demanda e a lista de dispositivos sob vigilância
              sanitária.
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleCreateSubmit} className="space-y-5">
            {/* Dados do Solicitante */}
            <div className="space-y-3">
              <h4 className="text-xs font-semibold uppercase text-muted-foreground">
                Dados do Solicitante
              </h4>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <Label htmlFor="req-name">Nome do Solicitante *</Label>
                  <Input
                    id="req-name"
                    required
                    placeholder="Ex: Dra. Mariana Costa"
                    value={requesterName}
                    onChange={(e) => setRequesterName(e.target.value)}
                  />
                </div>
                <div className="space-y-1">
                  <Label htmlFor="req-email">E-mail</Label>
                  <Input
                    id="req-email"
                    type="email"
                    placeholder="fiscal@anvisa.gov.br"
                    value={requesterEmail}
                    onChange={(e) => setRequesterEmail(e.target.value)}
                  />
                </div>
                <div className="space-y-1">
                  <Label htmlFor="req-doc">Documento / Matrícula</Label>
                  <Input
                    id="req-doc"
                    placeholder="SIAPE ou CPF"
                    value={requesterDocument}
                    onChange={(e) => setRequesterDocument(e.target.value)}
                  />
                </div>
                <div className="space-y-1">
                  <Label htmlFor="req-org">Órgão / Gerência</Label>
                  <Input
                    id="req-org"
                    value={requesterOrganization}
                    onChange={(e) => setRequesterOrganization(e.target.value)}
                  />
                </div>
              </div>
            </div>

            {/* Demanda */}
            <div className="space-y-3 border-t pt-3">
              <h4 className="text-xs font-semibold uppercase text-muted-foreground">
                Dados da Demanda
              </h4>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <Label>Tipo de Solicitação</Label>
                  <Select value={requestType} onValueChange={setRequestType}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="FISCALIZACAO">
                        Fiscalização Pós-Mercado
                      </SelectItem>
                      <SelectItem value="INVESTIGACAO_QUEIXA">
                        Investigação de Queixa Técnica
                      </SelectItem>
                      <SelectItem value="MONITORAMENTO">
                        Programa de Monitoramento
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1">
                  <Label>Prioridade</Label>
                  <Select value={priority} onValueChange={setPriority}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="NORMAL">Normal</SelectItem>
                      <SelectItem value="ALTA">Alta</SelectItem>
                      <SelectItem value="URGENTE">Urgente</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="space-y-1">
                <Label htmlFor="req-purpose">Finalidade / Motivo da Solicitação</Label>
                <Textarea
                  id="req-purpose"
                  rows={2}
                  placeholder="Ex: Verificação de conformidade em atendimento ao termo de apreensão fiscal..."
                  value={purpose}
                  onChange={(e) => setPurpose(e.target.value)}
                />
              </div>
            </div>

            {/* Itens Declarados */}
            <div className="space-y-3 border-t pt-3">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-semibold uppercase text-muted-foreground">
                  Itens e Amostras Declaradas ({items.length})
                </h4>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={handleAddItem}
                >
                  <Plus className="mr-1.5 h-3.5 w-3.5" />
                  Adicionar Item
                </Button>
              </div>

              <div className="space-y-3">
                {items.map((it, idx) => (
                  <div
                    key={idx}
                    className="p-3 border rounded-lg bg-muted/10 space-y-2 relative"
                  >
                    <div className="flex items-center justify-between pb-1 border-b">
                      <span className="text-xs font-bold text-foreground">
                        Item #{idx + 1}
                      </span>
                      {items.length > 1 && (
                        <button
                          type="button"
                          onClick={() => handleRemoveItem(idx)}
                          className="text-muted-foreground hover:text-rose-600 transition-colors"
                          title="Remover item"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                    <div className="grid grid-cols-3 gap-2 text-xs">
                      <div className="col-span-2 space-y-1">
                        <Label className="text-[11px]">Nome do Produto *</Label>
                        <Input
                          required
                          placeholder="Ex: Eletrocardiógrafo Portátil CardioX"
                          value={it.product_name}
                          onChange={(e) =>
                            handleItemChange(idx, "product_name", e.target.value)
                          }
                        />
                      </div>
                      <div className="space-y-1">
                        <Label className="text-[11px]">Fabricante</Label>
                        <Input
                          placeholder="Ex: MedTech Brasil"
                          value={it.manufacturer}
                          onChange={(e) =>
                            handleItemChange(idx, "manufacturer", e.target.value)
                          }
                        />
                      </div>
                      <div className="space-y-1">
                        <Label className="text-[11px]">Modelo</Label>
                        <Input
                          placeholder="Ex: ECG-100"
                          value={it.model}
                          onChange={(e) =>
                            handleItemChange(idx, "model", e.target.value)
                          }
                        />
                      </div>
                      <div className="space-y-1">
                        <Label className="text-[11px]">Nº de Série</Label>
                        <Input
                          placeholder="Ex: SN-2026-99"
                          value={it.serial_number}
                          onChange={(e) =>
                            handleItemChange(idx, "serial_number", e.target.value)
                          }
                        />
                      </div>
                      <div className="space-y-1">
                        <Label className="text-[11px]">Lote</Label>
                        <Input
                          placeholder="Ex: LOTE-88"
                          value={it.lot_number}
                          onChange={(e) =>
                            handleItemChange(idx, "lot_number", e.target.value)
                          }
                        />
                      </div>
                      <div className="space-y-1">
                        <Label className="text-[11px]">Qtd. Declarada *</Label>
                        <Input
                          type="number"
                          min="1"
                          required
                          value={it.declared_quantity}
                          onChange={(e) =>
                            handleItemChange(
                              idx,
                              "declared_quantity",
                              Number(e.target.value),
                            )
                          }
                        />
                      </div>
                      <div className="space-y-1">
                        <Label className="text-[11px]">Unidade</Label>
                        <Input
                          value={it.unit_of_measure}
                          onChange={(e) =>
                            handleItemChange(idx, "unit_of_measure", e.target.value)
                          }
                        />
                      </div>
                      <div className="space-y-1">
                        <Label className="text-[11px]">Notas / Embalagem</Label>
                        <Input
                          placeholder="Ex: Caixa lacrada com termo"
                          value={it.notes}
                          onChange={(e) =>
                            handleItemChange(idx, "notes", e.target.value)
                          }
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setCreateOpen(false)}
              >
                Cancelar
              </Button>
              <Button type="submit" disabled={submitting}>
                {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Salvar Rascunho
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Modal: Cancelar Solicitação */}
      <Dialog open={cancelModalOpen} onOpenChange={setCancelModalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Cancelar Solicitação</DialogTitle>
            <DialogDescription>
              Informe o motivo regulatório para o cancelamento definitivo da
              demanda.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <Label htmlFor="cancel-reason">Justificativa do Cancelamento *</Label>
            <Textarea
              id="cancel-reason"
              rows={3}
              placeholder="Ex: Processo arquivado pelo órgão de origem conforme ofício..."
              value={cancelReason}
              onChange={(e) => setCancelReason(e.target.value)}
            />
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setCancelModalOpen(false)}
              disabled={submitting}
            >
              Voltar
            </Button>
            <Button
              variant="destructive"
              onClick={handleCancelSolicitation}
              disabled={submitting || cancelReason.trim().length < 5}
            >
              {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Confirmar Cancelamento
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
