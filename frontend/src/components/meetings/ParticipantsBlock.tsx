"use client";

import { useMemo, useState } from "react";
import { Users, Pencil } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
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
  const [listOpen, setListOpen] = useState(false);
  const hasMembers = participants.length > 0;
  const count = hasMembers ? participants.length : (participantNames?.length ?? 0);
  const maxVisible = 8;

  const displayParticipants = useMemo(
    () =>
      hasMembers
        ? participants.map((participant) => ({
            id: participant.id,
            name: participant.full_name,
            avatarUrl: participant.avatar_url,
          }))
        : (participantNames ?? []).map((name, index) => ({
            id: `name-${index}`,
            name,
            avatarUrl: null,
          })),
    [hasMembers, participants, participantNames]
  );

  const visibleParticipants = displayParticipants.slice(0, maxVisible);
  const hiddenCount = Math.max(0, count - visibleParticipants.length);

  return (
    <>
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
          <div className="space-y-3">
            <TooltipProvider delayDuration={120}>
              <div className="flex items-center gap-2">
                <div className="flex -space-x-1.5 min-w-0">
                  {visibleParticipants.map((participant) => (
                    <Tooltip key={participant.id}>
                      <TooltipTrigger asChild>
                        <button
                          type="button"
                          className="rounded-full ring-2 ring-card focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                          onClick={() => setListOpen(true)}
                          aria-label={participant.name}
                        >
                          <UserAvatar
                            name={participant.name}
                            avatarUrl={participant.avatarUrl}
                            size="sm"
                          />
                        </button>
                      </TooltipTrigger>
                      <TooltipContent side="top">
                        {participant.name}
                      </TooltipContent>
                    </Tooltip>
                  ))}
                </div>

                {hiddenCount > 0 && (
                  <Button
                    type="button"
                    variant="secondary"
                    size="sm"
                    className="h-7 px-2.5 rounded-full text-xs font-semibold shrink-0"
                    onClick={() => setListOpen(true)}
                  >
                    +{hiddenCount}
                  </Button>
                )}
              </div>
            </TooltipProvider>

            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="h-7 px-2 rounded-lg text-xs text-muted-foreground hover:text-foreground"
              onClick={() => setListOpen(true)}
            >
              Показать список
            </Button>
          </div>
        )}
      </div>

      <Dialog open={listOpen} onOpenChange={setListOpen}>
        <DialogContent className="sm:max-w-md p-0 overflow-hidden">
          <DialogHeader className="px-6 pt-6 pb-3">
            <DialogTitle className="font-heading text-base">
              Участники ({count})
            </DialogTitle>
          </DialogHeader>

          <div className="px-6 pb-6 max-h-[60vh] overflow-y-auto">
            <div className="space-y-1.5">
              {displayParticipants.map((participant) => (
                <div
                  key={participant.id}
                  className="flex items-center gap-2.5 rounded-lg border border-border/50 bg-muted/20 px-2.5 py-2"
                >
                  <UserAvatar
                    name={participant.name}
                    avatarUrl={participant.avatarUrl}
                    size="sm"
                  />
                  <span className="text-sm font-medium text-foreground truncate">
                    {participant.name}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
