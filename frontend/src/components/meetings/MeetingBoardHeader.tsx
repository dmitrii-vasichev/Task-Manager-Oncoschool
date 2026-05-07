"use client";

import Link from "next/link";
import { ArrowLeft, CalendarDays, Users } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { formatMeetingHeaderDateTime } from "@/lib/meetingDateTime";
import type { Meeting, TeamMember } from "@/lib/types";

interface MeetingBoardHeaderProps {
  meeting: Meeting;
  participants: TeamMember[];
}

export function MeetingBoardHeader({
  meeting,
  participants,
}: MeetingBoardHeaderProps) {
  return (
    <div className="space-y-3">
      <Link
        href={`/meetings/${meeting.id}`}
        className="inline-flex items-center gap-1 text-sm text-muted-foreground transition-colors hover:text-foreground group"
      >
        <ArrowLeft className="h-3.5 w-3.5 transition-transform group-hover:-translate-x-0.5" />
        К встрече
      </Link>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0 space-y-2">
          <h1 className="break-words text-2xl font-heading font-bold tracking-tight text-foreground">
            {meeting.title || "Встреча без названия"}
          </h1>

          {meeting.meeting_date && (
            <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
              <CalendarDays className="h-4 w-4" />
              {formatMeetingHeaderDateTime(meeting.meeting_date)}
            </div>
          )}
        </div>

        <Badge
          variant="outline"
          className="w-fit shrink-0 gap-1.5 rounded-lg border-border/70 bg-card px-2.5 py-1 text-xs text-muted-foreground"
        >
          <Users className="h-3.5 w-3.5" />
          {participants.length}
        </Badge>
      </div>
    </div>
  );
}
