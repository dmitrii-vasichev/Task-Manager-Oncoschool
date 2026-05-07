"use client";

import { ExternalLink, FileText, StickyNote } from "lucide-react";
import type { MeetingBoardSettings } from "@/lib/types";
import { sanitizeMeetingBoardMaterialUrl } from "./meetingBoardPresentationUtils";

interface MeetingBoardMaterialsProps {
  settings: MeetingBoardSettings;
}

export function MeetingBoardMaterials({ settings }: MeetingBoardMaterialsProps) {
  const materials = settings.materials || [];

  return (
    <section className="rounded-xl border border-border/70 bg-card p-4">
      <div className="mb-3 flex items-center gap-2">
        <FileText className="h-4 w-4 text-primary" />
        <h2 className="text-sm font-heading font-semibold text-foreground">
          Материалы
        </h2>
      </div>

      {materials.length > 0 ? (
        <div className="space-y-2">
          {materials.map((material) => {
            const safeUrl = sanitizeMeetingBoardMaterialUrl(material.url);
            const content = (
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="break-words text-sm font-medium text-foreground">
                    {material.title}
                  </p>
                  {material.description && (
                    <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">
                      {material.description}
                    </p>
                  )}
                  {!safeUrl && (
                    <p className="mt-1 text-2xs text-destructive">
                      Ссылка недоступна
                    </p>
                  )}
                </div>
                {safeUrl && (
                  <ExternalLink className="mt-0.5 h-3.5 w-3.5 shrink-0 text-muted-foreground" />
                )}
              </div>
            );

            if (!safeUrl) {
              return (
                <div
                  key={material.id}
                  className="rounded-lg border border-border/60 bg-background/60 p-3"
                >
                  {content}
                </div>
              );
            }

            return (
              <a
                key={material.id}
                href={safeUrl}
                target="_blank"
                rel="noreferrer"
                className="block rounded-lg border border-border/60 bg-background/60 p-3 transition-colors hover:border-primary/30 hover:bg-accent/40"
              >
                {content}
              </a>
            );
          })}
        </div>
      ) : (
        <div className="rounded-lg border border-dashed border-border/70 bg-background/45 px-3 py-6 text-center text-xs text-muted-foreground">
          Материалы пока не добавлены
        </div>
      )}

      {settings.board_notes && (
        <div className="mt-4 rounded-lg border border-border/60 bg-muted/35 p-3">
          <div className="mb-2 flex items-center gap-1.5 text-xs font-medium text-foreground">
            <StickyNote className="h-3.5 w-3.5 text-primary" />
            Заметки
          </div>
          <p className="whitespace-pre-wrap break-words text-sm leading-6 text-muted-foreground">
            {settings.board_notes}
          </p>
        </div>
      )}
    </section>
  );
}
