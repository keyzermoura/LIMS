import { Badge } from "@/components/ui/badge";
import {
  CAPA_STATUS_LABELS,
  CHECKLIST_RESULT_LABELS,
  CONFERENCE_STATUS_LABELS,
  COORDINATION_STATUS_LABELS,
  CRITERION_CLASS_LABELS,
  CUSTODY_OBJECT_STATUS_LABELS,
  EQUIPMENT_CALIBRATION_LABELS,
  EXECUTION_STATUS_LABELS,
  OUTCOME_LABELS,
  RECEIPT_DECISION_LABELS,
  RECEIPT_STATUS_LABELS,
  SAMPLE_STATUS_LABELS,
  SOLICITATION_STATUS_LABELS,
  STATUS_TONE,
  TEST_STATUS_LABELS,
  cn,
} from "@/lib/utils";

type Kind =
  | "sample"
  | "test"
  | "outcome"
  | "capa"
  | "solicitation"
  | "receipt"
  | "conference"
  | "custody_object"
  | "criterion_class"
  | "checklist_result"
  | "coordination"
  | "decision"
  | "equipment"
  | "execution";

const LABELS: Record<Kind, Record<string, string>> = {
  sample: SAMPLE_STATUS_LABELS,
  test: TEST_STATUS_LABELS,
  outcome: OUTCOME_LABELS,
  capa: CAPA_STATUS_LABELS,
  solicitation: SOLICITATION_STATUS_LABELS,
  receipt: RECEIPT_STATUS_LABELS,
  conference: CONFERENCE_STATUS_LABELS,
  custody_object: CUSTODY_OBJECT_STATUS_LABELS,
  criterion_class: CRITERION_CLASS_LABELS,
  checklist_result: CHECKLIST_RESULT_LABELS,
  coordination: COORDINATION_STATUS_LABELS,
  decision: RECEIPT_DECISION_LABELS,
  equipment: EQUIPMENT_CALIBRATION_LABELS,
  execution: EXECUTION_STATUS_LABELS,
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
