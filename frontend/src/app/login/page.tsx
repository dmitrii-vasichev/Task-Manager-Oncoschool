"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useCurrentUser } from "@/hooks/useCurrentUser";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { GraduationCap, Loader2 } from "lucide-react";

export default function LoginPage() {
  const [telegramId, setTelegramId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const { login } = useCurrentUser();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const id = parseInt(telegramId, 10);
    if (!id || isNaN(id)) {
      setError("Введите корректный Telegram ID");
      return;
    }

    try {
      setLoading(true);
      await login(id);
      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка авторизации");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      {/* Decorative background */}
      <div className="fixed inset-0 bg-gradient-to-br from-primary/[0.03] via-transparent to-accent/[0.03]" />

      <div className="relative w-full max-w-sm animate-fade-in-up">
        <div className="rounded-2xl border border-border/60 bg-card p-8 shadow-xl shadow-primary/5">
          {/* Logo */}
          <div className="text-center mb-8">
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-lg shadow-primary/20">
              <GraduationCap className="h-7 w-7" />
            </div>
            <h1 className="text-2xl font-heading font-bold tracking-tight">
              Онкошкола
            </h1>
            <p className="mt-1.5 text-sm text-muted-foreground">
              Войдите с помощью Telegram ID
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <Label
                htmlFor="telegram_id"
                className="text-xs font-medium text-muted-foreground uppercase tracking-wider"
              >
                Telegram ID
              </Label>
              <Input
                id="telegram_id"
                type="text"
                inputMode="numeric"
                placeholder="123456789"
                value={telegramId}
                onChange={(e) => setTelegramId(e.target.value)}
                disabled={loading}
                className="h-11 rounded-xl text-center text-lg font-mono tracking-wider"
              />
              <p className="text-xs text-muted-foreground text-center">
                Узнать свой ID можно у бота @userinfobot
              </p>
            </div>

            {error && (
              <div className="rounded-xl bg-destructive/10 border border-destructive/20 px-3 py-2.5">
                <p className="text-sm text-destructive text-center">{error}</p>
              </div>
            )}

            <Button
              type="submit"
              className="w-full h-11 rounded-xl text-base"
              disabled={loading}
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Вход...
                </>
              ) : (
                "Войти"
              )}
            </Button>
          </form>
        </div>

        {/* Subtle footer */}
        <p className="mt-6 text-center text-xs text-muted-foreground/50">
          Таск-менеджер для команды Онкошколы
        </p>
      </div>
    </div>
  );
}
