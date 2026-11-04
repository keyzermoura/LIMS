import { Badge } from "@/components/ui/badge";
import {
  CAPA_STATUS_LABELS,
  OUTCOME_LABELS,
  SAMPLE_STATUS_LABELS,
  STATUS_TONE,
  TEST_STATUS_LABELS,
  cn,
} from "@/lib/utils";

type Kind = "sample" | "test" | "outcome" | "capa";

const LABELS: Record<Kind, Record<string, string>> = {
  sample: SAMPLE_STATUS_LABELS,
  test: TEST_STATUS_LABELS,
  outcome: OUTCOME_LABELS,
  capa: CAPA_STATUS_LABELS,
};

export function StatusBadge({
  status,
  kind = "sample",
  className,
}: {
  status: string | null | undefined;
  kind?: Kind;
  className?: string;
}) {
  if (!status) {
    return (
      <Badge variant="outline" className={cn("border-dashed text-muted-foreground", className)}>
        Sem status
      </Badge>
    );
  }

  return (
    <Badge
      variant="outline"
      className={cn(
        "border font-semibold normal-case tracking-normal",
        STATUS_TONE[status] ?? "border-border bg-muted text-foreground",
        className,
      )}
    >
      {LABELS[kind][status] ?? status}
    </Badge>
  );
}
