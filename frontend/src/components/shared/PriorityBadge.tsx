import { type TaskPriority, TASK_PRIORITY_LABELS } from "@/lib/types";
import {
  AlertTriangle,
  ArrowUp,
  Minus,
  ArrowDown,
} from "lucide-react";

const PRIORITY_CONFIG: Record<
  TaskPriority,
  { icon: typeof ArrowUp; className: string; dotClass: string }
> = {
  urgent: {
    icon: AlertTriangle,
    className: "bg-priority-urgent-bg text-priority-urgent-fg",
    dotClass: "bg-priority-urgent-dot",
  },
  high: {
    icon: ArrowUp,
    className: "bg-priority-high-bg text-priority-high-fg",
    dotClass: "bg-priority-high-dot",
  },
  medium: {
    icon: Minus,
    className: "bg-priority-medium-bg text-priority-medium-fg",
    dotClass: "bg-priority-medium-dot",
  },
  low: {
    icon: ArrowDown,
    className: "bg-priority-low-bg text-priority-low-fg",
    dotClass: "bg-priority-low-dot",
  },
};

export function PriorityBadge({ priority }: { priority: TaskPriority }) {
  const { icon: Icon, className } = PRIORITY_CONFIG[priority];

  return (
    <span
      className={`badge-animated inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${className}`}
    >
      <Icon className="h-3 w-3 shrink-0" />
      {TASK_PRIORITY_LABELS[priority]}
    </span>
  );
}
