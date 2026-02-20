import { type TaskPriority, TASK_PRIORITY_LABELS } from "@/lib/types";
import { cn } from "@/lib/utils";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  AlertTriangle,
  ArrowUp,
  Minus,
  ArrowDown,
} from "lucide-react";

const PRIORITY_CONFIG: Record<
  TaskPriority,
  {
    icon: typeof ArrowUp;
    badgeClassName: string;
    iconContainerClassName: string;
  }
> = {
  urgent: {
    icon: AlertTriangle,
    badgeClassName: "bg-priority-urgent-bg text-priority-urgent-fg",
    iconContainerClassName:
      "bg-priority-urgent-bg text-priority-urgent-fg ring-1 ring-inset ring-priority-urgent-dot/70 shadow-[0_0_0_1px_hsl(var(--priority-urgent-dot)/0.24)_inset]",
  },
  high: {
    icon: ArrowUp,
    badgeClassName: "bg-priority-high-bg text-priority-high-fg",
    iconContainerClassName:
      "bg-priority-high-bg text-priority-high-fg ring-1 ring-inset ring-priority-high-dot/70 shadow-[0_0_0_1px_hsl(var(--priority-high-dot)/0.24)_inset]",
  },
  medium: {
    icon: Minus,
    badgeClassName: "bg-priority-medium-bg text-priority-medium-fg",
    iconContainerClassName:
      "bg-priority-medium-bg text-priority-medium-fg ring-1 ring-inset ring-priority-medium-dot/70 shadow-[0_0_0_1px_hsl(var(--priority-medium-dot)/0.24)_inset]",
  },
  low: {
    icon: ArrowDown,
    badgeClassName: "bg-priority-low-bg text-priority-low-fg",
    iconContainerClassName:
      "bg-priority-low-bg text-priority-low-fg ring-1 ring-inset ring-priority-low-dot/70 shadow-[0_0_0_1px_hsl(var(--priority-low-dot)/0.2)_inset]",
  },
};

export function PriorityBadge({ priority }: { priority: TaskPriority }) {
  const { icon: Icon, badgeClassName } = PRIORITY_CONFIG[priority];

  return (
    <span
      className={`badge-animated inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${badgeClassName}`}
    >
      <Icon className="h-3 w-3 shrink-0" />
      {TASK_PRIORITY_LABELS[priority]}
    </span>
  );
}

export function PriorityIcon({
  priority,
  className,
}: {
  priority: TaskPriority;
  className?: string;
}) {
  const { icon: Icon, iconContainerClassName } = PRIORITY_CONFIG[priority];

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span
          className={cn(
            "inline-flex h-7 w-7 items-center justify-center rounded-md transition-transform duration-150 hover:scale-[1.05]",
            iconContainerClassName,
            className
          )}
        >
          <Icon className="h-3.5 w-3.5" />
        </span>
      </TooltipTrigger>
      <TooltipContent side="top">
        Приоритет: {TASK_PRIORITY_LABELS[priority]}
      </TooltipContent>
    </Tooltip>
  );
}
