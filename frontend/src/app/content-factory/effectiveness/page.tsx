"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { BarChart3, RefreshCw, Search } from "lucide-react";
import { ContentFactoryEffectivenessTable } from "@/components/content-factory/ContentFactoryEffectivenessTable";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/shared/Toast";
import { api } from "@/lib/api";
import {
  buildContentFactoryEffectivenessRows,
  filterContentFactoryEffectivenessRows,
  summarizeContentFactoryEffectiveness,
  type ContentFactoryEffectivenessMetricHealth,
} from "@/lib/contentFactoryUtils";
import type {
  CFBundle,
  CFFormat,
  CFMetricSnapshot,
  CFPlatform,
  CFPublication,
  CFPublicationSegmentTarget,
} from "@/lib/types";

type MetricHealthFilter = "all" | ContentFactoryEffectivenessMetricHealth;

const METRIC_HEALTH_FILTER_LABELS: Record<MetricHealthFilter, string> = {
  all: "Все замеры",
  fresh: "Свежие",
  stale: "Устарели",
  missing: "Нет замеров",
};

function EffectivenessLoadingSkeleton() {
  return (
    <div className="space-y-4 animate-in fade-in duration-300">
      <div className="flex items-center justify-between gap-3">
        <div className="space-y-2">
          <Skeleton className="h-5 w-40 rounded-md" />
          <Skeleton className="h-3 w-96 rounded-md" />
        </div>
        <Skeleton className="h-8 w-28 rounded-md" />
      </div>
      <div className="grid gap-3 md:grid-cols-5">
        {Array.from({ length: 5 }).map((_, index) => (
          <Skeleton key={index} className="h-20 rounded-lg" />
        ))}
      </div>
      <Skeleton className="h-20 rounded-lg" />
      <Skeleton className="h-36 rounded-lg" />
      <Skeleton className="h-36 rounded-lg" />
    </div>
  );
}

function SummaryCard({
  label,
  value,
  helper,
}: {
  label: string;
  value: number;
  helper: string;
}) {
  return (
    <div className="rounded-lg border border-border/70 bg-card px-3 py-3 shadow-sm">
      <span className="block text-2xs uppercase text-muted-foreground">
        {label}
      </span>
      <span className="mt-1 block text-xl font-semibold text-foreground">
        {value}
      </span>
      <span className="mt-1 block text-xs text-muted-foreground">{helper}</span>
    </div>
  );
}

async function mapWithConcurrency<TItem, TResult>(
  items: TItem[],
  limit: number,
  mapper: (item: TItem) => Promise<TResult>,
): Promise<TResult[]> {
  const results: TResult[] = new Array(items.length);
  let nextIndex = 0;
  const workerCount = Math.min(limit, items.length);

  await Promise.all(
    Array.from({ length: workerCount }, async () => {
      while (nextIndex < items.length) {
        const currentIndex = nextIndex;
        nextIndex += 1;
        results[currentIndex] = await mapper(items[currentIndex]);
      }
    }),
  );

  return results;
}

function objectiveLabel(value: string): string {
  if (value === "all") return "Все цели";
  if (value === "unknown") return "Цель не указана";
  return value;
}

export default function ContentFactoryEffectivenessPage() {
  const { toastError } = useToast();
  const [publications, setPublications] = useState<CFPublication[]>([]);
  const [bundles, setBundles] = useState<CFBundle[]>([]);
  const [platforms, setPlatforms] = useState<CFPlatform[]>([]);
  const [formats, setFormats] = useState<CFFormat[]>([]);
  const [segmentTargetsByPublicationId, setSegmentTargetsByPublicationId] =
    useState<Record<string, CFPublicationSegmentTarget[]>>({});
  const [metricsByPublicationId, setMetricsByPublicationId] =
    useState<Record<string, CFMetricSnapshot[]>>({});
  const [search, setSearch] = useState("");
  const [objectiveFilter, setObjectiveFilter] = useState("all");
  const [metricHealthFilter, setMetricHealthFilter] =
    useState<MetricHealthFilter>("all");
  const [platformFilter, setPlatformFilter] = useState("all");
  const [partialEvidence, setPartialEvidence] = useState(false);
  const [loading, setLoading] = useState(true);
  const latestRequestSeqRef = useRef(0);

  const fetchData = useCallback(async () => {
    const requestSeq = latestRequestSeqRef.current + 1;
    latestRequestSeqRef.current = requestSeq;
    const isLatestRequest = () => latestRequestSeqRef.current === requestSeq;

    setLoading(true);
    setPartialEvidence(false);
    try {
      const [publicationRes, bundleRes, platformRes, formatRes] =
        await Promise.all([
          api.getCFPublications({ limit: 500 }),
          api.getCFBundles({ limit: 500 }),
          api.getCFPlatforms(),
          api.getCFFormats(),
        ]);

      let secondaryFailed = false;
      const [targetEntries, metricEntries] = await Promise.all([
        mapWithConcurrency(publicationRes, 8, async (publication) => {
          try {
            const targets = await api.getCFPublicationSegmentTargets(
              publication.id,
            );
            return [publication.id, targets] as const;
          } catch {
            secondaryFailed = true;
            return [publication.id, [] as CFPublicationSegmentTarget[]] as const;
          }
        }),
        mapWithConcurrency(publicationRes, 8, async (publication) => {
          try {
            const metrics = await api.getCFMetrics(publication.id);
            return [publication.id, metrics] as const;
          } catch {
            secondaryFailed = true;
            return [publication.id, [] as CFMetricSnapshot[]] as const;
          }
        }),
      ]);

      if (!isLatestRequest()) return;
      setPublications(publicationRes);
      setBundles(bundleRes);
      setPlatforms(platformRes);
      setFormats(formatRes);
      setSegmentTargetsByPublicationId(Object.fromEntries(targetEntries));
      setMetricsByPublicationId(Object.fromEntries(metricEntries));
      setPartialEvidence(secondaryFailed);
      if (secondaryFailed) {
        toastError("Часть данных по эффективности не удалось загрузить");
      }
    } catch (err) {
      if (!isLatestRequest()) return;
      toastError(
        err instanceof Error
          ? err.message
          : "Не удалось загрузить эффективность публикаций",
      );
      setPublications([]);
      setBundles([]);
      setPlatforms([]);
      setFormats([]);
      setSegmentTargetsByPublicationId({});
      setMetricsByPublicationId({});
    } finally {
      if (isLatestRequest()) setLoading(false);
    }
  }, [toastError]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const rows = useMemo(
    () =>
      buildContentFactoryEffectivenessRows({
        now: new Date(),
        freshnessDays: 8,
        publications,
        bundles,
        platforms,
        formats,
        segmentTargetsByPublicationId,
        metricsByPublicationId,
      }),
    [
      bundles,
      formats,
      metricsByPublicationId,
      platforms,
      publications,
      segmentTargetsByPublicationId,
    ],
  );

  const summary = useMemo(
    () => summarizeContentFactoryEffectiveness(rows),
    [rows],
  );

  const objectiveOptions = useMemo(
    () =>
      Array.from(new Set(rows.map((row) => row.objective))).sort((left, right) =>
        left.localeCompare(right, "ru"),
      ),
    [rows],
  );

  const filteredRows = useMemo(
    () =>
      filterContentFactoryEffectivenessRows(rows, {
        search,
        objective: objectiveFilter,
        metricHealth: metricHealthFilter,
        platformId: platformFilter,
      }),
    [metricHealthFilter, objectiveFilter, platformFilter, rows, search],
  );

  if (loading) {
    return <EffectivenessLoadingSkeleton />;
  }

  return (
    <div className="space-y-4 animate-in fade-in duration-300">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex min-w-0 items-start gap-3">
          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <BarChart3 className="h-5 w-5" />
          </span>
          <div className="min-w-0">
            <h1 className="text-xl font-semibold leading-7 text-foreground">
              Эффективность
            </h1>
            <p className="text-sm text-muted-foreground">
              Ручные замеры, свежесть evidence и публикации без данных к
              ретроспективе
            </p>
          </div>
        </div>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="h-8 w-full gap-1.5 px-2.5 text-xs sm:w-auto"
          onClick={() => void fetchData()}
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Обновить
        </Button>
      </div>

      <div className="grid gap-3 md:grid-cols-5">
        <SummaryCard
          label="Публикации"
          value={summary.totalPublications}
          helper="в выборке"
        />
        <SummaryCard
          label="Опубликовано"
          value={summary.publishedPublications}
          helper="можно оценивать"
        />
        <SummaryCard
          label="С замерами"
          value={summary.rowsWithEvidence}
          helper={partialEvidence ? "загружено частично" : "есть evidence"}
        />
        <SummaryCard
          label="Без замеров"
          value={summary.rowsWithoutEvidence}
          helper="нужно заполнить"
        />
        <SummaryCard
          label="Устарели"
          value={summary.staleEvidenceRows}
          helper="проверьте перед ретро"
        />
      </div>

      <div className="grid gap-3 rounded-lg border border-border/70 bg-card px-4 py-3 shadow-sm xl:grid-cols-[1fr_auto]">
        <div className="grid gap-2 md:grid-cols-[minmax(0,1fr)_150px_150px_180px]">
          <div className="relative">
            <Search className="pointer-events-none absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Поиск по публикациям, кампаниям, целям, метрикам"
              className="h-9 border-border/70 bg-muted/20 pl-8 text-sm"
            />
          </div>
          <Select value={objectiveFilter} onValueChange={setObjectiveFilter}>
            <SelectTrigger className="h-9 border-border/70 bg-muted/20 text-sm">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="z-[70] border-border/70 shadow-xl">
              <SelectItem value="all">Все цели</SelectItem>
              {objectiveOptions.map((objective) => (
                <SelectItem key={objective} value={objective}>
                  {objectiveLabel(objective)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select
            value={metricHealthFilter}
            onValueChange={(value) =>
              setMetricHealthFilter(value as MetricHealthFilter)
            }
          >
            <SelectTrigger className="h-9 border-border/70 bg-muted/20 text-sm">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="z-[70] border-border/70 shadow-xl">
              {Object.entries(METRIC_HEALTH_FILTER_LABELS).map(
                ([value, label]) => (
                  <SelectItem key={value} value={value}>
                    {label}
                  </SelectItem>
                ),
              )}
            </SelectContent>
          </Select>
          <Select value={platformFilter} onValueChange={setPlatformFilter}>
            <SelectTrigger className="h-9 border-border/70 bg-muted/20 text-sm">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="z-[70] border-border/70 shadow-xl">
              <SelectItem value="all">Все площадки</SelectItem>
              {platforms.map((platform) => (
                <SelectItem key={platform.id} value={platform.id}>
                  {platform.display_name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <p className="self-center text-sm text-muted-foreground">
          {filteredRows.length} строк показано
        </p>
      </div>

      {partialEvidence ? (
        <div className="rounded-lg border border-amber-500/20 bg-amber-500/10 px-4 py-3 text-sm text-amber-800">
          Часть ручных замеров или аудиторных связей не загрузилась. Таблица
          показывает доступные данные.
        </div>
      ) : null}

      <ContentFactoryEffectivenessTable rows={filteredRows} />
    </div>
  );
}
