"use client";

import { useEffect, useMemo, useState } from "react";
import { ChevronDown, ChevronRight, Search, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { UserAvatar } from "@/components/shared/UserAvatar";
import { cn } from "@/lib/utils";
import type { Department, TeamMember } from "@/lib/types";

interface ParticipantsPickerDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  members: TeamMember[];
  departments: Department[];
  selectedIds: string[];
  onApply: (ids: string[]) => void;
}

interface ParticipantGroup {
  id: string;
  name: string;
  color: string | null;
  sortOrder: number;
  members: TeamMember[];
}

const GROUP_UNASSIGNED = "__unassigned__";
const GROUP_UNKNOWN_DEPARTMENT = "__unknown_department__";

function sortMembersByName(a: TeamMember, b: TeamMember) {
  return a.full_name.localeCompare(b.full_name, "ru", { sensitivity: "base" });
}

function uniq(values: string[]) {
  return Array.from(new Set(values));
}

export function ParticipantsPickerDialog({
  open,
  onOpenChange,
  members,
  departments,
  selectedIds,
  onApply,
}: ParticipantsPickerDialogProps) {
  const [query, setQuery] = useState("");
  const [draftSelectedIds, setDraftSelectedIds] = useState<string[]>(selectedIds);
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>({});

  const activeMembers = useMemo(
    () => members.filter((member) => member.is_active),
    [members]
  );

  const departmentById = useMemo(() => {
    return new Map(departments.map((department) => [department.id, department]));
  }, [departments]);

  const groups = useMemo(() => {
    const map = new Map<string, ParticipantGroup>();

    for (const member of activeMembers) {
      let groupId = GROUP_UNASSIGNED;
      let groupName = "Без отдела";
      let groupColor: string | null = "#6B7280";
      let groupSortOrder = Number.MAX_SAFE_INTEGER;

      if (member.department_id) {
        const department = departmentById.get(member.department_id);
        if (department) {
          groupId = department.id;
          groupName = department.name;
          groupColor = department.color;
          groupSortOrder = department.sort_order;
        } else {
          groupId = GROUP_UNKNOWN_DEPARTMENT;
          groupName = "Отдел не найден";
          groupColor = "#9CA3AF";
          groupSortOrder = Number.MAX_SAFE_INTEGER - 1;
        }
      }

      const existing = map.get(groupId);
      if (existing) {
        existing.members.push(member);
      } else {
        map.set(groupId, {
          id: groupId,
          name: groupName,
          color: groupColor,
          sortOrder: groupSortOrder,
          members: [member],
        });
      }
    }

    return Array.from(map.values())
      .map((group) => ({
        ...group,
        members: [...group.members].sort(sortMembersByName),
      }))
      .sort((a, b) => {
        if (a.sortOrder !== b.sortOrder) return a.sortOrder - b.sortOrder;
        return a.name.localeCompare(b.name, "ru", { sensitivity: "base" });
      });
  }, [activeMembers, departmentById]);

  useEffect(() => {
    if (!open) return;

    setQuery("");
    setDraftSelectedIds(selectedIds);
    setExpandedGroups(() => {
      const initialState: Record<string, boolean> = {};
      for (const group of groups) {
        const hasSelected = group.members.some((member) => selectedIds.includes(member.id));
        initialState[group.id] = hasSelected || groups.length <= 4;
      }
      return initialState;
    });
  }, [open, selectedIds, groups]);

  const normalizedQuery = query.trim().toLowerCase();

  const filteredGroups = useMemo(() => {
    if (!normalizedQuery) return groups;

    return groups
      .map((group) => {
        const groupMatches = group.name.toLowerCase().includes(normalizedQuery);
        const filteredMembers = groupMatches
          ? group.members
          : group.members.filter((member) => {
              const fullName = member.full_name.toLowerCase();
              const position = member.position?.toLowerCase() ?? "";
              const username = member.telegram_username?.toLowerCase() ?? "";
              return (
                fullName.includes(normalizedQuery) ||
                position.includes(normalizedQuery) ||
                username.includes(normalizedQuery)
              );
            });

        return {
          ...group,
          members: filteredMembers,
        };
      })
      .filter((group) => group.members.length > 0);
  }, [groups, normalizedQuery]);

  const visibleMemberIds = useMemo(
    () => filteredGroups.flatMap((group) => group.members.map((member) => member.id)),
    [filteredGroups]
  );

  const selectedSet = useMemo(
    () => new Set(draftSelectedIds),
    [draftSelectedIds]
  );

  const selectedVisibleCount = useMemo(
    () => visibleMemberIds.filter((memberId) => selectedSet.has(memberId)).length,
    [visibleMemberIds, selectedSet]
  );

  const hiddenSelectedCount = useMemo(() => {
    const activeIds = new Set(activeMembers.map((member) => member.id));
    return draftSelectedIds.filter((id) => !activeIds.has(id)).length;
  }, [activeMembers, draftSelectedIds]);

  const toggleGroup = (groupId: string) => {
    setExpandedGroups((prev) => ({
      ...prev,
      [groupId]: !prev[groupId],
    }));
  };

  const toggleMember = (memberId: string) => {
    setDraftSelectedIds((prev) =>
      prev.includes(memberId)
        ? prev.filter((id) => id !== memberId)
        : [...prev, memberId]
    );
  };

  const selectMembers = (memberIds: string[]) => {
    if (memberIds.length === 0) return;
    setDraftSelectedIds((prev) => uniq([...prev, ...memberIds]));
  };

  const deselectMembers = (memberIds: string[]) => {
    if (memberIds.length === 0) return;
    const idsToRemove = new Set(memberIds);
    setDraftSelectedIds((prev) => prev.filter((id) => !idsToRemove.has(id)));
  };

  const applySelection = () => {
    onApply(uniq(draftSelectedIds));
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl p-0 max-h-[85vh] overflow-hidden">
        <DialogHeader className="px-6 pt-6 pb-2">
          <DialogTitle className="font-heading flex items-center gap-2">
            <Users className="h-4 w-4" />
            Выбор участников
          </DialogTitle>
        </DialogHeader>

        <div className="px-6 pb-3 space-y-2">
          <div className="relative">
            <Search className="h-4 w-4 text-muted-foreground absolute left-3 top-1/2 -translate-y-1/2" />
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Поиск по имени, должности или отделу"
              className="pl-9 rounded-xl"
            />
          </div>

          <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-muted-foreground">
            <span>
              Выбрано: {draftSelectedIds.length} из {activeMembers.length}
              {hiddenSelectedCount > 0 ? ` (+${hiddenSelectedCount} скрыто)` : ""}
            </span>
            <div className="flex items-center gap-1.5">
              <button
                type="button"
                onClick={() => selectMembers(visibleMemberIds)}
                className="rounded-md px-2 py-1 hover:bg-muted text-foreground transition-colors"
              >
                Выбрать видимых
              </button>
              <button
                type="button"
                onClick={() => deselectMembers(visibleMemberIds)}
                className="rounded-md px-2 py-1 hover:bg-muted text-foreground transition-colors"
              >
                Снять видимых
              </button>
            </div>
          </div>
        </div>

        <div className="px-6 pb-3 overflow-y-auto max-h-[48vh] space-y-2">
          {filteredGroups.length === 0 ? (
            <div className="rounded-xl border border-dashed border-border/60 bg-muted/20 p-6 text-center">
              <p className="text-sm text-muted-foreground">Ничего не найдено</p>
              <p className="text-xs text-muted-foreground/70 mt-1">
                Попробуйте изменить запрос поиска
              </p>
            </div>
          ) : (
            filteredGroups.map((group) => {
              const groupIds = group.members.map((member) => member.id);
              const selectedInGroup = groupIds.filter((memberId) =>
                selectedSet.has(memberId)
              ).length;
              const expanded = normalizedQuery ? true : !!expandedGroups[group.id];

              return (
                <div key={group.id} className="rounded-xl border border-border/60 bg-card overflow-hidden">
                  <div className="px-3 py-2.5 flex flex-wrap items-center gap-2">
                    <button
                      type="button"
                      onClick={() => toggleGroup(group.id)}
                      className="flex items-center gap-2 min-w-0 flex-1 text-left"
                    >
                      <div
                        className="w-1 h-6 rounded-full shrink-0"
                        style={{ backgroundColor: group.color || "#6B7280" }}
                      />
                      {expanded ? (
                        <ChevronDown className="h-4 w-4 text-muted-foreground shrink-0" />
                      ) : (
                        <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0" />
                      )}
                      <span className="text-sm font-medium truncate">{group.name}</span>
                      <span className="text-xs text-muted-foreground shrink-0">
                        {selectedInGroup}/{group.members.length}
                      </span>
                    </button>

                    <button
                      type="button"
                      onClick={() => selectMembers(groupIds)}
                      className="rounded-md px-2 py-1 text-xs hover:bg-muted transition-colors"
                    >
                      Все
                    </button>
                    <button
                      type="button"
                      onClick={() => deselectMembers(groupIds)}
                      className="rounded-md px-2 py-1 text-xs hover:bg-muted transition-colors"
                    >
                      Снять
                    </button>
                  </div>

                  {expanded && (
                    <div className="border-t border-border/50 px-3 py-2 space-y-1.5">
                      {group.members.map((member) => {
                        const selected = selectedSet.has(member.id);
                        return (
                          <button
                            key={member.id}
                            type="button"
                            onClick={() => toggleMember(member.id)}
                            className={cn(
                              "w-full flex items-center gap-2 rounded-lg border px-2.5 py-2 text-left transition-all",
                              selected
                                ? "border-primary bg-primary/5"
                                : "border-border/60 hover:border-border bg-card"
                            )}
                          >
                            <div
                              className={cn(
                                "h-4 w-4 rounded border shrink-0 flex items-center justify-center",
                                selected ? "bg-primary border-primary" : "border-border"
                              )}
                            >
                              {selected && (
                                <svg
                                  viewBox="0 0 12 12"
                                  className="h-2.5 w-2.5 text-primary-foreground"
                                  fill="none"
                                  stroke="currentColor"
                                  strokeWidth="2"
                                >
                                  <path d="M2 6L5 9L10 3" />
                                </svg>
                              )}
                            </div>
                            <UserAvatar
                              name={member.full_name}
                              avatarUrl={member.avatar_url}
                              size="sm"
                            />
                            <span className="flex-1 min-w-0">
                              <span className="block text-sm font-medium truncate">
                                {member.full_name}
                              </span>
                              {member.position && (
                                <span className="block text-xs text-muted-foreground truncate">
                                  {member.position}
                                </span>
                              )}
                            </span>
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>

        <div className="border-t border-border/60 px-6 py-4 flex items-center justify-between gap-2">
          <p className="text-xs text-muted-foreground">
            В видимом списке выбрано: {selectedVisibleCount} из {visibleMemberIds.length}
          </p>
          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="outline"
              className="rounded-xl"
              onClick={() => onOpenChange(false)}
            >
              Отмена
            </Button>
            <Button
              type="button"
              className="rounded-xl"
              onClick={applySelection}
            >
              Применить
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
