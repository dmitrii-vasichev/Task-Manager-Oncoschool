"use client";

import * as React from "react";
import { Clock } from "lucide-react";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";

interface TimePickerProps {
  /** Current time value as "HH:MM" string, e.g. "09:00" */
  value: string;
  /** Called with "HH:MM" string when user selects a time */
  onChange: (value: string) => void;
  /** Placeholder text when no value is set */
  placeholder?: string;
  /** Minute step interval */
  minuteStep?: 1 | 5 | 10 | 15;
  /** Disabled state */
  disabled?: boolean;
  /** Additional CSS classes for the trigger button */
  className?: string;
}

const HOURS = Array.from({ length: 24 }, (_, i) =>
  String(i).padStart(2, "0")
);

function getMinutes(step: number) {
  return Array.from({ length: Math.ceil(60 / step) }, (_, i) =>
    String(i * step).padStart(2, "0")
  );
}

export function TimePicker({
  value,
  onChange,
  placeholder = "Время",
  minuteStep = 5,
  disabled = false,
  className,
}: TimePickerProps) {
  const [open, setOpen] = React.useState(false);

  const minutes = React.useMemo(() => getMinutes(minuteStep), [minuteStep]);

  const parsed = value
    ? { hours: value.split(":")[0], minutes: value.split(":")[1] }
    : null;

  const selectedHourRef = React.useRef<HTMLButtonElement>(null);
  const selectedMinuteRef = React.useRef<HTMLButtonElement>(null);

  React.useEffect(() => {
    if (open) {
      requestAnimationFrame(() => {
        selectedHourRef.current?.scrollIntoView({ block: "nearest" });
        selectedMinuteRef.current?.scrollIntoView({ block: "nearest" });
      });
    }
  }, [open]);

  function handleHourClick(hour: string) {
    const min = parsed?.minutes || "00";
    onChange(`${hour}:${min}`);
  }

  function handleMinuteClick(minute: string) {
    const hr = parsed?.hours || "00";
    onChange(`${hr}:${minute}`);
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          disabled={disabled}
          className={cn(
            "justify-start text-left font-normal gap-2",
            !value && "text-muted-foreground",
            className
          )}
        >
          <Clock className="h-4 w-4 opacity-60 shrink-0" />
          {value || placeholder}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0" align="start">
        <div className="flex">
          {/* Hours column */}
          <div className="flex flex-col">
            <div className="px-3 py-2 text-[11px] font-medium text-muted-foreground uppercase tracking-wider">
              Часы
            </div>
            <ScrollArea className="h-[200px]">
              <div className="flex flex-col gap-0.5 p-1">
                {HOURS.map((hour) => {
                  const isSelected = parsed?.hours === hour;
                  return (
                    <button
                      key={hour}
                      ref={isSelected ? selectedHourRef : undefined}
                      onClick={() => handleHourClick(hour)}
                      className={cn(
                        "h-8 w-12 rounded-lg text-sm font-medium transition-colors cursor-pointer",
                        isSelected
                          ? "bg-primary text-primary-foreground"
                          : "hover:bg-muted"
                      )}
                    >
                      {hour}
                    </button>
                  );
                })}
              </div>
            </ScrollArea>
          </div>

          <Separator orientation="vertical" className="h-auto" />

          {/* Minutes column */}
          <div className="flex flex-col">
            <div className="px-3 py-2 text-[11px] font-medium text-muted-foreground uppercase tracking-wider">
              Мин.
            </div>
            <ScrollArea className="h-[200px]">
              <div className="flex flex-col gap-0.5 p-1">
                {minutes.map((minute) => {
                  const isSelected = parsed?.minutes === minute;
                  return (
                    <button
                      key={minute}
                      ref={isSelected ? selectedMinuteRef : undefined}
                      onClick={() => handleMinuteClick(minute)}
                      className={cn(
                        "h-8 w-12 rounded-lg text-sm font-medium transition-colors cursor-pointer",
                        isSelected
                          ? "bg-primary text-primary-foreground"
                          : "hover:bg-muted"
                      )}
                    >
                      {minute}
                    </button>
                  );
                })}
              </div>
            </ScrollArea>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}
