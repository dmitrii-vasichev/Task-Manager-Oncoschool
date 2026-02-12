"use client";

import { useState, useMemo } from "react";
import {
  CalendarDays,
  ListChecks,
  Video,
  ChevronLeft,
  ChevronRight,
  Search,
} from "lucide-react";
import Link from "next/link";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { useMeetings } from "@/hooks/useMeetings";
import { EmptyState } from "@/components/shared/EmptyState";

const PER_PAGE = 6;

function formatMeetingDate(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));

  if (days === 0) return "Сегодня";
  if (days === 1) return "Вчера";
  if (days < 7) {
    const weekday = date.toLocaleDateString("ru-RU", { weekday: "long" });
    return weekday.charAt(0).toUpperCase() + weekday.slice(1);
  }

  return date.toLocaleDateString("ru-RU", {
    day: "numeric",
    month: "long",
    year: now.getFullYear() !== date.getFullYear() ? "numeric" : undefined,
  });
}

export default function MeetingsPage() {
  const { meetings, loading } = useMeetings();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    if (!search.trim()) return meetings;
    const q = search.toLowerCase();
    return meetings.filter(
      (m) =>
        m.title?.toLowerCase().includes(q) ||
        m.parsed_summary?.toLowerCase().includes(q)
    );
  }, [meetings, search]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PER_PAGE));
  const currentPage = Math.min(page, totalPages);
  const paginated = filtered.slice(
    (currentPage - 1) * PER_PAGE,
    currentPage * PER_PAGE
  );

  if (loading) {
    return (
      <div className="space-y-6 animate-in fade-in duration-300">
        <Skeleton className="h-10 w-72 rounded-lg" />
        <div className="grid gap-4 md:grid-cols-2">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-44 rounded-2xl" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Search */}
      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
          placeholder="Поиск по встречам..."
          className="pl-9 h-10 rounded-xl bg-card border-border/60"
        />
      </div>

      {filtered.length === 0 ? (
        <EmptyState
          variant="meetings"
          title={search ? "Ничего не найдено" : "Пока нет встреч"}
          description={
            search
              ? "Попробуйте изменить поисковый запрос"
              : "Используйте /summary в Telegram или раздел Summary для парсинга Zoom."
          }
          actionLabel={!search ? "Создать из Summary" : undefined}
          actionHref={!search ? "/summary" : undefined}
        />
      ) : (
        <>
          {/* Grid */}
          <div className="grid gap-4 md:grid-cols-2">
            {paginated.map((meeting, i) => (
              <Link
                key={meeting.id}
                href={`/meetings/${meeting.id}`}
                className="group block"
              >
                <div
                  className={`
                    relative overflow-hidden rounded-2xl border border-border/60 bg-card p-5
                    hover:shadow-lg hover:shadow-primary/5 hover:-translate-y-0.5
                    animate-fade-in-up stagger-${i + 1}
                  `}
                >
                  {/* Decorative corner accent */}
                  <div className="absolute top-0 right-0 w-20 h-20 bg-gradient-to-bl from-primary/5 to-transparent rounded-bl-3xl" />

                  {/* Date chip */}
                  {meeting.meeting_date && (
                    <div className="flex items-center gap-1.5 text-xs text-muted-foreground mb-3">
                      <CalendarDays className="h-3.5 w-3.5" />
                      <span className="font-medium">
                        {formatMeetingDate(meeting.meeting_date)}
                      </span>
                    </div>
                  )}

                  {/* Title */}
                  <h3 className="text-base font-heading font-semibold text-foreground mb-2 pr-6 line-clamp-2 group-hover:text-primary">
                    {meeting.title || "Встреча без названия"}
                  </h3>

                  {/* Summary preview */}
                  {meeting.parsed_summary && (
                    <p className="text-sm text-muted-foreground line-clamp-2 mb-4 leading-relaxed">
                      {meeting.parsed_summary}
                    </p>
                  )}

                  {/* Footer badges */}
                  <div className="flex items-center gap-2 mt-auto pt-3 border-t border-border/40">
                    {meeting.decisions && meeting.decisions.length > 0 && (
                      <Badge
                        variant="secondary"
                        className="gap-1 rounded-lg text-2xs font-medium bg-status-done-bg text-status-done-fg"
                      >
                        <ListChecks className="h-3 w-3" />
                        {meeting.decisions.length}{" "}
                        {meeting.decisions.length === 1
                          ? "решение"
                          : meeting.decisions.length < 5
                            ? "решения"
                            : "решений"}
                      </Badge>
                    )}

                    <div className="flex-1" />

                    {/* Zoom icon on hover */}
                    <div className="h-7 w-7 rounded-lg bg-muted/60 flex items-center justify-center opacity-0 group-hover:opacity-100">
                      <Video className="h-3.5 w-3.5 text-muted-foreground" />
                    </div>
                  </div>
                </div>
              </Link>
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-1 pt-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={currentPage <= 1}
                className="h-9 w-9 rounded-xl flex items-center justify-center text-muted-foreground hover:bg-muted hover:text-foreground disabled:opacity-30 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>

              {Array.from({ length: totalPages }, (_, i) => i + 1).map(
                (num) => (
                  <button
                    key={num}
                    onClick={() => setPage(num)}
                    className={`
                      h-9 w-9 rounded-xl text-sm font-medium flex items-center justify-center
                      ${
                        num === currentPage
                          ? "bg-primary text-primary-foreground shadow-sm"
                          : "text-muted-foreground hover:bg-muted hover:text-foreground"
                      }
                    `}
                  >
                    {num}
                  </button>
                )
              )}

              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={currentPage >= totalPages}
                className="h-9 w-9 rounded-xl flex items-center justify-center text-muted-foreground hover:bg-muted hover:text-foreground disabled:opacity-30 disabled:cursor-not-allowed"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          )}

          {/* Results count */}
          <p className="text-center text-xs text-muted-foreground/60">
            {filtered.length}{" "}
            {filtered.length === 1
              ? "встреча"
              : filtered.length < 5
                ? "встречи"
                : "встреч"}
          </p>
        </>
      )}
    </div>
  );
}
