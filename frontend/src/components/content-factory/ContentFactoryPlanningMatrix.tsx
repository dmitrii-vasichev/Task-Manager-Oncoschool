"use client";

import Link from "next/link";
import { AlertTriangle, CalendarClock, PlusCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ContentFactoryStatusBadge } from "@/components/content-factory/ContentFactoryStatusBadge";
import type {
  ContentFactoryPlanningMatrix as PlanningMatrix,
  ContentFactoryPlanningMatrixCell,
  ContentFactoryPlanningMatrixSummary,
} from "@/lib/contentFactoryUtils";
import type { CFPublication } from "@/lib/types";

function formatDateTime(value: string | null): string {
  if (!value) return "Без даты";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Без даты";
  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function publicationTitle(publication: CFPublication): string {
  return publication.title?.trim() || "Без названия";
}

export function ContentFactoryPlanningMatrix({
  matrix,
  summary,
  eventDate,
  creatingSlotKey,
  onCreateSlot,
}: {
  matrix: PlanningMatrix<CFPublication>;
  summary: ContentFactoryPlanningMatrixSummary;
  eventDate: string | null;
  creatingSlotKey: string | null;
  onCreateSlot: (cell: ContentFactoryPlanningMatrixCell<CFPublication>) => void;
}) {
  return (
    <section className="rounded-lg border border-border/70 bg-card shadow-sm">
      <div className="flex flex-col gap-3 border-b border-border/60 px-4 py-3 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <CalendarClock className="h-4 w-4 text-muted-foreground" />
            <h2 className="text-sm font-semibold text-foreground">
              Матрица каналов
            </h2>
          </div>
          <p className="mt-1 text-xs leading-5 text-muted-foreground">
            Ожидаемые публикации по шаблону кампании: что уже создано, чего не
            хватает и что появилось вне шаблона.
          </p>
        </div>
        <div className="grid grid-cols-2 gap-2 text-xs sm:grid-cols-4 lg:min-w-[420px]">
          <div className="rounded-md bg-muted/30 px-2 py-1.5">
            <p className="text-muted-foreground">Ожидается</p>
            <p className="font-semibold text-foreground">{summary.expected}</p>
          </div>
          <div className="rounded-md bg-primary/10 px-2 py-1.5 text-primary">
            <p>Создано</p>
            <p className="font-semibold">{summary.ready}</p>
          </div>
          <div className="rounded-md bg-amber-50 px-2 py-1.5 text-amber-700">
            <p>Не хватает</p>
            <p className="font-semibold">{summary.missing}</p>
          </div>
          <div className="rounded-md bg-muted/30 px-2 py-1.5">
            <p className="text-muted-foreground">Вне шаблона</p>
            <p className="font-semibold text-foreground">{summary.extra}</p>
          </div>
        </div>
      </div>

      {matrix.warnings.length > 0 && (
        <div className="space-y-1 border-b border-border/60 bg-amber-50/70 px-4 py-3 text-xs text-amber-800">
          {matrix.warnings.map((warning) => (
            <div key={warning} className="flex items-start gap-2">
              <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
              <p>{warning}</p>
            </div>
          ))}
        </div>
      )}

      {matrix.rows.length === 0 ? (
        <div className="px-4 py-8 text-center text-sm text-muted-foreground">
          У кампании нет шаблона публикаций. Добавьте шаблон кампании в
          справочниках или создавайте публикации вручную.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <div className="min-w-[720px]">
            <div
              className="grid border-b border-border/60 bg-muted/20 text-xs font-medium text-muted-foreground"
              style={{
                gridTemplateColumns: `minmax(180px,1.2fr) minmax(120px,0.8fr) repeat(${matrix.platforms.length}, minmax(160px,1fr))`,
              }}
            >
              <div className="px-4 py-2">Шаг</div>
              <div className="px-3 py-2">Плановая дата</div>
              {matrix.platforms.map((platform) => (
                <div key={platform.id} className="px-3 py-2">
                  {platform.display_name}
                </div>
              ))}
            </div>
            <div className="divide-y divide-border/60">
              {matrix.rows.map((row) => (
                <div
                  key={row.key}
                  className="grid"
                  style={{
                    gridTemplateColumns: `minmax(180px,1.2fr) minmax(120px,0.8fr) repeat(${matrix.platforms.length}, minmax(160px,1fr))`,
                  }}
                >
                  <div className="px-4 py-3">
                    <p className="text-sm font-medium text-foreground">
                      {row.label}
                    </p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {row.offsetLabel}
                    </p>
                  </div>
                  <div className="px-3 py-3 text-xs text-muted-foreground">
                    {formatDateTime(row.scheduled_at)}
                    {!eventDate && (
                      <p className="mt-1 text-amber-700">
                        Дата события не задана
                      </p>
                    )}
                  </div>
                  {matrix.platforms.map((platform) => {
                    const cell = row.cells.find(
                      (item) => item.platform.id === platform.id,
                    );
                    if (!cell) {
                      return (
                        <div
                          key={`${row.key}-${platform.id}`}
                          className="px-3 py-3 text-xs text-muted-foreground"
                        >
                          Не требуется
                        </div>
                      );
                    }

                    if (cell.publication) {
                      return (
                        <Link
                          key={cell.key}
                          href={`/content-factory/publications/${cell.publication.id}`}
                          className="block px-3 py-3 transition-colors hover:bg-muted/20"
                        >
                          <div className="space-y-1.5 rounded-md border border-border/70 bg-background px-2.5 py-2">
                            <p className="line-clamp-2 text-sm font-medium text-foreground">
                              {publicationTitle(cell.publication)}
                            </p>
                            <ContentFactoryStatusBadge
                              kind="publication"
                              status={cell.publication.status}
                            />
                          </div>
                        </Link>
                      );
                    }

                    return (
                      <div key={cell.key} className="px-3 py-3">
                        <div className="rounded-md border border-dashed border-amber-300 bg-amber-50/70 px-2.5 py-2">
                          <p className="text-xs font-medium text-amber-800">
                            Не хватает
                          </p>
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            className="mt-2 h-7 w-full gap-1.5 rounded-md px-2 text-xs"
                            disabled={creatingSlotKey === cell.key}
                            onClick={() => onCreateSlot(cell)}
                          >
                            <PlusCircle className="h-3.5 w-3.5" />
                            Создать
                          </Button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {matrix.extraPublications.length > 0 && (
        <div className="border-t border-border/60 px-4 py-3">
          <p className="text-xs font-semibold uppercase text-muted-foreground">
            Публикации вне шаблона
          </p>
          <div className="mt-2 flex flex-wrap gap-2">
            {matrix.extraPublications.map((publication) => (
              <Link
                key={publication.id}
                href={`/content-factory/publications/${publication.id}`}
                className="rounded-md border border-border/70 bg-muted/20 px-2.5 py-1.5 text-xs text-foreground transition-colors hover:border-primary/30 hover:bg-muted/40"
              >
                {publicationTitle(publication)}
              </Link>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
