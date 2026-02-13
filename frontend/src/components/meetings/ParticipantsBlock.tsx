"use client";

import { Users } from "lucide-react";
import { UserAvatar } from "@/components/shared/UserAvatar";
import type { TeamMember } from "@/lib/types";

interface ParticipantsBlockProps {
  /** Resolved participant members (from meeting_participants or schedule.participant_ids) */
  participants: TeamMember[];
  /** String-only participant names (from parsed summary) */
  participantNames?: string[];
}

export function ParticipantsBlock({
  participants,
  participantNames,
}: ParticipantsBlockProps) {
  const names = participants.length > 0
    ? participants.map((p) => p.full_name)
    : participantNames || [];

  if (names.length === 0) return null;

  return (
    <div className="rounded-2xl border border-border/60 bg-card p-4">
      <div className="flex items-center gap-2 mb-3">
        <div className="h-8 w-8 rounded-xl bg-violet-500/10 flex items-center justify-center">
          <Users className="h-4 w-4 text-violet-600" />
        </div>
        <span className="text-sm font-heading font-semibold">Участники</span>
        <span className="text-2xs text-muted-foreground/60 ml-auto">
          {names.length}
        </span>
      </div>
      <div className="flex flex-wrap gap-2">
        {names.map((name, i) => (
          <div
            key={i}
            className="inline-flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-muted/50 text-sm"
          >
            <UserAvatar name={name} size="sm" />
            <span className="text-foreground font-medium">{name}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
