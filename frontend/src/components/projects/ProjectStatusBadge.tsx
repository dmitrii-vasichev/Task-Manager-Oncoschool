import { Badge } from "@/components/ui/badge";
import { PROJECT_STATUS_LABELS } from "@/lib/projectUtils";
import { cn } from "@/lib/utils";
import type { ProjectStatus } from "@/lib/types";

const PROJECT_STATUS_CLASSES: Record<ProjectStatus, string> = {
  planned: "bg-muted text-muted-foreground ring-1 ring-inset ring-border/70",
  in_progress:
    "bg-status-progress-bg text-status-progress-fg ring-1 ring-inset ring-status-progress-ring",
  paused:
    "bg-status-review-bg/70 text-status-review-fg ring-1 ring-inset ring-status-review-ring",
  completed:
    "bg-status-done-bg text-status-done-fg ring-1 ring-inset ring-status-done-ring",
  cancelled:
    "bg-background text-status-cancelled-fg ring-1 ring-inset ring-status-cancelled-ring",
};

export function ProjectStatusBadge({
  status,
  className,
}: {
  status: ProjectStatus;
  className?: string;
}) {
  return (
    <Badge
      variant="outline"
      className={cn(
        "min-w-[6.5rem] justify-center rounded-full border-transparent px-2 py-0.5 text-2xs font-medium",
        PROJECT_STATUS_CLASSES[status],
        className,
      )}
    >
      {PROJECT_STATUS_LABELS[status]}
    </Badge>
  );
}
