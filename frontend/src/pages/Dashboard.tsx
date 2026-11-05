import * as React from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertOctagon,
  ArrowLeftRight,
  ArrowRight,
  CheckCircle2,
  ClipboardList,
  Download,
  FileCheck2,
  FlaskConical,
  Loader2,
  MapPin,
  PackageOpen,
  Plus,
  QrCode,
  RefreshCw,
  RotateCcw,
  ShieldCheck,
  UserCheck,
} from "lucide-react";
import { useForm } from "react-hook-form";
import { Link } from "react-router-dom";
import { z } from "zod";

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
import { api, ApiError, fetchObjectUrl } from "@/lib/api";
import type {
  DeviceSample,
  Page,
  TimelineEvent,
  UserBrief,
} from "@/lib/types";
import {
  dayKey,
  dayLabel,
  formatDateTime,
  formatTime,
  initials,
  relativeTime,
  shortHash,
} from "@/lib/utils";
import { cn } from "@/lib/utils";

const sampleSchema = z.object({
  commercial_name: z.string().min(3, "Informe o nome comercial do dispositivo."),
  manufacturer: z.string().min(2, "Informe o fabricante."),
  serial_number: z.string().min(1, "Número de série é obrigatório."),
  lot_number: z.string().min(1, "Lote é obrigatório."),
  registration_number: z.string().optional(),
  model: z.string().optional(),
  storage_location: z.string().min(1, "Informe a localização física."),
  description: z.string().optional(),
});

type SampleFormValues = z.infer<typeof sampleSchema>;

interface CreateSampleResponse {
  sample: DeviceSample;
  audit_log_id: number;
  signature_id: string;
  qr_code_url: string;
}

const TIMELINE_STYLES: Record<
  TimelineEvent["type"],
  { icon: React.ComponentType<{ className?: string }>; tone: string; label: string }
> = {
  RECEIPT: {
    icon: PackageOpen,
    tone: "border-sky-200 bg-sky-50 text-sky-700",
    label: "Entrada",
  },
  CUSTODY: {
    icon: UserCheck,
    tone: "border-teal-200 bg-teal-50 text-teal-700",
    label: "Custódia",
  },
  TEST_CREATED: {
    icon: FlaskConical,
    tone: "border-indigo-200 bg-indigo-50 text-indigo-700",
    label: "Ensaio",
  },
  TEST_SIGNED: {
    icon: FileCheck2,
    tone: "border-emerald-200 bg-emerald-50 text-emerald-700",
    label: "Laudo",
  },
  CAPA_OPENED: {
    icon: AlertOctagon,
    tone: "border-rose-200 bg-rose-50 text-rose-700",
    label: "CAPA",
  },
  STATUS_CHANGE: {
    icon: RefreshCw,
    tone: "border-slate-200 bg-slate-100 text-slate-600",
    label: "Status",
  },
};

export function DashboardPage() {
  const queryClient = useQueryClient();
  const { push } = useToast();
  const { requestSignature } = useESignature();
  const { user } = useAuth();

  const [selectedId, setSelectedId] = React.useState<string | null>(null);
  const [transferOpen, setTransferOpen] = React.useState(false);
  const [submitting, setSubmitting] = React.useState(false);
  const [reopening, setReopening] = React.useState(false);

  const canCreate =
    user?.role === "ADMIN" || user?.role === "FISCAL" || user?.role === "TECNICO";

  const samplesQuery = useQuery({
    queryKey: ["samples", "recent"],
    queryFn: () => api.get<Page<DeviceSample>>("/samples?size=50"),
  });

  const samples = samplesQuery.data?.items ?? [];

  React.useEffect(() => {
    if (!selectedId && samples.length > 0) {
      setSelectedId(samples[0].id);
    }
  }, [samples, selectedId]);

  const selected = samples.find((sample) => sample.id === selectedId) ?? null;
  const canTransfer = Boolean(
    selected &&
      selected.status !== "DESCARTADO" &&
      user?.role !== "AUDITOR" &&
      (selected.current_custodian?.id == null ||
        selected.current_custodian.id === user?.id ||
        user?.role === "ADMIN" ||
        user?.role === "FISCAL"),
  );

  // Reabrir uma amostra aprovada é um ato assinado: devolve o status para
  // EM_TESTE antes de programar um reteste (evita rebaixamento silencioso).
  const canReopen = Boolean(
    selected &&
      selected.status === "APROVADO" &&
      (user?.role === "ADMIN" ||
        user?.role === "FISCAL" ||
        user?.role === "TECNICO"),
  );

  const REOPEN_REASON =
    "Reabertura da amostra para reteste em vigilância pós-mercado.";

  const timelineQuery = useQuery({
    queryKey: ["timeline", selectedId],
    queryFn: () => api.get<TimelineEvent[]>(`/samples/${selectedId}/timeline`),
    enabled: Boolean(selectedId),
  });

  const form = useForm<SampleFormValues>({
    resolver: zodResolver(sampleSchema),
    defaultValues: {
      commercial_name: "",
      manufacturer: "",
      serial_number: "",
      lot_number: "",
      registration_number: "",
      model: "",
      storage_location: "",
      description: "",
    },
  });

  const timeline = timelineQuery.data ?? [];
  const grouped = React.useMemo(() => {
    const groups = new Map<string, { label: string; items: TimelineEvent[] }>();
    for (const event of timeline) {
      const key = dayKey(event.occurred_at);
      if (!groups.has(key)) {
        groups.set(key, { label: dayLabel(event.occurred_at), items: [] });
      }
      groups.get(key)!.items.push(event);
    }
    return Array.from(groups.values());
  }, [timeline]);

  async function handleCreate(values: SampleFormValues) {
    const id = crypto.randomUUID();
    const token = await requestSignature({
      entityType: "DeviceSample",
      entityId: id,
      action: "CREATE",
      meaning: "AUTORIA",
      title: "Registrar entrada da amostra",
      recordLabel: `${values.commercial_name} · lote ${values.lot_number}`,
      suggestedReason: `Registro de entrada da amostra ${values.commercial_name}, lote ${values.lot_number}, recebida para fiscalização pós-mercado.`,
    });
    if (!token) return;

    setSubmitting(true);
    try {
      const response = await api.post<CreateSampleResponse>(
        "/samples",
        {
          id,
          commercial_name: values.commercial_name.trim(),
          manufacturer: values.manufacturer.trim(),
          serial_number: values.serial_number.trim(),
          lot_number: values.lot_number.trim(),
          registration_number: values.registration_number?.trim() || null,
          model: values.model?.trim() || null,
          storage_location: values.storage_location.trim(),
          description: values.description?.trim() || null,
        },
        token,
      );

      await queryClient.invalidateQueries({ queryKey: ["samples"] });
      setSelectedId(response.sample.id);
      form.reset();
      push({
        variant: "success",
        title: "Amostra registrada",
        description: `Accession ${response.sample.accession_number} gerado e assinado.`,
      });
    } catch (error) {
      push({
        variant: "destructive",
        title: "Não foi possível registrar",
        description:
          error instanceof ApiError ? error.message : "Verifique os dados e tente novamente.",
      });
    } finally {
      setSubmitting(false);
    }
  }

  async function handleReopen() {
    if (!selected) return;

    const token = await requestSignature({
      entityType: "DeviceSample",
      entityId: selected.id,
      action: "UPDATE",
      meaning: "REVISAO",
      title: "Reabrir amostra para reteste",
      recordLabel: `${selected.accession_number} · ${selected.commercial_name}`,
      suggestedReason: REOPEN_REASON,
    });
    if (!token) return;

    setReopening(true);
    try {
      await api.patch(
        `/samples/${selected.id}/status`,
        { status: "EM_TESTE", reason: REOPEN_REASON, version: selected.version },
        token,
      );
      await queryClient.invalidateQueries({ queryKey: ["samples"] });
      void queryClient.invalidateQueries({ queryKey: ["timeline", selected.id] });
      push({
        variant: "success",
        title: "Amostra reaberta para reteste",
        description: "Status Em teste — já é possível programar um novo ensaio.",
      });
    } catch (error) {
      push({
        variant: "destructive",
        title: "Não foi possível reabrir",
        description:
          error instanceof ApiError ? error.message : "Recarregue e tente novamente.",
      });
    } finally {
      setReopening(false);
    }
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(400px,460px)_1fr]">
      <Card className="h-fit xl:sticky xl:top-24">
        <CardHeader>
          <div className="flex items-center gap-2 text-primary">
            <span className="flex h-8 w-8 items-center justify-center rounded-md bg-primary/10">
              <Plus className="h-4 w-4" />
            </span>
            <span className="text-[11px] font-semibold uppercase tracking-[0.16em]">
              Nova entrada
            </span>
          </div>
          <CardTitle>Dispositivo médico recebido</CardTitle>
          <CardDescription>
            O registro gera um número de accession e um QR Code assinado. A gravação
            exige assinatura eletrônica.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {canCreate ? (
            <form
              onSubmit={form.handleSubmit(handleCreate)}
              className="grid gap-4"
              noValidate
            >
              <div className="grid gap-1.5">
                <Label htmlFor="commercial_name">Nome comercial *</Label>
                <Input
                  id="commercial_name"
                  placeholder="Ex.: Monitor de Sinais Vitais VitalOne 5"
                  {...form.register("commercial_name")}
                />
                <FieldError message={form.formState.errors.commercial_name?.message} />
              </div>

              <div className="grid gap-1.5">
                <Label htmlFor="manufacturer">Fabricante *</Label>
                <Input
                  id="manufacturer"
                  placeholder="Razão social do fabricante"
                  {...form.register("manufacturer")}
                />
                <FieldError message={form.formState.errors.manufacturer?.message} />
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="grid gap-1.5">
                  <Label htmlFor="lot_number">Lote *</Label>
                  <Input
                    id="lot_number"
                    placeholder="L2026-041"
                    className="font-mono"
                    {...form.register("lot_number")}
                  />
                  <FieldError message={form.formState.errors.lot_number?.message} />
                </div>
                <div className="grid gap-1.5">
                  <Label htmlFor="serial_number">Número de série *</Label>
                  <Input
                    id="serial_number"
                    placeholder="SN-000000"
                    className="font-mono"
                    {...form.register("serial_number")}
                  />
                  <FieldError message={form.formState.errors.serial_number?.message} />
                </div>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="grid gap-1.5">
                  <Label htmlFor="model">Modelo</Label>
                  <Input id="model" placeholder="Opcional" {...form.register("model")} />
                </div>
                <div className="grid gap-1.5">
                  <Label htmlFor="registration_number">Registro ANVISA</Label>
                  <Input
                    id="registration_number"
                    placeholder="80012345678"
                    className="font-mono"
                    {...form.register("registration_number")}
                  />
                </div>
              </div>

              <div className="grid gap-1.5">
                <Label htmlFor="storage_location">Localização física *</Label>
                <Input
                  id="storage_location"
                  placeholder="Ex.: Prateleira B3 — Sala de amostras"
                  {...form.register("storage_location")}
                />
                <FieldError message={form.formState.errors.storage_location?.message} />
              </div>

              <div className="grid gap-1.5">
                <Label htmlFor="description">Observações da apreensão</Label>
                <Textarea
                  id="description"
                  rows={3}
                  placeholder="Contexto da coleta, suspeita, condições do lacre…"
                  {...form.register("description")}
                />
              </div>

              <Button type="submit" className="mt-1 w-full" disabled={submitting}>
                {submitting ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <ShieldCheck className="h-4 w-4" />
                )}
                Registrar e assinar entrada
              </Button>
              <p className="text-center text-[11px] leading-relaxed text-muted-foreground">
                Você será solicitado a reautenticar. A assinatura é vinculada a este
                registro e não pode ser reutilizada.
              </p>
            </form>
          ) : (
            <div className="rounded-md border border-dashed border-border bg-muted/30 p-6 text-center">
              <p className="text-sm font-medium">Perfil somente leitura</p>
              <p className="mt-1 text-[13px] text-muted-foreground">
                Seu perfil não pode registrar novas amostras.
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="min-w-0 space-y-5">
        <Card>
          <CardHeader className="gap-3 border-b border-border pb-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="min-w-0 flex-1">
                <CardTitle className="flex items-center gap-2 text-[15px]">
                  <ClipboardList className="h-4 w-4 text-primary" />
                  Amostra em foco
                </CardTitle>
                <CardDescription>
                  Selecione uma amostra para visualizar a cadeia de custódia.
                </CardDescription>
              </div>
              <div className="flex w-full items-center gap-2 sm:w-auto">
                <Select
                  value={selectedId ?? undefined}
                  onValueChange={(value) => setSelectedId(value)}
                  disabled={samples.length === 0}
                >
                  <SelectTrigger className="w-full sm:w-[320px]">
                    <SelectValue
                      placeholder={
                        samplesQuery.isPending
                          ? "Carregando amostras…"
                          : "Nenhuma amostra registrada"
                      }
                    />
                  </SelectTrigger>
                  <SelectContent>
                    {samples.map((sample) => (
                      <SelectItem key={sample.id} value={sample.id}>
                        {sample.accession_number} · {sample.commercial_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => samplesQuery.refetch()}
                  title="Atualizar lista"
                  aria-label="Atualizar lista de amostras"
                >
                  <RefreshCw
                    className={cn("h-4 w-4", samplesQuery.isFetching && "animate-spin")}
                  />
                </Button>
              </div>
            </div>
          </CardHeader>

          <CardContent className="pt-5">
            {samplesQuery.isPending ? (
              <div className="h-32 animate-pulse rounded-md bg-muted" />
            ) : selected ? (
              <div className="grid gap-5 md:grid-cols-[1fr_auto]">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="rounded bg-primary/10 px-2 py-0.5 font-mono text-xs font-semibold text-primary">
                      {selected.accession_number}
                    </span>
                    <StatusBadge status={selected.status} kind="sample" />
                    <span className="text-[11px] text-muted-foreground">
                      atualizado {relativeTime(selected.updated_at)}
                    </span>
                  </div>

                  <h2 className="mt-2 text-lg font-semibold leading-tight">
                    {selected.commercial_name}
                  </h2>
                  <p className="text-[13px] text-muted-foreground">
                    {selected.manufacturer}
                    {selected.model ? ` · ${selected.model}` : ""}
                  </p>

                  <dl className="mt-4 grid gap-x-6 gap-y-3 text-[13px] sm:grid-cols-2">
                    <Field label="Lote" value={selected.lot_number} mono />
                    <Field label="Número de série" value={selected.serial_number} mono />
                    <Field
                      label="Registro ANVISA"
                      value={selected.registration_number ?? "—"}
                      mono
                    />
                    <Field
                      label="Localização"
                      value={selected.current_location ?? "—"}
                      icon={MapPin}
                    />
                    <Field
                      label="Custodiante atual"
                      value={selected.current_custodian?.full_name ?? "Sem custódia"}
                    />
                    <Field
                      label="Recebido em"
                      value={formatDateTime(selected.received_at)}
                    />
                  </dl>

                  <div className="mt-5 flex flex-wrap gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setTransferOpen(true)}
                      disabled={!canTransfer}
                      title={
                        canTransfer
                          ? undefined
                          : "Somente o custodiante atual, a fiscalização ou a administração podem transferir a guarda."
                      }
                    >
                      <ArrowLeftRight className="h-4 w-4" />
                      Transferir custódia
                    </Button>
                    <Button variant="outline" size="sm" asChild>
                      <Link to={`/tests?sample=${selected.id}`}>
                        <FlaskConical className="h-4 w-4" />
                        Abrir ensaios
                        <ArrowRight className="h-3.5 w-3.5" />
                      </Link>
                    </Button>
                    {canReopen ? (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={handleReopen}
                        disabled={reopening}
                        title="Reabre a amostra aprovada para reteste; exige assinatura eletrônica."
                      >
                        {reopening ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <RotateCcw className="h-4 w-4" />
                        )}
                        Reabrir para reteste
                      </Button>
                    ) : null}
                  </div>
                </div>

                <SampleQr sample={selected} />
              </div>
            ) : (
              <EmptySamples />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex-row items-start justify-between gap-4 border-b border-border pb-4">
            <div>
              <CardTitle className="flex items-center gap-2 text-[15px]">
                <UserCheck className="h-4 w-4 text-primary" />
                Cadeia de custódia
              </CardTitle>
              <CardDescription>
                Quem encostou na amostra, quando, onde e com qual assinatura.
              </CardDescription>
            </div>
            <span className="rounded-full border border-border px-2 py-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
              append-only
            </span>
          </CardHeader>
          <CardContent className="pt-5">
            {!selected ? (
              <p className="text-[13px] text-muted-foreground">
                {samplesQuery.isPending
                  ? "Carregando amostras…"
                  : "Selecione uma amostra para ver a linha do tempo."}
              </p>
            ) : timelineQuery.isPending ? (
              <div className="space-y-4">
                {[0, 1, 2].map((index) => (
                  <div key={index} className="flex gap-4">
                    <div className="h-8 w-8 animate-pulse rounded-full bg-muted" />
                    <div className="flex-1 space-y-2">
                      <div className="h-3 w-1/3 animate-pulse rounded bg-muted" />
                      <div className="h-3 w-2/3 animate-pulse rounded bg-muted" />
                    </div>
                  </div>
                ))}
              </div>
            ) : timeline.length === 0 ? (
              <p className="text-[13px] text-muted-foreground">
                Nenhum evento registrado para esta amostra.
              </p>
            ) : (
              <div className="space-y-7">
                {grouped.map((group) => (
                  <section key={group.label}>
                    <p className="mb-3 text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                      {group.label}
                    </p>
                    <ol className="relative space-y-4">
                      <span
                        aria-hidden="true"
                        className="timeline-line absolute bottom-4 left-[15px] top-2 w-px"
                      />
                      {group.items.map((event) => (
                        <TimelineRow key={event.id} event={event} />
                      ))}
                    </ol>
                  </section>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {selected ? (
        <TransferDialog
          open={transferOpen}
          onOpenChange={setTransferOpen}
          sample={selected}
          onTransferred={() => {
            void queryClient.invalidateQueries({ queryKey: ["samples"] });
            void queryClient.invalidateQueries({ queryKey: ["timeline", selected.id] });
          }}
        />
      ) : null}
    </div>
  );
}

function Field({
  label,
  value,
  mono,
  icon: Icon,
}: {
  label: string;
  value: string;
  mono?: boolean;
  icon?: React.ComponentType<{ className?: string }>;
}) {
  return (
    <div>
      <dt className="data-label">{label}</dt>
      <dd
        className={cn(
          "mt-0.5 flex items-center gap-1.5 text-foreground",
          mono && "font-mono text-xs",
        )}
      >
        {Icon ? <Icon className="h-3.5 w-3.5 text-muted-foreground" /> : null}
        <span className="truncate">{value}</span>
      </dd>
    </div>
  );
}

function FieldError({ message }: { message?: string }) {
  if (!message) return null;
  return <p className="text-[11px] font-medium text-destructive">{message}</p>;
}

function TimelineRow({ event }: { event: TimelineEvent }) {
  const style = TIMELINE_STYLES[event.type];
  const Icon = style.icon;

  return (
    <li className="relative flex gap-4">
      <span
        className={cn(
          "relative z-10 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border",
          style.tone,
        )}
      >
        <Icon className="h-3.5 w-3.5" />
      </span>
      <div className="min-w-0 flex-1 rounded-md border border-border bg-background px-3.5 py-3">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <p className="text-[13px] font-medium leading-snug">{event.title}</p>
          <span className="shrink-0 font-mono text-[11px] text-muted-foreground">
            {formatTime(event.occurred_at)}
          </span>
        </div>
        {event.description ? (
          <p className="mt-1 text-[12.5px] leading-relaxed text-muted-foreground">
            {event.description}
          </p>
        ) : null}
        <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-muted-foreground">
          {event.actor_name ? (
            <span className="inline-flex items-center gap-1">
              <span className="flex h-4 w-4 items-center justify-center rounded-full bg-muted text-[8px] font-semibold text-foreground">
                {initials(event.actor_name)}
              </span>
              {event.actor_name}
            </span>
          ) : null}
          {event.location ? (
            <span className="inline-flex items-center gap-1">
              <MapPin className="h-3 w-3" />
              {event.location}
            </span>
          ) : null}
          {typeof event.metadata.signature_id === "string" ? (
            <span className="inline-flex items-center gap-1 font-mono text-[10px]">
              <ShieldCheck className="h-3 w-3 text-success" />
              assinado · {shortHash(event.metadata.signature_id, 8)}
            </span>
          ) : null}
          {typeof event.metadata.audit_hash === "string" ? (
            <span className="font-mono text-[10px]">
              hash · {shortHash(event.metadata.audit_hash, 12)}
            </span>
          ) : null}
        </div>
      </div>
    </li>
  );
}

function SampleQr({ sample }: { sample: DeviceSample }) {
  const [url, setUrl] = React.useState<string | null>(null);

  React.useEffect(() => {
    let active = true;
    let objectUrl: string | null = null;

    fetchObjectUrl(`/samples/${sample.id}/qrcode.png`)
      .then((next) => {
        if (!active) {
          URL.revokeObjectURL(next);
          return;
        }
        objectUrl = next;
        setUrl(next);
      })
      .catch(() => {
        if (active) setUrl(null);
      });

    return () => {
      active = false;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [sample.id]);

  return (
    <div className="flex flex-col items-center gap-2 rounded-md border border-border bg-muted/30 p-3">
      {url ? (
        <img
          src={url}
          alt={`QR Code da amostra ${sample.accession_number}`}
          className="h-28 w-28 rounded bg-white p-1"
        />
      ) : (
        <div className="flex h-28 w-28 items-center justify-center rounded bg-muted">
          <QrCode className="h-8 w-8 text-muted-foreground/40" />
        </div>
      )}
      <p className="text-center font-mono text-[10px] text-muted-foreground">
        {sample.accession_number}
      </p>
      {url ? (
        <a
          href={url}
          download={`${sample.accession_number}.png`}
          className="inline-flex items-center gap-1 text-[11px] font-medium text-primary hover:underline"
        >
          <Download className="h-3 w-3" />
          Baixar etiqueta
        </a>
      ) : null}
    </div>
  );
}

function EmptySamples() {
  return (
    <div className="rounded-md border border-dashed border-border bg-muted/20 px-6 py-10 text-center">
      <PackageOpen className="mx-auto h-8 w-8 text-muted-foreground/50" />
      <p className="mt-3 text-sm font-medium">Nenhuma amostra registrada</p>
      <p className="mt-1 text-[13px] text-muted-foreground">
        Utilize o formulário ao lado para registrar a primeira entrada.
      </p>
    </div>
  );
}

function TransferDialog({
  open,
  onOpenChange,
  sample,
  onTransferred,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  sample: DeviceSample;
  onTransferred: () => void;
}) {
  const { push } = useToast();
  const { requestSignature } = useESignature();
  const [toCustodian, setToCustodian] = React.useState("");
  const [reason, setReason] = React.useState("");
  const [location, setLocation] = React.useState(sample.current_location ?? "");
  const [seal, setSeal] = React.useState("");
  const [notes, setNotes] = React.useState("");
  const [submitting, setSubmitting] = React.useState(false);

  const usersQuery = useQuery({
    queryKey: ["users"],
    queryFn: () => api.get<UserBrief[]>("/users"),
    enabled: open,
  });

  React.useEffect(() => {
    if (!open) return;
    setToCustodian("");
    setReason("");
    setLocation(sample.current_location ?? "");
    setSeal("");
    setNotes("");
  }, [open, sample.current_location]);

  const eligible = (usersQuery.data ?? []).filter(
    (candidate) =>
      candidate.id !== sample.current_custodian?.id &&
      ["CUSTODIANTE", "TECNICO", "FISCAL", "ADMIN"].includes(candidate.role),
  );

  async function handleTransfer(event: React.FormEvent) {
    event.preventDefault();
    if (!toCustodian) {
      push({ variant: "warning", title: "Selecione o custodiante de destino." });
      return;
    }
    if (reason.trim().length < 10) {
      push({
        variant: "warning",
        title: "Motivo muito curto",
        description: "Descreva o motivo da transferência com ao menos 10 caracteres.",
      });
      return;
    }

    const token = await requestSignature({
      entityType: "DeviceSample",
      entityId: sample.id,
      action: "TRANSFER",
      meaning: "TRANSFERENCIA_DE_CUSTODIA",
      title: "Assinar transferência de custódia",
      recordLabel: `${sample.accession_number} · ${sample.commercial_name}`,
      suggestedReason: reason.trim(),
    });
    if (!token) return;

    setSubmitting(true);
    try {
      await api.post(
        "/custody/transfer",
        {
          device_sample_id: sample.id,
          to_custodian_id: toCustodian,
          reason: reason.trim(),
          storage_location: location.trim(),
          seal_number: seal.trim() || null,
          notes: notes.trim() || null,
          version: sample.version,
        },
        token,
      );
      push({
        variant: "success",
        title: "Custódia transferida",
        description: "Evento registrado na cadeia e na trilha de auditoria.",
      });
      onOpenChange(false);
      onTransferred();
    } catch (error) {
      push({
        variant: "destructive",
        title: "Transferência recusada",
        description:
          error instanceof ApiError ? error.message : "Tente novamente.",
      });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Transferir guarda da amostra</DialogTitle>
          <DialogDescription>
            {sample.accession_number} · {sample.commercial_name}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleTransfer} className="grid gap-4">
          <div className="grid gap-1.5">
            <Label htmlFor="to-custodian">Novo custodiante *</Label>
            <Select value={toCustodian} onValueChange={setToCustodian}>
              <SelectTrigger id="to-custodian">
                <SelectValue placeholder="Selecione o responsável" />
              </SelectTrigger>
              <SelectContent>
                {eligible.map((candidate) => (
                  <SelectItem key={candidate.id} value={candidate.id}>
                    {candidate.full_name} · {candidate.role}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-[11px] text-muted-foreground">
              Atual: {sample.current_custodian?.full_name ?? "sem custodiante"}
            </p>
          </div>

          <div className="grid gap-1.5">
            <Label htmlFor="transfer-reason">Motivo da transferência *</Label>
            <Textarea
              id="transfer-reason"
              rows={3}
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              placeholder="Ex.: Encaminhamento ao laboratório para ensaios de conformidade."
              required
            />
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="grid gap-1.5">
              <Label htmlFor="transfer-location">Localização de destino *</Label>
              <Input
                id="transfer-location"
                value={location}
                onChange={(event) => setLocation(event.target.value)}
                placeholder="Prateleira B3"
                required
              />
            </div>
            <div className="grid gap-1.5">
              <Label htmlFor="transfer-seal">Nº do lacre</Label>
              <Input
                id="transfer-seal"
                value={seal}
                onChange={(event) => setSeal(event.target.value)}
                placeholder="SELO-2026-0001"
                className="font-mono"
              />
            </div>
          </div>

          <div className="grid gap-1.5">
            <Label htmlFor="transfer-notes">Observações</Label>
            <Textarea
              id="transfer-notes"
              rows={2}
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              placeholder="Condição da embalagem, lacre, temperatura…"
            />
          </div>

          <div className="flex items-start gap-2 rounded-md border border-dashed border-border bg-muted/30 px-3 py-2 text-[11px] leading-relaxed text-muted-foreground">
            <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-success" />
            A transferência é um evento imutável. A assinatura registra quem entregou a
            guarda e o motivo declarado.
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
              Assinar transferência
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
