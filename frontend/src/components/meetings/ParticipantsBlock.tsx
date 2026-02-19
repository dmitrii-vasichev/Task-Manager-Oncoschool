"use client";

import { Users, Pencil } from "lucide-react";
import { Button } from "@/components/ui/button";
import { UserAvatar } from "@/components/shared/UserAvatar";
import type { TeamMember } from "@/lib/types";

interface ParticipantsBlockProps {
  /** Resolved participant members (from meeting.participant_ids mapped to team_members) */
  participants: TeamMember[];
  /** String-only participant names (from parsed summary, fallback) */
  participantNames?: string[];
  /** Whether the current user is a moderator */
  isModerator?: boolean;
  /** Called when moderator clicks the edit button */
  onEdit?: () => void;
}

export function ParticipantsBlock({
  participants,
  participantNames,
  isModerator,
  onEdit,
}: ParticipantsBlockProps) {
  const hasMembers = participants.length > 0;
  const count = hasMembers ? participants.length : (participantNames?.length ?? 0);

  return (
    <div className="rounded-2xl border border-border/60 bg-card p-4">
      <div className="flex items-center gap-2 mb-3">
        <div className="h-8 w-8 rounded-xl bg-violet-500/10 flex items-center justify-center">
          <Users className="h-4 w-4 text-violet-600" />
        </div>
        <span className="text-sm font-heading font-semibold">Участники</span>
        {count > 0 && (
          <span className="text-2xs text-muted-foreground/60">
            {count}
          </span>
        )}
        {isModerator && onEdit && (
          <Button
            variant="ghost"
            size="sm"
            className="ml-auto h-7 w-7 p-0 rounded-lg"
            onClick={onEdit}
          >
            <Pencil className="h-3.5 w-3.5 text-muted-foreground" />
          </Button>
        )}
      </div>

      {count === 0 ? (
        <p className="text-xs text-muted-foreground/60">
          {isModerator ? "Нажмите на карандаш, чтобы добавить участников" : "Участники не указаны"}
        </p>
      ) : (
        <div className="flex flex-wrap gap-2">
          {hasMembers
            ? participants.map((p) => (
                <div
                  key={p.id}
                  className="inline-flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-muted/50 text-sm"
                >
                  <UserAvatar name={p.full_name} avatarUrl={p.avatar_url} size="sm" />
                  <span className="text-foreground font-medium">{p.full_name}</span>
                </div>
              ))
            : participantNames?.map((name, i) => (
                <div
                  key={i}
                  className="inline-flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-muted/50 text-sm"
                >
                  <UserAvatar name={name} size="sm" />
                  <span className="text-foreground font-medium">{name}</span>
                </div>
              ))}
        </div>
      )}
    </div>
  );
}
