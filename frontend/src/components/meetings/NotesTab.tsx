"use client";

import { useState, useRef } from "react";
import { StickyNote, Check, Loader2 } from "lucide-react";
import { Textarea } from "@/components/ui/textarea";

interface NotesTabProps {
  notes: string | null;
  isModerator: boolean;
  onSave: (notes: string) => Promise<void>;
}

export function NotesTab({ notes, isModerator, onSave }: NotesTabProps) {
  const [value, setValue] = useState(notes || "");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  const handleBlur = async () => {
    if (!isModerator) return;
    if (value === (notes || "")) return;

    setSaving(true);
    try {
      await onSave(value);
      setSaved(true);
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      timeoutRef.current = setTimeout(() => setSaved(false), 2000);
    } finally {
      setSaving(false);
    }
  };

  if (!isModerator && !notes) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="h-12 w-12 rounded-xl bg-muted/50 flex items-center justify-center mb-3">
          <StickyNote className="h-5 w-5 text-muted-foreground/50" />
        </div>
        <p className="text-sm text-muted-foreground">
          К этой встрече нет заметок
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-heading font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-2">
          <StickyNote className="h-4 w-4" />
          Заметки
        </h3>
        {saving && (
          <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
            <Loader2 className="h-3 w-3 animate-spin" />
            Сохранение...
          </span>
        )}
        {saved && (
          <span className="inline-flex items-center gap-1 text-xs text-emerald-600">
            <Check className="h-3 w-3" />
            Сохранено
          </span>
        )}
      </div>

      {isModerator ? (
        <Textarea
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onBlur={handleBlur}
          placeholder="Добавьте заметки к встрече..."
          rows={8}
          className="rounded-xl border-border/60 bg-background/50 resize-none text-sm leading-relaxed focus:bg-background"
        />
      ) : (
        <div className="rounded-2xl border border-border/60 bg-card p-6">
          <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">
            {notes}
          </p>
        </div>
      )}
    </div>
  );
}
