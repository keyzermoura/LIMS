import React, { useEffect, useState } from "react";
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Copy,
  Cpu,
  Database,
  ExternalLink,
  KeyRound,
  Layers,
  Loader2,
  Plus,
  RefreshCw,
  Send,
  Shield,
  Workflow,
  XCircle,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/components/ui/toast";
import { useAuth } from "@/hooks/use-auth";
import { integrationApi } from "@/lib/api";
import type { InstrumentProfile, OutboxEvent, ServiceClient, ServiceClientCreated } from "@/lib/types";

const AVAILABLE_SCOPES = [
  { id: "instrument:write", label: "instrument:write (Upload de curvas e ensaios brutos)" },
  { id: "instrument:read", label: "instrument:read (Consulta a perfis e dados de bancada)" },
  { id: "reports:read", label: "reports:read (Consulta a laudos homologados)" },
  { id: "tests:read", label: "tests:read (Consulta a ensaios e medições)" },
  { id: "samples:read", label: "samples:read (Consulta a cadeia de custódia e amostras)" },
  { id: "integration:read", label: "integration:read (Exportações BI e Data Lake)" },
  { id: "integration:write", label: "integration:write (Configuração de conectores e outbox)" },
];

export function IntegrationsPage() {
  const { user } = useAuth();
  const { toast } = useToast();
  const [activeTab, setActiveTab] = useState<"clients" | "outbox" | "gateway" | "bi">("clients");

  // State: Service Clients
  const [clients, setClients] = useState<ServiceClient[]>([]);
  const [loadingClients, setLoadingClients] = useState(false);
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [newClientName, setNewClientName] = useState("");
  const [newClientExpires, setNewClientExpires] = useState("90");
  const [selectedScopes, setSelectedScopes] = useState<string[]>(["instrument:write", "samples:read"]);
  const [creatingClient, setCreatingClient] = useState(false);
  const [createdClientData, setCreatedClientData] = useState<ServiceClientCreated | null>(null);

  // State: Outbox
  const [pendingOutbox, setPendingOutbox] = useState<OutboxEvent[]>([]);
  const [deadLetterOutbox, setDeadLetterOutbox] = useState<OutboxEvent[]>([]);
  const [loadingOutbox, setLoadingOutbox] = useState(false);
  const [dispatching, setDispatching] = useState(false);
  const [retryingId, setRetryingId] = useState<string | null>(null);

  // State: Gateway Profiles
  const [profiles, setProfiles] = useState<InstrumentProfile[]>([]);
  const [loadingProfiles, setLoadingProfiles] = useState(false);

  // Loaders
  async function loadServiceClients() {
    if (user?.role !== "ADMIN") return;
    setLoadingClients(true);
    try {
      const data = await integrationApi.listServiceClients();
      setClients(data);
    } catch (err: unknown) {
      toast({
        title: "Erro ao carregar clientes",
        description: err instanceof Error ? err.message : "Falha na comunicação.",
        variant: "destructive",
      });
    } finally {
      setLoadingClients(false);
    }
  }

  async function loadOutbox() {
    setLoadingOutbox(true);
    try {
      const [pending, deadLetter] = await Promise.all([
        integrationApi.getPendingOutbox(50),
        integrationApi.getDeadLetterOutbox(50),
      ]);
      setPendingOutbox(pending);
      setDeadLetterOutbox(deadLetter);
    } catch (err: unknown) {
      toast({
        title: "Erro ao carregar outbox",
        description: err instanceof Error ? err.message : "Falha na comunicação.",
        variant: "destructive",
      });
    } finally {
      setLoadingOutbox(false);
    }
  }

  async function loadProfiles() {
    setLoadingProfiles(true);
    try {
      const res = await integrationApi.getProfiles();
      setProfiles(res.profiles || []);
    } catch (err: unknown) {
      toast({
        title: "Erro ao carregar perfis",
        description: err instanceof Error ? err.message : "Falha na comunicação.",
        variant: "destructive",
      });
    } finally {
      setLoadingProfiles(false);
    }
  }

  useEffect(() => {
    if (activeTab === "clients") loadServiceClients();
    if (activeTab === "outbox") loadOutbox();
    if (activeTab === "gateway") loadProfiles();
  }, [activeTab]);

  // Actions: Service Clients
  async function handleCreateClient(e: React.FormEvent) {
    e.preventDefault();
    if (!newClientName.trim()) return;

    setCreatingClient(true);
    try {
      const created = await integrationApi.createServiceClient({
        name: newClientName.trim(),
        scopes: selectedScopes,
        expires_in_days: parseInt(newClientExpires, 10) || 90,
      });
      setCreatedClientData(created);
      toast({
        title: "Conta M2M Criada com Sucesso",
        description: "Copie as credenciais imediatamente. O segredo não será exibido de novo.",
      });
      loadServiceClients();
    } catch (err: unknown) {
      toast({
        title: "Erro ao criar conta de serviço",
        description: err instanceof Error ? err.message : "Falha.",
        variant: "destructive",
      });
    } finally {
      setCreatingClient(false);
    }
  }

  async function handleRotateSecret(clientId: string) {
    if (!confirm(`Deseja rotacionar o segredo do cliente ${clientId}? O segredo anterior permanecerá ativo por 7 dias durante o período de carência.`)) {
      return;
    }

    try {
      const res = await integrationApi.rotateSecret(clientId);
      alert(`Novo Client Secret gerado para ${clientId}:\n\n${res.client_secret}\n\nCopie e salve em local seguro!`);
      loadServiceClients();
    } catch (err: unknown) {
      toast({
        title: "Erro ao rotacionar segredo",
        description: err instanceof Error ? err.message : "Falha.",
        variant: "destructive",
      });
    }
  }

  async function handleDeactivateClient(clientId: string) {
    if (!confirm(`Tem certeza que deseja revogar o cliente ${clientId}? O acesso M2M será interrompido imediatamente.`)) {
      return;
    }

    try {
      await integrationApi.deactivateServiceClient(clientId);
      toast({ title: "Cliente revogado", description: `O cliente ${clientId} foi desativado.` });
      loadServiceClients();
    } catch (err: unknown) {
      toast({
        title: "Erro ao desativar cliente",
        description: err instanceof Error ? err.message : "Falha.",
        variant: "destructive",
      });
    }
  }

  // Actions: Outbox
  async function handleDispatchOutbox() {
    setDispatching(true);
    try {
      const res = await integrationApi.dispatchOutbox(50);
      toast({
        title: "Fila de Outbox Processada",
        description: `${res.dispatched} eventos despachados, ${res.failed} falhas.`,
      });
      loadOutbox();
    } catch (err: unknown) {
      toast({
        title: "Erro ao disparar outbox",
        description: err instanceof Error ? err.message : "Falha.",
        variant: "destructive",
      });
    } finally {
      setDispatching(false);
    }
  }

  async function handleRetryDeadLetter(id: string) {
    setRetryingId(id);
    try {
      await integrationApi.retryDeadLetter(id);
      toast({
        title: "Evento recolocado na fila",
        description: "O evento foi transferido para status PENDING para nova tentativa.",
      });
      loadOutbox();
    } catch (err: unknown) {
      toast({
        title: "Erro ao reprocessar evento",
        description: err instanceof Error ? err.message : "Falha.",
        variant: "destructive",
      });
    } finally {
      setRetryingId(null);
    }
  }

  function copyToClipboard(text: string, label: string) {
    navigator.clipboard.writeText(text);
    toast({ title: "Copiado para a área de transferência", description: label });
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <Workflow className="h-7 w-7 text-primary" />
            Integrações & Ecossistema M2M
          </h1>
          <p className="text-sm text-muted-foreground">
            Gestão de Contas de Serviço (RFC 6749), Webhooks com Outbox Transacional, Gateway de Instrumentos e Exportação BI.
          </p>
        </div>

        {activeTab === "clients" && user?.role === "ADMIN" && (
          <Button onClick={() => { setCreatedClientData(null); setNewClientName(""); setCreateModalOpen(true); }}>
            <Plus className="mr-2 h-4 w-4" />
            Nova Conta de Serviço M2M
          </Button>
        )}

        {activeTab === "outbox" && (
          <div className="flex gap-2">
            <Button variant="outline" onClick={loadOutbox} disabled={loadingOutbox}>
              <RefreshCw className={`mr-2 h-4 w-4 ${loadingOutbox ? "animate-spin" : ""}`} />
              Atualizar
            </Button>
            <Button onClick={handleDispatchOutbox} disabled={dispatching || pendingOutbox.length === 0}>
              <Send className="mr-2 h-4 w-4" />
              {dispatching ? "Despachando…" : "Despachar Pendentes"}
            </Button>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="flex border-b border-border space-x-4">
        <button
          className={`pb-2 text-sm font-medium transition-colors border-b-2 ${
            activeTab === "clients"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
          onClick={() => setActiveTab("clients")}
        >
          Contas de Serviço (M2M)
        </button>
        <button
          className={`pb-2 text-sm font-medium transition-colors border-b-2 ${
            activeTab === "outbox"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
          onClick={() => setActiveTab("outbox")}
        >
          Fila Outbox & Webhooks
          {(pendingOutbox.length > 0 || deadLetterOutbox.length > 0) && (
            <Badge variant="secondary" className="ml-2">
              {pendingOutbox.length + deadLetterOutbox.length}
            </Badge>
          )}
        </button>
        <button
          className={`pb-2 text-sm font-medium transition-colors border-b-2 ${
            activeTab === "gateway"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
          onClick={() => setActiveTab("gateway")}
        >
          Gateway de Instrumentos
        </button>
        <button
          className={`pb-2 text-sm font-medium transition-colors border-b-2 ${
            activeTab === "bi"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
          onClick={() => setActiveTab("bi")}
        >
          Conectores BI & Exportação por Cursor
        </button>
      </div>

      {/* Tab 1: Service Clients */}
      {activeTab === "clients" && (
        <div className="space-y-4">
          <div className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Clientes M2M Cadastrados</CardTitle>
                <KeyRound className="h-4 w-4 text-primary" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{clients.length}</div>
                <p className="text-xs text-muted-foreground">Credenciais OAuth2 client_credentials</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Contas Ativas</CardTitle>
                <CheckCircle2 className="h-4 w-4 text-emerald-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{clients.filter((c) => c.is_active).length}</div>
                <p className="text-xs text-muted-foreground">Operacionais com chave válida</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Conformidade e Isolamento</CardTitle>
                <Shield className="h-4 w-4 text-primary" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-emerald-600">Zero Humanos</div>
                <p className="text-xs text-muted-foreground">Tokens curtos de 15 min; isolados por escopo</p>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Credenciais de Serviço Registradas</CardTitle>
              <CardDescription>
                Contas M2M usadas por analisadores, balanças, agentes de bancada e pipelines corporativos.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {loadingClients ? (
                <div className="flex h-32 items-center justify-center">
                  <Loader2 className="h-6 w-6 animate-spin text-primary" />
                </div>
              ) : clients.length === 0 ? (
                <div className="py-8 text-center text-muted-foreground">
                  Nenhuma conta de serviço cadastrada. Crie uma nova conta para iniciar conexões M2M.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Nome & Finalidade</TableHead>
                        <TableHead>Client ID</TableHead>
                        <TableHead>Escopos Concedidos</TableHead>
                        <TableHead>Expira em</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead className="text-right">Ações</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {clients.map((c) => (
                        <TableRow key={c.id}>
                          <TableCell className="font-medium">
                            {c.name}
                            <div className="text-xs text-muted-foreground">Criado em {new Date(c.created_at).toLocaleDateString()}</div>
                          </TableCell>
                          <TableCell>
                            <code className="rounded bg-muted px-2 py-1 text-xs">{c.client_id}</code>
                          </TableCell>
                          <TableCell>
                            <div className="flex flex-wrap gap-1">
                              {c.scopes.map((s) => (
                                <Badge key={s} variant="outline" className="text-xs">
                                  {s}
                                </Badge>
                              ))}
                            </div>
                          </TableCell>
                          <TableCell className="text-xs">
                            {new Date(c.expires_at).toLocaleDateString()}
                          </TableCell>
                          <TableCell>
                            {c.is_active ? (
                              <Badge className="bg-emerald-600 hover:bg-emerald-700">Ativo</Badge>
                            ) : (
                              <Badge variant="destructive">Revogado</Badge>
                            )}
                          </TableCell>
                          <TableCell className="text-right space-x-2">
                            {c.is_active && user?.role === "ADMIN" && (
                              <>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => handleRotateSecret(c.client_id)}
                                >
                                  Rotacionar
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="text-destructive hover:bg-destructive/10"
                                  onClick={() => handleDeactivateClient(c.client_id)}
                                >
                                  Revogar
                                </Button>
                              </>
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Tab 2: Outbox & Webhooks */}
      {activeTab === "outbox" && (
        <div className="space-y-4">
          <div className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Eventos Pendentes</CardTitle>
                <RefreshCw className="h-4 w-4 text-amber-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{pendingOutbox.length}</div>
                <p className="text-xs text-muted-foreground">Aguardando entrega garantida (At-Least-Once)</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Dead-Letter Queue (DLQ)</CardTitle>
                <AlertTriangle className="h-4 w-4 text-destructive" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-destructive">{deadLetterOutbox.length}</div>
                <p className="text-xs text-muted-foreground">Excederam 5 retentativas com backoff</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Assinatura Criptográfica</CardTitle>
                <Shield className="h-4 w-4 text-primary" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">HMAC-SHA256</div>
                <p className="text-xs text-muted-foreground">Header X-LIMS-Signature com anti-replay (&lt; 300 s)</p>
              </CardContent>
            </Card>
          </div>

          {deadLetterOutbox.length > 0 && (
            <Card className="border-destructive/40 bg-destructive/5">
              <CardHeader>
                <CardTitle className="text-destructive flex items-center gap-2">
                  <XCircle className="h-5 w-5" />
                  Falhas de Entrega em Dead-Letter ({deadLetterOutbox.length})
                </CardTitle>
                <CardDescription>
                  Eventos que não puderam ser entregues aos webhooks após 5 retentativas consecutivas.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Evento</TableHead>
                      <TableHead>Delivery ID</TableHead>
                      <TableHead>Último Erro</TableHead>
                      <TableHead>Tentativas</TableHead>
                      <TableHead className="text-right">Ação</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {deadLetterOutbox.map((evt) => (
                      <TableRow key={evt.id}>
                        <TableCell className="font-semibold">{evt.event_name}</TableCell>
                        <TableCell><code className="text-xs">{evt.delivery_id.slice(0, 16)}…</code></TableCell>
                        <TableCell className="text-xs text-destructive max-w-xs truncate">{evt.last_error || "Timeout"}</TableCell>
                        <TableCell>{evt.retry_count} / {evt.max_retries}</TableCell>
                        <TableCell className="text-right">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleRetryDeadLetter(evt.id)}
                            disabled={retryingId === evt.id}
                          >
                            {retryingId === evt.id ? "Enfileirando…" : "Reprocessar"}
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader>
              <CardTitle>Fila de Eventos Pendentes</CardTitle>
              <CardDescription>
                Eventos gerados transacionalmente no mesmo commit das operações laboratoriais (report.issued, oos.opened, test.completed).
              </CardDescription>
            </CardHeader>
            <CardContent>
              {loadingOutbox ? (
                <div className="flex h-32 items-center justify-center">
                  <Loader2 className="h-6 w-6 animate-spin text-primary" />
                </div>
              ) : pendingOutbox.length === 0 ? (
                <div className="py-8 text-center text-muted-foreground flex flex-col items-center gap-2">
                  <CheckCircle2 className="h-8 w-8 text-emerald-500" />
                  <span>Fila de outbox limpa. Todos os eventos foram despachados com sucesso.</span>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Evento</TableHead>
                      <TableHead>Agregado</TableHead>
                      <TableHead>Delivery ID</TableHead>
                      <TableHead>Tentativas</TableHead>
                      <TableHead>Enfileirado em</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {pendingOutbox.map((evt) => (
                      <TableRow key={evt.id}>
                        <TableCell>
                          <Badge variant="outline">{evt.event_name}</Badge>
                        </TableCell>
                        <TableCell className="text-xs">{evt.aggregate_type} ({evt.aggregate_id.slice(0, 8)}…)</TableCell>
                        <TableCell><code className="text-xs">{evt.delivery_id}</code></TableCell>
                        <TableCell>{evt.retry_count} / {evt.max_retries}</TableCell>
                        <TableCell className="text-xs">{new Date(evt.created_at).toLocaleTimeString()}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Tab 3: Instrument Gateway */}
      {activeTab === "gateway" && (
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Cpu className="h-5 w-5 text-primary" />
                Catálogo Declarativo de Perfis de Instrumentos
              </CardTitle>
              <CardDescription>
                Perfis versionados com schemas determinísticos e baterias de teste no CI para Agilent, Shimadzu, Thermo, ASTM e Balanças.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {loadingProfiles ? (
                <div className="flex h-32 items-center justify-center">
                  <Loader2 className="h-6 w-6 animate-spin text-primary" />
                </div>
              ) : (
                <div className="grid gap-4 md:grid-cols-2">
                  {profiles.map((p) => (
                    <Card key={p.profile_id} className="border border-border">
                      <CardHeader className="pb-3">
                        <div className="flex items-center justify-between">
                          <CardTitle className="text-base font-semibold">{p.name}</CardTitle>
                          <Badge variant="secondary">v{p.version}</Badge>
                        </div>
                        <CardDescription className="text-xs">
                          {p.manufacturer} • Formato: {p.format.toUpperCase()}
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-2 text-xs">
                        <p className="text-muted-foreground">{p.description}</p>
                        <div className="rounded bg-muted p-2 font-mono text-[11px] space-y-1">
                          <div><strong>Profile ID:</strong> {p.profile_id}</div>
                          {p.delimiter && <div><strong>Delimitador:</strong> "{p.delimiter}"</div>}
                          {p.decimal_separator && <div><strong>Separador Decimal:</strong> "{p.decimal_separator}"</div>}
                          {p.columns && (
                            <div>
                              <strong>Mapeamento:</strong>{" "}
                              {Object.entries(p.columns)
                                .map(([k, v]) => `${k} → ${v}`)
                                .join(", ")}
                            </div>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Tab 4: BI Connectors & Cursor Pagination */}
      {activeTab === "bi" && (
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Database className="h-5 w-5 text-primary" />
                Conectores Analíticos Corporativos (BI, PowerBI, Tableau)
              </CardTitle>
              <CardDescription>
                Endpoints REST de alta performance paginados por cursor determinístico com negociação de conteúdo (ISO/IEC 17025 §7.8).
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <div className="rounded-lg border border-border p-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-sm">1. Exportação de Ensaios Laboratoriais</span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => copyToClipboard("/api/v1/integration/exports/tests", "URL de Ensaios")}
                    >
                      <Copy className="h-3.5 w-3.5 mr-1" /> Copiar Endpoint
                    </Button>
                  </div>
                  <code className="block bg-muted p-2 rounded text-xs font-mono">
                    GET /api/v1/integration/exports/tests?limit=50&cursor=&lt;opaque_cursor&gt;&updated_since=&lt;iso8601&gt;
                  </code>
                  <p className="text-xs text-muted-foreground">
                    Retorna medições numéricas, limites de especificação, analista responsável, timestamps de ensaio e assinatura.
                  </p>
                </div>

                <div className="rounded-lg border border-border p-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-sm">2. Exportação de Laudos Periciais Oficiais</span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => copyToClipboard("/api/v1/integration/exports/reports", "URL de Laudos")}
                    >
                      <Copy className="h-3.5 w-3.5 mr-1" /> Copiar Endpoint
                    </Button>
                  </div>
                  <code className="block bg-muted p-2 rounded text-xs font-mono">
                    GET /api/v1/integration/exports/reports?limit=50&cursor=&lt;opaque_cursor&gt;
                  </code>
                  <p className="text-xs text-muted-foreground">
                    Documentos oficiais periciais com Hash SHA-256 de integridade e histórico de emendas regulamentares.
                  </p>
                </div>

                <div className="rounded-lg border border-border p-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-sm">3. Métricas Agregadas de Qualidade (QC Metrics)</span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => copyToClipboard("/api/v1/integration/exports/qc-metrics", "URL de Métricas QC")}
                    >
                      <Copy className="h-3.5 w-3.5 mr-1" /> Copiar Endpoint
                    </Button>
                  </div>
                  <code className="block bg-muted p-2 rounded text-xs font-mono">
                    GET /api/v1/integration/exports/qc-metrics
                  </code>
                  <p className="text-xs text-muted-foreground">
                    Totais consolidados de ensaios por status e conformidade, laudos emitidos e desvios OOS em aberto.
                  </p>
                </div>
              </div>

              <div className="rounded-md bg-muted p-4 space-y-2">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Exemplo cURL com Cabeçalhos de Versionamento:</h4>
                <pre className="text-xs font-mono overflow-x-auto text-foreground">
{`curl -X GET "https://lims.local/api/v1/integration/exports/tests?limit=100" \\
  -H "Authorization: Bearer <m2m_token>" \\
  -H "Accept: application/vnd.lims.v1+json"`}
                </pre>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Modal: Create Service Client */}
      <Dialog open={createModalOpen} onOpenChange={setCreateModalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Nova Conta de Serviço M2M</DialogTitle>
            <DialogDescription>
              Crie uma credencial OAuth2 de máquina para conexão de analisadores ou pipelines externos.
            </DialogDescription>
          </DialogHeader>

          {createdClientData ? (
            <div className="space-y-4">
              <div className="rounded-lg border border-amber-500/50 bg-amber-500/10 p-4 text-xs space-y-2 text-foreground">
                <div className="font-semibold text-amber-700 dark:text-amber-400 flex items-center gap-1.5">
                  <AlertTriangle className="h-4 w-4" />
                  Atenção: Salve o Client Secret agora!
                </div>
                <p>O segredo é criptografado com Argon2id no banco e nunca poderá ser exibido novamente.</p>
              </div>

              <div className="space-y-2">
                <Label>Client ID</Label>
                <div className="flex gap-2">
                  <Input readOnly value={createdClientData.client_id} className="font-mono text-xs" />
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => copyToClipboard(createdClientData.client_id, "Client ID")}
                  >
                    <Copy className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Client Secret</Label>
                <div className="flex gap-2">
                  <Input readOnly value={createdClientData.client_secret} className="font-mono text-xs" />
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => copyToClipboard(createdClientData.client_secret, "Client Secret")}
                  >
                    <Copy className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              <DialogFooter>
                <Button onClick={() => setCreateModalOpen(false)}>Concluído</Button>
              </DialogFooter>
            </div>
          ) : (
            <form onSubmit={handleCreateClient} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="client-name">Nome da Aplicação / Instrumento</Label>
                <Input
                  id="client-name"
                  placeholder="Ex: Agente HPLC Central - Linha 1"
                  value={newClientName}
                  onChange={(e) => setNewClientName(e.target.value)}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="client-expires">Validade da Credencial (dias)</Label>
                <Input
                  id="client-expires"
                  type="number"
                  min="1"
                  max="365"
                  value={newClientExpires}
                  onChange={(e) => setNewClientExpires(e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label>Escopos de Acesso</Label>
                <div className="space-y-2 max-h-40 overflow-y-auto border border-border p-2 rounded">
                  {AVAILABLE_SCOPES.map((sc) => {
                    const checked = selectedScopes.includes(sc.id);
                    return (
                      <label key={sc.id} className="flex items-start gap-2 text-xs cursor-pointer">
                        <input
                          type="checkbox"
                          checked={checked}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedScopes([...selectedScopes, sc.id]);
                            } else {
                              setSelectedScopes(selectedScopes.filter((s) => s !== sc.id));
                            }
                          }}
                          className="mt-0.5"
                        />
                        <span>{sc.label}</span>
                      </label>
                    );
                  })}
                </div>
              </div>

              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setCreateModalOpen(false)}>
                  Cancelar
                </Button>
                <Button type="submit" disabled={creatingClient || !newClientName.trim()}>
                  {creatingClient ? "Criando…" : "Gerar Credenciais"}
                </Button>
              </DialogFooter>
            </form>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
