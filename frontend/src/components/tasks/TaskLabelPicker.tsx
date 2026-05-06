"use client";

import { useEffect, useMemo, useState } from "react";
import { Check, Loader2, Plus, Search, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { api } from "@/lib/api";
import type { TaskLabel } from "@/lib/types";

import { TaskLabelChips } from "./TaskLabelChips";

export function TaskLabelPicker({
  value,
  onChange,
  disabled = false,
  placeholder = "Метки",
}: {
  value: TaskLabel[];
  onChange: (labels: TaskLabel[]) => void;
  disabled?: boolean;
  placeholder?: string;
}) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [options, setOptions] = useState<TaskLabel[]>([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const selectedIds = useMemo(
    () => new Set(value.map((label) => label.id)),
    [value]
  );
  const normalizedSearch = search.trim();
  const canCreate =
    normalizedSearch.length > 0 &&
    !options.some(
      (label) => label.name.toLowerCase() === normalizedSearch.toLowerCase()
    );

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    setLoading(true);
    api
      .getTaskLabels({ search: normalizedSearch || undefined, limit: 20 })
      .then((labels) => {
        if (!cancelled) setOptions(labels);
      })
      .catch(() => {
        if (!cancelled) setOptions([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [open, normalizedSearch]);

  function toggleLabel(label: TaskLabel) {
    if (selectedIds.has(label.id)) {
      onChange(value.filter((item) => item.id !== label.id));
      return;
    }
    onChange([...value, label]);
  }

  async function createLabel() {
    if (!normalizedSearch || creating) return;
    setCreating(true);
    try {
      const label = await api.createTaskLabel({ name: normalizedSearch });
      if (!selectedIds.has(label.id)) {
        onChange([...value, label]);
      }
      setSearch("");
      setOpen(false);
    } finally {
      setCreating(false);
    }
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          type="button"
          variant="outline"
          disabled={disabled}
          className="h-auto min-h-10 w-full justify-start gap-2 px-3 py-2"
        >
          {value.length ? (
            <TaskLabelChips labels={value} maxVisible={3} />
          ) : (
            <span className="text-muted-foreground">{placeholder}</span>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent align="start" className="w-[320px] p-2">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Найти или создать метку"
            className="h-9 pl-9"
          />
        </div>
        <div className="mt-2 max-h-64 overflow-y-auto">
          {loading && (
            <div className="flex items-center gap-2 px-2 py-3 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Загрузка...
            </div>
          )}
          {!loading &&
            options.map((label) => (
              <button
                key={label.id}
                type="button"
                onClick={() => toggleLabel(label)}
                className="flex w-full items-center justify-between rounded-md px-2 py-2 text-left text-sm hover:bg-muted"
              >
                <span className="truncate">{label.name}</span>
                <span className="flex items-center gap-2 text-xs text-muted-foreground">
                  {label.usage_count}
                  {selectedIds.has(label.id) && (
                    <Check className="h-4 w-4 text-primary" />
                  )}
                </span>
              </button>
            ))}
          {!loading && canCreate && (
            <button
              type="button"
              onClick={() => void createLabel()}
              disabled={creating}
              className="flex w-full items-center gap-2 rounded-md px-2 py-2 text-sm font-medium text-primary hover:bg-primary/10 disabled:opacity-50"
            >
              {creating ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Plus className="h-4 w-4" />
              )}
              Создать "{normalizedSearch}"
            </button>
          )}
        </div>
        {value.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1.5 border-t border-border/60 pt-2">
            {value.map((label) => (
              <button
                key={label.id}
                type="button"
                onClick={() =>
                  onChange(value.filter((item) => item.id !== label.id))
                }
                className="inline-flex items-center gap-1 rounded-full bg-muted px-2 py-1 text-xs"
              >
                {label.name}
                <X className="h-3 w-3" />
              </button>
            ))}
          </div>
        )}
      </PopoverContent>
    </Popover>
  );
}
