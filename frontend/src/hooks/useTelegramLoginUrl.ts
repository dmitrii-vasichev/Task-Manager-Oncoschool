"use client";

import { useEffect, useRef } from "react";
import { api } from "@/lib/api";
import type { TelegramAuthData } from "@/lib/types";

/**
 * Detects Telegram LoginUrl callback parameters in the URL,
 * authenticates the user via /api/auth/telegram, and cleans the URL.
 *
 * Uses window.location directly instead of useSearchParams to avoid
 * requiring a Suspense boundary (which breaks Vercel pre-rendering).
 *
 * Should be called once in a top-level component (e.g. AppShell).
 */
export function useTelegramLoginUrl(onLogin: () => void) {
  const handled = useRef(false);

  useEffect(() => {
    if (handled.current) return;
    if (typeof window === "undefined") return;

    const params = new URLSearchParams(window.location.search);

    const id = params.get("id");
    const hash = params.get("hash");
    const authDate = params.get("auth_date");
    const firstName = params.get("first_name");

    // Not a Telegram LoginUrl callback
    if (!id || !hash || !authDate || !firstName) return;

    handled.current = true;

    const authData: TelegramAuthData = {
      id: Number(id),
      first_name: firstName,
      last_name: params.get("last_name") || undefined,
      username: params.get("username") || undefined,
      photo_url: params.get("photo_url") || undefined,
      auth_date: Number(authDate),
      hash,
    };

    api
      .loginWithTelegram(authData)
      .then(() => {
        onLogin();
        // Clean URL: remove Telegram params, keep the path
        window.history.replaceState({}, "", window.location.pathname);
      })
      .catch((err) => {
        console.error("Telegram LoginUrl auth failed:", err);
        handled.current = false;
      });
  }, [onLogin]);
}
