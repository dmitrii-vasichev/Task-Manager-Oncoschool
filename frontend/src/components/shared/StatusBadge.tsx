import { type TaskStatus, TASK_STATUS_LABELS } from "@/lib/types";
import {
  Circle,
  Loader2,
  Eye,
  CheckCircle2,
  XCircle,
} from "lucide-react";

const STATUS_CONFIG: Record<
  TaskStatus,
  { icon: typeof Circle; className: string }
> = {
  new: {
    icon: Circle,
    className:
      "bg-status-new-bg text-status-new-fg ring-1 ring-inset ring-status-new-ring",
  },
  in_progress: {
    icon: Loader2,
    className:
      "bg-status-progress-bg text-status-progress-fg ring-1 ring-inset ring-status-progress-ring",
  },
  review: {
    icon: Eye,
    className:
      "bg-status-review-bg text-status-review-fg ring-1 ring-inset ring-status-review-ring",
  },
  done: {
    icon: CheckCircle2,
    className:
      "bg-status-done-bg text-status-done-fg ring-1 ring-inset ring-status-done-ring",
  },
  cancelled: {
    icon: XCircle,
    className:
      "bg-status-cancelled-bg text-status-cancelled-fg ring-1 ring-inset ring-status-cancelled-ring",
  },
};

export function StatusBadge({ status }: { status: TaskStatus }) {
  const { icon: Icon, className } = STATUS_CONFIG[status];

  return (
    <span
      className={`badge-animated inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ${className}`}
    >
      <Icon className="h-3 w-3 shrink-0" />
      {TASK_STATUS_LABELS[status]}
    </span>
  );
}
