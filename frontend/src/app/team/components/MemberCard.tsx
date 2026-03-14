"use client";

import { FlaskConical, Pencil, Star } from "lucide-react";
import { Button } from "@/components/ui/button";
import { RoleBadge } from "@/components/shared/RoleBadge";
import { UserAvatar } from "@/components/shared/UserAvatar";
import type { TeamMember } from "@/lib/types";

interface MemberCardProps {
  member: TeamMember;
  isHead?: boolean;
  onClick: () => void;
  onEdit?: () => void;
}

export function MemberCard({ member, isHead, onClick, onEdit }: MemberCardProps) {
  return (
    <div
      className={`
        group relative overflow-hidden rounded-2xl border bg-card p-4
        hover:shadow-lg hover:shadow-primary/5 hover:-translate-y-0.5
        cursor-pointer transition-all duration-200
        ${isHead ? "ring-2 ring-amber-400/50" : "border-border/60"}
        ${!member.is_active ? "opacity-60" : ""}
      `}
      onClick={onClick}
    >
      <div className="flex items-center gap-3">
        <UserAvatar
          name={member.full_name}
          avatarUrl={member.avatar_url}
          size="lg"
        />

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="font-heading font-semibold text-[15px] truncate">
              {member.full_name}
            </span>
            {isHead && (
              <Star className="h-3.5 w-3.5 text-amber-500 fill-amber-500 shrink-0" />
            )}
          </div>
          {member.position && (
            <p className="text-sm text-muted-foreground truncate mt-0.5">
              {member.position}
            </p>
          )}
          <div className="mt-1 flex items-center gap-1.5 flex-wrap">
            <RoleBadge role={member.role} />
            {member.is_test && (
              <span className="inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-2xs font-semibold bg-orange-500/15 text-orange-700 ring-1 ring-inset ring-orange-500/40">
                <FlaskConical className="h-3 w-3" />
                Тестовый
              </span>
            )}
          </div>
          {!member.is_active && (
            <div className="mt-1">
              <span className="inline-flex items-center rounded-full px-2 py-0.5 text-2xs font-medium bg-muted text-muted-foreground ring-1 ring-inset ring-border/60">
                Неактивен
              </span>
            </div>
          )}
        </div>

        {onEdit && (
          <Button
            variant="ghost"
            size="icon"
            className="shrink-0 h-8 w-8 rounded-xl text-muted-foreground hover:text-foreground hover:bg-muted opacity-0 group-hover:opacity-100 transition-opacity"
            onClick={(e) => {
              e.stopPropagation();
              onEdit();
            }}
          >
            <Pencil className="h-3.5 w-3.5" />
          </Button>
        )}
      </div>
    </div>
  );
}
