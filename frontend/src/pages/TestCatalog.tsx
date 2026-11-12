import * as React from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  BookOpen,
  CheckCircle2,
  FileCode2,
  Layers,
  Loader2,
  Plus,
  RefreshCw,
  Sparkles,
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
import { useToast } from "@/components/ui/toast";
import { useAuth } from "@/hooks/use-auth";
import { methodsApi, ApiError } from "@/lib/api";
import type {
  TestMethod,
  TestMethodCreatePayload,
} from "@/lib/types";

export function TestCatalogPage() {
  const { user } = useAuth();
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const [createModalOpen, setCreateModalOpen] = React.useState(false);
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [isSeeding, setIsSeeding] = React.useState(false);

  const [form, setForm] = React.useState<TestMethodCreatePayload>({
    code: "",
    name: "",
    standard: "",
    category: "Geral",
    description: "",
    default_unit: "UN",
    default_lower_limit: "",
    default_upper_limit: "",
    default_acceptance_criteria: "",
  });

  const { data: methods = [], isLoading, refetch } = useQuery({
    queryKey: ["methods"],
    queryFn: () => methodsApi.list(),
  });

  const canWrite = user?.role === "ADMIN" || user?.role === "FISCAL" || user?.role === "TECNICO";
  const isAdmin = user?.role === "ADMIN";

  async function handleCreateMethod(e: React.FormEvent) {
    e.preventDefault();
    if (!form.code.trim() || !form.name.trim() || !form.standard.trim()) {
      toast({
        title: "Campos obrigatórios",
        description: "Código, nome e norma técnica são obrigatórios.",
        variant: "destructive",
      });
      return;
    }

    setIsSubmitting(true);
    try {
      await methodsApi.create({
        ...form,
        default_lower_limit: form.default_lower_limit ? Number(form.default_lower_limit) : null,
        default_upper_limit: form.default_upper_limit ? Number(form.default_upper_limit) : null,
      });
      toast({
        title: "Método cadastrado",
        description: `Método ${form.code} adicionado com sucesso.`,
      });
      setCreateModalOpen(false);
      setForm({
        code: "",
        name: "",
        standard: "",
        category: "Geral",
        description: "",
        default_unit: "UN",
        default_lower_limit: "",
        default_upper_limit: "",
        default_acceptance_criteria: "",
      });
      queryClient.invalidateQueries({ queryKey: ["methods"] });
    } catch (err) {
      toast({
        title: "Erro ao cadastrar método",
        description: err instanceof ApiError ? err.message : "Falha na comunicação.",
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleSeedStandards() {
    setIsSeeding(true);
    try {
      const seeded = await methodsApi.seedStandards();
      toast({
        title: "Catálogo inicializado",
        description: `${seeded.length} métodos normativos padrão da SEFI carregados.`,
      });
      queryClient.invalidateQueries({ queryKey: ["methods"] });
    } catch (err) {
      toast({
        title: "Erro ao inicializar normas",
        description: err instanceof ApiError ? err.message : "Falha ao carregar normas.",
        variant: "destructive",
      });
    } finally {
      setIsSeeding(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <BookOpen className="h-6 w-6 text-primary" />
            Catálogo de Métodos de Ensaio e Normas
          </h1>
          <p className="text-sm text-muted-foreground">
            Biblioteca padronizada de procedimentos de ensaio, normas técnicas regulatórias e limites de aceitação.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" onClick={() => refetch()} className="gap-2">
            <RefreshCw className="h-4 w-4" />
            Atualizar
          </Button>
          {isAdmin ? (
            <Button
              variant="outline"
              size="sm"
              onClick={handleSeedStandards}
              disabled={isSeeding}
              className="gap-2 border-primary/40 text-primary hover:bg-primary/5"
            >
              {isSeeding ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
              Carregar Padrões SEFI
            </Button>
          ) : null}
          {canWrite ? (
            <Button size="sm" onClick={() => setCreateModalOpen(true)} className="gap-2">
              <Plus className="h-4 w-4" />
              Novo Método
            </Button>
          ) : null}
        </div>
      </div>

      {/* Grid de Métodos */}
      {isLoading ? (
        <div className="flex items-center justify-center p-12 text-muted-foreground">
          <Loader2 className="h-6 w-6 animate-spin text-primary mr-2" />
          Carregando catálogo de métodos…
        </div>
      ) : methods.length === 0 ? (
        <Card className="p-8 text-center text-muted-foreground">
          <p className="mb-4">Nenhum método de ensaio cadastrado ainda no catálogo.</p>
          {isAdmin ? (
            <Button size="sm" onClick={handleSeedStandards} disabled={isSeeding} className="gap-2">
              <Sparkles className="h-4 w-4" />
              Inicializar com Métodos Normativos Padrão
            </Button>
          ) : null}
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {methods.map((method) => (
            <Card key={method.id} className="flex flex-col justify-between transition-shadow hover:shadow-md">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <span className="text-xs font-mono font-bold text-primary">
                      {method.code}
                    </span>
                    <CardTitle className="text-base font-semibold leading-tight mt-0.5">
                      {method.name}
                    </CardTitle>
                    <CardDescription className="text-xs font-medium text-foreground/80 mt-1 flex items-center gap-1.5">
                      <FileCode2 className="h-3.5 w-3.5 text-muted-foreground" />
                      {method.standard}
                    </CardDescription>
                  </div>
                  <span className="text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded bg-muted text-muted-foreground">
                    {method.category || "Geral"}
                  </span>
                </div>
              </CardHeader>

              <CardContent className="space-y-3 pb-4 text-xs">
                {method.description ? (
                  <p className="text-muted-foreground text-xs line-clamp-2">
                    {method.description}
                  </p>
                ) : null}

                <div className="rounded-md bg-muted/40 p-2.5 space-y-1.5 border border-border/50">
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-muted-foreground">Unidade de Medida:</span>
                    <span className="font-mono font-semibold text-foreground">{method.default_unit}</span>
                  </div>
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-muted-foreground">Limites de Aceitação:</span>
                    <span className="font-mono text-foreground font-medium">
                      {method.default_lower_limit !== null ? method.default_lower_limit : "-∞"} a{" "}
                      {method.default_upper_limit !== null ? method.default_upper_limit : "+∞"}{" "}
                      {method.default_unit}
                    </span>
                  </div>
                  {method.default_acceptance_criteria ? (
                    <div className="pt-1.5 border-t border-border/40 text-[11px] text-muted-foreground">
                      <strong className="text-foreground">Critério: </strong>
                      {method.default_acceptance_criteria}
                    </div>
                  ) : null}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Modal de Criação de Método */}
      <Dialog open={createModalOpen} onOpenChange={setCreateModalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Cadastrar Método de Ensaio</DialogTitle>
            <DialogDescription>
              Insira as referências normativas e os parâmetros de aceitação.
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleCreateMethod} className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label htmlFor="m_code" className="text-xs">Código do Método *</Label>
                <Input
                  id="m_code"
                  placeholder="MET-ELETRO-02"
                  value={form.code}
                  onChange={(e) => setForm({ ...form, code: e.target.value })}
                  className="h-8 text-xs uppercase font-mono"
                  required
                />
              </div>
              <div>
                <Label htmlFor="m_cat" className="text-xs">Categoria</Label>
                <Input
                  id="m_cat"
                  placeholder="Elétrica / Mecânica"
                  value={form.category || ""}
                  onChange={(e) => setForm({ ...form, category: e.target.value })}
                  className="h-8 text-xs"
                />
              </div>
            </div>

            <div>
              <Label htmlFor="m_name" className="text-xs">Nome Oficial do Ensaio *</Label>
              <Input
                id="m_name"
                placeholder="Ex: Corrente de Fuga e Isolamento de Paciente"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="h-8 text-xs"
                required
              />
            </div>

            <div>
              <Label htmlFor="m_standard" className="text-xs">Norma Técnica de Referência *</Label>
              <Input
                id="m_standard"
                placeholder="Ex: ABNT NBR IEC 60601-1:2016 Cláusula 8.7"
                value={form.standard}
                onChange={(e) => setForm({ ...form, standard: e.target.value })}
                className="h-8 text-xs"
                required
              />
            </div>

            <div className="grid grid-cols-3 gap-2 pt-1 border-t border-border">
              <div>
                <Label htmlFor="m_unit" className="text-xs">Unidade</Label>
                <Input
                  id="m_unit"
                  placeholder="mA / °C"
                  value={form.default_unit || "UN"}
                  onChange={(e) => setForm({ ...form, default_unit: e.target.value })}
                  className="h-8 text-xs font-mono"
                />
              </div>
              <div>
                <Label htmlFor="m_lower" className="text-xs">Limite Mínimo</Label>
                <Input
                  id="m_lower"
                  type="number"
                  step="any"
                  placeholder="0.0"
                  value={form.default_lower_limit ?? ""}
                  onChange={(e) => setForm({ ...form, default_lower_limit: e.target.value })}
                  className="h-8 text-xs font-mono"
                />
              </div>
              <div>
                <Label htmlFor="m_upper" className="text-xs">Limite Máximo</Label>
                <Input
                  id="m_upper"
                  type="number"
                  step="any"
                  placeholder="10.0"
                  value={form.default_upper_limit ?? ""}
                  onChange={(e) => setForm({ ...form, default_upper_limit: e.target.value })}
                  className="h-8 text-xs font-mono"
                />
              </div>
            </div>

            <div>
              <Label htmlFor="m_crit" className="text-xs">Critério de Aceitação / Observações</Label>
              <Textarea
                id="m_crit"
                placeholder="A corrente medida não deve exceder os limites estipulados na Tabela 3 da norma..."
                value={form.default_acceptance_criteria || ""}
                onChange={(e) => setForm({ ...form, default_acceptance_criteria: e.target.value })}
                className="text-xs min-h-[60px]"
              />
            </div>

            <DialogFooter className="pt-2">
              <Button type="button" variant="outline" size="sm" onClick={() => setCreateModalOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" size="sm" disabled={isSubmitting}>
                {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                Salvar Método
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
