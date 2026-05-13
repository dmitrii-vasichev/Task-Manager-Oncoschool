import { Badge } from "@/components/ui/badge";
import { IDEA_STATUS_LABELS } from "@/lib/ideaUtils";
import { cn } from "@/lib/utils";
import type { IdeaStatus } from "@/lib/types";

const IDEA_STATUS_CLASSES: Record<IdeaStatus, string> = {
  new: "bg-status-new-bg text-status-new-fg ring-1 ring-inset ring-status-new-ring",
  in_review:
    "bg-status-review-bg text-status-review-fg ring-1 ring-inset ring-status-review-ring",
  accepted:
    "bg-status-progress-bg text-status-progress-fg ring-1 ring-inset ring-status-progress-ring",
  in_tasks:
    "bg-status-progress-bg text-status-progress-fg ring-1 ring-inset ring-status-progress-ring",
  completed:
    "bg-status-done-bg text-status-done-fg ring-1 ring-inset ring-status-done-ring",
  rejected:
    "bg-status-cancelled-bg text-status-cancelled-fg ring-1 ring-inset ring-status-cancelled-ring",
  deferred:
    "bg-muted text-muted-foreground ring-1 ring-inset ring-border/70",
};

export function IdeaStatusBadge({
  status,
  className,
}: {
  status: IdeaStatus;
  className?: string;
}) {
  return (
    <Badge
      variant="outline"
      className={cn(
        "rounded-full border-transparent px-2 py-0.5 text-2xs font-medium",
        IDEA_STATUS_CLASSES[status],
        className,
      )}
    >
      {IDEA_STATUS_LABELS[status]}
    </Badge>
  );
}
