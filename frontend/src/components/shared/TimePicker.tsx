"use client";

import * as React from "react";
import { Clock } from "lucide-react";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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

const TIME_RE = /^([01]\d|2[0-3]):([0-5]\d)$/;

function getMinutes(step: number) {
  return Array.from({ length: Math.ceil(60 / step) }, (_, i) =>
    String(i * step).padStart(2, "0")
  );
}

function parseTimeValue(value: string): { hours: string; minutes: string } | null {
  const match = TIME_RE.exec(value.trim());
  if (!match) return null;
  return { hours: match[1], minutes: match[2] };
}

function sanitizeTimePart(raw: string): string {
  return raw.replace(/\D/g, "").slice(0, 2);
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
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
  const [manualHours, setManualHours] = React.useState("");
  const [manualMinutes, setManualMinutes] = React.useState("");

  const minutes = React.useMemo(() => getMinutes(minuteStep), [minuteStep]);

  const parsed = React.useMemo(() => parseTimeValue(value), [value]);

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

  React.useEffect(() => {
    if (!open) return;
    setManualHours(parsed?.hours ?? "");
    setManualMinutes(parsed?.minutes ?? "");
  }, [open, parsed?.hours, parsed?.minutes]);

  function commitManualTime(
    hoursRaw: string = manualHours,
    minutesRaw: string = manualMinutes
  ) {
    const nextHourSource = hoursRaw === "" ? (parsed?.hours ?? "00") : hoursRaw;
    const nextMinuteSource = minutesRaw === "" ? (parsed?.minutes ?? "00") : minutesRaw;

    const nextHourNumber = Number(nextHourSource);
    const nextMinuteNumber = Number(nextMinuteSource);
    if (!Number.isFinite(nextHourNumber) || !Number.isFinite(nextMinuteNumber)) {
      return;
    }

    const normalizedHour = String(clamp(nextHourNumber, 0, 23)).padStart(2, "0");
    const normalizedMinute = String(clamp(nextMinuteNumber, 0, 59)).padStart(2, "0");
    const nextValue = `${normalizedHour}:${normalizedMinute}`;

    setManualHours(normalizedHour);
    setManualMinutes(normalizedMinute);
    if (nextValue !== value) {
      onChange(nextValue);
    }
  }

  function handleHourClick(hour: string) {
    const min = parsed?.minutes || "00";
    const nextValue = `${hour}:${min}`;
    onChange(nextValue);
    setManualHours(hour);
    setManualMinutes(min);
  }

  function handleMinuteClick(minute: string) {
    const hr = parsed?.hours || "00";
    const nextValue = `${hr}:${minute}`;
    onChange(nextValue);
    setManualHours(hr);
    setManualMinutes(minute);
  }

  function handleManualKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") {
      e.preventDefault();
      commitManualTime();
    }
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
      <PopoverContent className="w-[228px] p-0" align="start">
        <div className="border-b border-border/60 p-2">
          <div className="mb-1 text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
            Вручную
          </div>
          <div className="flex items-center gap-1.5">
            <Input
              value={manualHours}
              onChange={(e) => setManualHours(sanitizeTimePart(e.target.value))}
              onBlur={() => commitManualTime(manualHours, manualMinutes)}
              onKeyDown={handleManualKeyDown}
              inputMode="numeric"
              placeholder="ЧЧ"
              className="h-8 w-14 rounded-lg px-2 text-center text-sm"
              aria-label="Часы"
            />
            <span className="text-sm font-medium text-muted-foreground">:</span>
            <Input
              value={manualMinutes}
              onChange={(e) => setManualMinutes(sanitizeTimePart(e.target.value))}
              onBlur={() => commitManualTime(manualHours, manualMinutes)}
              onKeyDown={handleManualKeyDown}
              inputMode="numeric"
              placeholder="ММ"
              className="h-8 w-14 rounded-lg px-2 text-center text-sm"
              aria-label="Минуты"
            />
          </div>
        </div>
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
