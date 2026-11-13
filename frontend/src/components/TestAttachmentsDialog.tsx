import * as React from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Download, FileUp, HardDrive, Loader2, Paperclip, ShieldCheck } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useToast } from "@/components/ui/toast";
import { attachmentsApi, ApiError } from "@/lib/api";
import type { LabTest, TestAttachment } from "@/lib/types";
import { formatDateTime } from "@/lib/utils";

interface TestAttachmentsDialogProps {
  test: LabTest;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function TestAttachmentsDialog({
  test,
  open,
  onOpenChange,
}: TestAttachmentsDialogProps) {
  const { push } = useToast();
  const queryClient = useQueryClient();
  const fileInputRef = React.useRef<HTMLInputElement | null>(null);

  const [uploading, setUploading] = React.useState(false);

  const { data: attachments, isLoading, refetch } = useQuery<TestAttachment[]>({
    queryKey: ["test-attachments", test.id],
    queryFn: () => attachmentsApi.list(test.id),
    enabled: open,
  });

  async function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      setUploading(true);
      const created = await attachmentsApi.upload(test.id, file);
      push({
        title: "Evidência anexada",
        description: `Arquivo '${created.filename}' registrado com hash SHA-256: ${created.sha256_hash.slice(0, 10)}...`,
        variant: "success",
      });
      await queryClient.invalidateQueries({ queryKey: ["test-attachments", test.id] });
      if (fileInputRef.current) fileInputRef.current.value = "";
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Falha ao anexar arquivo.";
      push({ title: "Erro de upload", description: msg, variant: "destructive" });
    } finally {
      setUploading(false);
    }
  }

  function formatBytes(bytes: number): string {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Paperclip className="h-5 w-5 text-primary" />
            Evidências e Dados Brutos de Bancada (ALCOA+)
          </DialogTitle>
          <DialogDescription>
            Anexos vinculados de forma indissociável ao ensaio:{" "}
            <strong className="text-foreground">{test.name}</strong>
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-2">
          {/* Ação de Upload */}
          <div className="border border-dashed rounded-lg p-6 flex flex-col items-center justify-center text-center bg-muted/10 hover:bg-muted/20 transition-colors">
            <FileUp className="h-8 w-8 text-primary mb-2" />
            <p className="text-xs font-semibold text-foreground">
              Anexar curvas analíticas, fotos de calibração ou laudos de instrumentos
            </p>
            <p className="text-[11px] text-muted-foreground mt-1 mb-3">
              Garantia de integridade criptográfica SHA-256 (tamanho máximo: 25MB)
            </p>
            <input
              ref={fileInputRef}
              type="file"
              onChange={handleFileSelect}
              className="hidden"
            />
            <Button
              size="sm"
              variant="outline"
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
            >
              {uploading ? (
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
              ) : (
                <HardDrive className="h-4 w-4 mr-2" />
              )}
              {uploading ? "Calculando hash e enviando..." : "Selecionar Arquivo"}
            </Button>
          </div>

          {/* Listagem de Evidências */}
          <div className="space-y-2">
            <h4 className="text-xs font-bold text-foreground uppercase tracking-wider">
              Arquivos Anexados ({attachments?.length ?? 0})
            </h4>

            {isLoading ? (
              <div className="flex h-32 items-center justify-center">
                <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
              </div>
            ) : !attachments?.length ? (
              <p className="text-xs text-muted-foreground py-6 text-center italic border rounded-lg">
                Nenhuma evidência bruta anexada até o momento.
              </p>
            ) : (
              <div className="border rounded-lg divide-y">
                {attachments.map((att) => (
                  <div
                    key={att.id}
                    className="p-3 flex items-center justify-between gap-4 text-xs hover:bg-muted/10 transition-colors"
                  >
                    <div className="space-y-1 min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-foreground truncate">
                          {att.filename}
                        </span>
                        <span className="text-muted-foreground">({formatBytes(att.file_size)})</span>
                      </div>
                      <div className="flex items-center gap-2 text-[11px] text-muted-foreground">
                        <ShieldCheck className="h-3.5 w-3.5 text-emerald-600 shrink-0" />
                        <span className="font-mono truncate select-all">
                          SHA-256: {att.sha256_hash}
                        </span>
                        <span>· {formatDateTime(att.created_at)}</span>
                      </div>
                    </div>

                    <a
                      href={attachmentsApi.getDownloadUrl(att.id)}
                      download={att.filename}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center justify-center rounded-md text-xs font-medium border border-input bg-background hover:bg-accent hover:text-accent-foreground h-8 px-3"
                    >
                      <Download className="h-3.5 w-3.5 mr-1.5" />
                      Baixar
                    </a>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
