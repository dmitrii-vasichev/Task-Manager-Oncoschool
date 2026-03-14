"use client";

import {
  createContext,
  useContext,
  useState,
  useCallback,
  type ReactNode,
} from "react";
import { CheckCircle2, AlertTriangle, Info, X } from "lucide-react";
import { cn } from "@/lib/utils";

/* ============================================
   Toast Types
   ============================================ */

type ToastType = "success" | "error" | "info";

interface Toast {
  id: string;
  type: ToastType;
  message: string;
}

interface ToastContextValue {
  toast: (type: ToastType, message: string) => void;
  toastSuccess: (message: string) => void;
  toastError: (message: string) => void;
  toastInfo: (message: string) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

/* ============================================
   Toast Provider
   ============================================ */

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const addToast = useCallback(
    (type: ToastType, message: string) => {
      const id = `${Date.now()}-${Math.random().toString(36).slice(2, 6)}`;
      setToasts((prev) => [...prev, { id, type, message }]);

      // Auto-remove after 4 seconds
      setTimeout(() => removeToast(id), 4000);
    },
    [removeToast]
  );

  const contextValue: ToastContextValue = {
    toast: addToast,
    toastSuccess: useCallback(
      (message: string) => addToast("success", message),
      [addToast]
    ),
    toastError: useCallback(
      (message: string) => addToast("error", message),
      [addToast]
    ),
    toastInfo: useCallback(
      (message: string) => addToast("info", message),
      [addToast]
    ),
  };

  return (
    <ToastContext.Provider value={contextValue}>
      {children}

      {/* Toast container — fixed bottom-right */}
      <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2 pointer-events-none max-w-sm w-full">
        {toasts.map((t) => (
          <ToastItem
            key={t.id}
            toast={t}
            onRemove={() => removeToast(t.id)}
          />
        ))}
      </div>
    </ToastContext.Provider>
  );
}

/* ============================================
   Hook
   ============================================ */

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return ctx;
}

/* ============================================
   Toast Item
   ============================================ */

const ICON_MAP = {
  success: CheckCircle2,
  error: AlertTriangle,
  info: Info,
} as const;

const STYLE_MAP = {
  success:
    "border-status-done-fg/20 bg-card text-status-done-fg [&_.toast-icon]:text-status-done-fg",
  error:
    "border-destructive/20 bg-card text-destructive [&_.toast-icon]:text-destructive",
  info: "border-primary/20 bg-card text-primary [&_.toast-icon]:text-primary",
} as const;

function ToastItem({
  toast,
  onRemove,
}: {
  toast: Toast;
  onRemove: () => void;
}) {
  const Icon = ICON_MAP[toast.type];
  const style = STYLE_MAP[toast.type];

  return (
    <div
      className={cn(
        "pointer-events-auto flex items-center gap-3 rounded-xl border px-4 py-3 shadow-lg animate-toast-in",
        style
      )}
    >
      <Icon className="toast-icon h-4 w-4 shrink-0" />
      <p className="flex-1 text-sm font-medium text-foreground">
        {toast.message}
      </p>
      <button
        onClick={onRemove}
        className="shrink-0 h-6 w-6 rounded-lg flex items-center justify-center text-muted-foreground/50 hover:text-foreground hover:bg-muted/50"
      >
        <X className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}
