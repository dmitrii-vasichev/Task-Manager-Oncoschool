"use client";

import { useMemo, useState } from "react";
import { AlertTriangle, Clipboard, Layers3 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useToast } from "@/components/shared/Toast";
import {
  buildContentFactoryPublicationVariants,
  type ContentFactoryPublicationVariantKey,
} from "@/lib/contentFactoryUtils";
import type {
  CFBundle,
  CFFormat,
  CFPlatform,
  CFPublication,
} from "@/lib/types";

function VariantPreview({ value }: { value: string }) {
  return (
    <pre className="max-h-72 overflow-auto whitespace-pre-wrap rounded-md bg-muted/25 px-3 py-3 text-sm leading-6 text-foreground">
      {value}
    </pre>
  );
}

export function ContentFactoryPublicationVariants({
  publication,
  platform,
  format,
  bundle,
}: {
  publication: CFPublication;
  platform: CFPlatform | null;
  format: CFFormat | null;
  bundle: CFBundle | null;
}) {
  const { toastSuccess, toastError } = useToast();
  const variants = useMemo(
    () =>
      buildContentFactoryPublicationVariants({
        publication,
        platform,
        format,
        bundle,
      }),
    [bundle, format, platform, publication],
  );
  const [selectedKey, setSelectedKey] =
    useState<ContentFactoryPublicationVariantKey>("telegram");
  const selectedVariant =
    variants.variants.find((variant) => variant.key === selectedKey) ??
    variants.variants[0];

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(selectedVariant.copyText);
      toastSuccess("Адаптация скопирована");
    } catch {
      toastError("Не удалось скопировать адаптацию");
    }
  }

  return (
    <section className="rounded-lg border border-border/70 bg-card shadow-sm">
      <div className="flex flex-col gap-3 border-b border-border/60 px-4 py-3 md:flex-row md:items-start md:justify-between">
        <div className="flex min-w-0 items-start gap-2">
          <Layers3 className="mt-0.5 h-4 w-4 text-muted-foreground" />
          <div className="min-w-0">
            <h2 className="text-sm font-semibold text-foreground">Адаптации</h2>
            <p className="mt-1 text-xs leading-5 text-muted-foreground">
              Ручные заготовки под каналы без AI и автопубликации.
            </p>
          </div>
        </div>
        <Button
          type="button"
          size="sm"
          className="h-8 shrink-0 gap-1.5 rounded-md px-3 text-xs"
          onClick={() => void handleCopy()}
        >
          <Clipboard className="h-3.5 w-3.5" />
          Скопировать адаптацию
        </Button>
      </div>

      <div className="space-y-4 px-4 py-4">
        <div className="grid gap-2 sm:grid-cols-3">
          {variants.contextRows.map((row) => (
            <div
              key={row.label}
              className="min-w-0 rounded-md border border-border/60 bg-muted/15 px-3 py-2"
            >
              <p className="text-xs uppercase text-muted-foreground">
                {row.label}
              </p>
              <p className="mt-1 truncate text-sm font-medium text-foreground">
                {row.value}
              </p>
            </div>
          ))}
        </div>

        <div className="flex gap-2 overflow-x-auto pb-1">
          {variants.variants.map((variant) => (
            <button
              key={variant.key}
              type="button"
              className={`shrink-0 rounded-md border px-3 py-2 text-sm font-medium transition-colors ${
                selectedVariant.key === variant.key
                  ? "border-primary bg-primary text-primary-foreground"
                  : "border-border bg-background text-muted-foreground hover:text-foreground"
              }`}
              onClick={() => setSelectedKey(variant.key)}
            >
              {variant.channelLabel}
            </button>
          ))}
        </div>

        <div className="grid gap-3 lg:grid-cols-[220px_minmax(0,1fr)]">
          <div className="space-y-2 rounded-md border border-border/70 bg-muted/10 px-3 py-3">
            <p className="text-xs uppercase text-muted-foreground">Канал</p>
            <p className="text-sm font-semibold text-foreground">
              {selectedVariant.channelLabel}
            </p>
            <p className="text-xs uppercase text-muted-foreground">Назначение</p>
            <p className="text-sm leading-5 text-foreground">
              {selectedVariant.useCase}
            </p>
            <p className="text-xs uppercase text-muted-foreground">Длина</p>
            <p className="text-sm text-foreground">{selectedVariant.lengthHint}</p>
          </div>

          <div className="min-w-0 space-y-2">
            {selectedVariant.warnings.length > 0 ? (
              <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs leading-5 text-amber-900">
                <div className="flex gap-2">
                  <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                  <div>
                    {selectedVariant.warnings.map((warning) => (
                      <p key={warning}>{warning}</p>
                    ))}
                  </div>
                </div>
              </div>
            ) : null}
            <VariantPreview value={selectedVariant.copyText} />
          </div>
        </div>
      </div>
    </section>
  );
}
