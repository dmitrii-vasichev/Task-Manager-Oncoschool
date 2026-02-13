"use client";

import { useState } from "react";
import {
  Video,
  ExternalLink,
  Copy,
  Check,
  PlayCircle,
} from "lucide-react";
import type { Meeting } from "@/lib/types";

interface ZoomBlockProps {
  meeting: Meeting;
  isModerator: boolean;
  onCreateZoom?: () => Promise<void>;
}

export function ZoomBlock({ meeting }: ZoomBlockProps) {
  const [copied, setCopied] = useState(false);

  const handleCopyId = async () => {
    if (!meeting.zoom_meeting_id) return;
    await navigator.clipboard.writeText(meeting.zoom_meeting_id);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (
    !meeting.zoom_join_url &&
    !meeting.zoom_meeting_id &&
    !meeting.zoom_recording_url
  ) {
    return (
      <div className="rounded-2xl border border-dashed border-border/50 bg-muted/20 p-4 flex items-center gap-3">
        <div className="h-9 w-9 rounded-xl bg-muted/60 flex items-center justify-center">
          <Video className="h-4.5 w-4.5 text-muted-foreground/40" />
        </div>
        <div className="flex-1">
          <p className="text-sm text-muted-foreground">Zoom не подключён</p>
          <p className="text-xs text-muted-foreground/60">
            Встреча создана без Zoom-конференции
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-border/60 bg-card p-4 space-y-3">
      <div className="flex items-center gap-2">
        <div className="h-8 w-8 rounded-xl bg-blue-500/10 flex items-center justify-center">
          <Video className="h-4 w-4 text-blue-600" />
        </div>
        <span className="text-sm font-heading font-semibold">Zoom</span>
      </div>

      <div className="flex items-center gap-2 flex-wrap">
        {/* Join link */}
        {meeting.zoom_join_url && meeting.status !== "completed" && (
          <a
            href={meeting.zoom_join_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-sm font-medium text-blue-600 hover:text-blue-700 bg-blue-500/10 rounded-xl px-3 py-2 hover:bg-blue-500/15 transition-colors"
          >
            <Video className="h-3.5 w-3.5" />
            Подключиться
            <ExternalLink className="h-3 w-3" />
          </a>
        )}

        {/* Recording link */}
        {meeting.zoom_recording_url && (
          <a
            href={meeting.zoom_recording_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-sm font-medium text-emerald-600 hover:text-emerald-700 bg-emerald-500/10 rounded-xl px-3 py-2 hover:bg-emerald-500/15 transition-colors"
          >
            <PlayCircle className="h-3.5 w-3.5" />
            Запись
            <ExternalLink className="h-3 w-3" />
          </a>
        )}

        {/* Meeting ID */}
        {meeting.zoom_meeting_id && (
          <button
            onClick={handleCopyId}
            className="inline-flex items-center gap-1.5 text-xs text-muted-foreground bg-muted/40 rounded-lg px-2.5 py-1.5 hover:bg-muted/60 transition-colors"
          >
            <span className="font-mono">ID: {meeting.zoom_meeting_id}</span>
            {copied ? (
              <Check className="h-3 w-3 text-emerald-500" />
            ) : (
              <Copy className="h-3 w-3" />
            )}
          </button>
        )}
      </div>
    </div>
  );
}
