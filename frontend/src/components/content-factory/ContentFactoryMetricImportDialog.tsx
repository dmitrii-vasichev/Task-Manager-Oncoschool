"use client";

import { useMemo, useState } from "react";
import { AlertTriangle, CheckCircle2, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/components/shared/Toast";
import { api } from "@/lib/api";
import {
  CF_CONFIDENCE_LABELS,
  CF_METRIC_SOURCE_LABELS,
  CF_METRIC_WINDOW_LABELS,
  formatContentFactoryMetricValue,
  parseContentFactoryMetricImportRows,
  type ContentFactoryMetricImportRow,
} from "@/lib/contentFactoryUtils";

const SAMPLE_IMPORT = `Окно | Метрика | Значение | Источник | Доверие | Заметка
24h | Просмотры | 1200 | TGStat | Высокое | экспорт из кабинета
7d | Регистрации | 34 | GetCourse | Среднее | ручной отчёт`;

function ImportRowPreview({ row }: { row: ContentFactoryMetricImportRow }) {
  if (!row.payload) {
    return (
      <div className="rounded-md border border-destructive/20 bg-destructive/5 px-3 py-2 text-sm">
        <div className="flex items-start gap-2 text-destructive">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <div className="min-w-0">
            <p className="font-medium">Строка {row.lineNumber}: {row.error}</p>
            <p className="mt-1 break-words text-xs text-muted-foreground">
              {row.raw}
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-md border border-border/70 bg-muted/10 px-3 py-2 text-sm">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate font-medium text-foreground">
            {row.payload.metric_name}
          </p>
          <p className="mt-1 text-xs leading-5 text-muted-foreground">
            {CF_METRIC_WINDOW_LABELS[row.payload.window]} ·{" "}
            {CF_METRIC_SOURCE_LABELS[row.payload.source]} · Доверие:{" "}
            {CF_CONFIDENCE_LABELS[row.payload.confidence].toLowerCase()}
          </p>
        </div>
        <p className="shrink-0 font-semibold text-foreground">
          {formatContentFactoryMetricValue(row.payload)}
        </p>
      </div>
      {row.payload.note ? (
        <p className="mt-1 text-xs leading-5 text-muted-foreground">
          {row.payload.note}
        </p>
      ) : null}
    </div>
  );
}

export function ContentFactoryMetricImportDialog({
  open,
  onOpenChange,
  publicationId,
  onImported,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  publicationId: string;
  onImported: () => void | Promise<void>;
}) {
  const { toastSuccess, toastError } = useToast();
  const [rawInput, setRawInput] = useState("");
  const [saving, setSaving] = useState(false);
  const preview = useMemo(
    () => parseContentFactoryMetricImportRows(rawInput),
    [rawInput],
  );
  const hasValidRows = preview.validRows.length > 0;

  function handleOpenChange(nextOpen: boolean) {
    if (!nextOpen && saving) return;
    onOpenChange(nextOpen);
  }

  async function handleImport() {
    if (!hasValidRows || saving) return;

    setSaving(true);
    try {
      for (const row of preview.validRows) {
        if (!row.payload) continue;
        await api.recordCFMetric(publicationId, {
          publication_id: publicationId,
          ...row.payload,
        });
      }
      toastSuccess(`Импортировано метрик: ${preview.validRows.length}`);
      await onImported();
      setRawInput("");
      onOpenChange(false);
    } catch (err) {
      toastError(
        err instanceof Error ? err.message : "Не удалось импортировать метрики",
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="max-h-[calc(100vh-1.5rem)] overflow-y-auto sm:max-w-[760px]">
        <DialogHeader>
          <DialogTitle className="text-lg">Импорт метрик</DialogTitle>
          <DialogDescription>
            Вставьте строки из таблицы или отчёта. Формат: окно, метрика,
            значение, источник, доверие, заметка.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="rounded-md border border-border/70 bg-muted/20 px-3 py-2 text-xs leading-5 text-muted-foreground">
            <p className="font-medium text-foreground">Пример</p>
            <pre className="mt-1 whitespace-pre-wrap font-mono text-2xs">
              {SAMPLE_IMPORT}
            </pre>
          </div>

          <Textarea
            value={rawInput}
            onChange={(event) => setRawInput(event.target.value)}
            placeholder="24h | Просмотры | 1200 | TGStat | Высокое | экспорт"
            className="min-h-40 border-border/70 bg-muted/20 text-sm"
            disabled={saving}
          />

          <div className="grid gap-2 sm:grid-cols-2">
            <div className="rounded-md border border-primary/20 bg-primary/5 px-3 py-2 text-sm text-primary">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4" />
                Готово к сохранению: {preview.validRows.length}
              </div>
            </div>
            <div className="rounded-md border border-destructive/20 bg-destructive/5 px-3 py-2 text-sm text-destructive">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4" />
                С ошибками: {preview.invalidRows.length}
              </div>
            </div>
          </div>

          {preview.rows.length > 0 ? (
            <div className="space-y-2">
              {preview.rows.map((row) => (
                <ImportRowPreview key={`${row.lineNumber}-${row.raw}`} row={row} />
              ))}
            </div>
          ) : (
            <p className="rounded-md border border-border/70 bg-muted/10 px-3 py-4 text-center text-sm text-muted-foreground">
              Вставьте строки, чтобы увидеть предпросмотр.
            </p>
          )}
        </div>

        <DialogFooter className="gap-2 pt-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={saving}
            onClick={() => onOpenChange(false)}
          >
            Отмена
          </Button>
          <Button
            type="button"
            size="sm"
            disabled={!hasValidRows || saving}
            onClick={() => void handleImport()}
          >
            {saving && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
            Импортировать
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
