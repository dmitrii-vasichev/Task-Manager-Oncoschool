"use client";

import { X } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  CF_BUNDLE_STATUS_LABELS,
  CF_BUNDLE_STATUSES,
  CF_PRODUCT_STREAM_LABELS,
  type ContentFactoryBundleFilterValues,
} from "@/lib/contentFactoryUtils";
import type { CFProductStream, TeamMember } from "@/lib/types";

export const EMPTY_CONTENT_FACTORY_BUNDLE_FILTERS: ContentFactoryBundleFilterValues = {
  status: "all",
  product_stream: "",
  owner_id: "",
};

function FilterSelect({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: Array<{ value: string; label: string }>;
}) {
  return (
    <div className="min-w-0 space-y-1">
      <span className="text-2xs font-medium uppercase text-muted-foreground">
        {label}
      </span>
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger
          aria-label={label}
          className="h-8 w-full border-border/70 bg-background px-2.5 text-xs shadow-sm transition-colors hover:border-primary/30 focus:border-primary/40 focus:ring-primary/20"
        >
          <SelectValue />
        </SelectTrigger>
        <SelectContent className="z-[60] max-h-64 border-border/70 shadow-xl">
          {options.map((option) => (
            <SelectItem key={option.value} value={option.value}>
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}

function hasActiveFilters(filters: ContentFactoryBundleFilterValues): boolean {
  return (
    filters.status !== "all" ||
    Boolean(filters.product_stream) ||
    Boolean(filters.owner_id)
  );
}

export function ContentFactoryBundleFilters({
  filters,
  members,
  onChange,
}: {
  filters: ContentFactoryBundleFilterValues;
  members: TeamMember[];
  onChange: (filters: ContentFactoryBundleFilterValues) => void;
}) {
  const activeFilters = hasActiveFilters(filters);
  const productStreamOptions = Object.entries(CF_PRODUCT_STREAM_LABELS) as Array<
    [CFProductStream, string]
  >;

  return (
    <div className="space-y-3">
      <div className="flex justify-end">
        {activeFilters && (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="h-8 gap-1.5 px-2.5 text-xs text-muted-foreground hover:text-foreground"
            onClick={() => onChange(EMPTY_CONTENT_FACTORY_BUNDLE_FILTERS)}
          >
            <X className="h-3.5 w-3.5" />
            Сбросить
          </Button>
        )}
      </div>

      <div className="grid gap-2 sm:grid-cols-3">
        <FilterSelect
          label="Статус"
          value={filters.status}
          onChange={(value) =>
            onChange({
              ...filters,
              status: value as ContentFactoryBundleFilterValues["status"],
            })
          }
          options={[
            { value: "all", label: "Все статусы" },
            ...CF_BUNDLE_STATUSES.map((status) => ({
              value: status,
              label: CF_BUNDLE_STATUS_LABELS[status],
            })),
          ]}
        />
        <FilterSelect
          label="Поток"
          value={filters.product_stream || "all"}
          onChange={(value) =>
            onChange({
              ...filters,
              product_stream:
                value === "all"
                  ? ""
                  : (value as ContentFactoryBundleFilterValues["product_stream"]),
            })
          }
          options={[
            { value: "all", label: "Все потоки" },
            ...productStreamOptions.map(([value, label]) => ({ value, label })),
          ]}
        />
        <FilterSelect
          label="Владелец"
          value={filters.owner_id || "all"}
          onChange={(value) =>
            onChange({ ...filters, owner_id: value === "all" ? "" : value })
          }
          options={[
            { value: "all", label: "Все владельцы" },
            ...members.map((member) => ({
              value: member.id,
              label: member.full_name,
            })),
          ]}
        />
      </div>
    </div>
  );
}
