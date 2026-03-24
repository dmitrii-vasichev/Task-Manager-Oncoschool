"use client";

import { useState, useCallback, type ReactNode } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useCurrentUser } from "@/hooks/useCurrentUser";
import { useTelegramLoginUrl } from "@/hooks/useTelegramLoginUrl";
import { Sidebar, SidebarContext } from "./Sidebar";
import { Header } from "./Header";
import { Skeleton } from "@/components/ui/skeleton";
import { TooltipProvider } from "@/components/ui/tooltip";
import { GraduationCap } from "lucide-react";

export function AppShell({ children }: { children: ReactNode }) {
  const { user, loading, refreshUser } = useCurrentUser();
  const pathname = usePathname();
  const router = useRouter();

  // Handle Telegram LoginUrl callback (from inline buttons in chats)
  const onTelegramLogin = useCallback(() => {
    refreshUser();
  }, [refreshUser]);
  useTelegramLoginUrl(onTelegramLogin);

  // Sidebar state
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  // Login page — no shell
  if (pathname === "/login") {
    return <>{children}</>;
  }

  // Loading state
  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-4 animate-in fade-in duration-500">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-lg">
            <GraduationCap className="h-6 w-6" />
          </div>
          <div className="flex flex-col items-center gap-2">
            <Skeleton className="h-3 w-24 rounded-full" />
            <Skeleton className="h-3 w-16 rounded-full" />
          </div>
        </div>
      </div>
    );
  }

  // Not authenticated — redirect to login
  if (!user) {
    router.push("/login");
    return null;
  }

  return (
    <SidebarContext.Provider
      value={{ collapsed, setCollapsed, mobileOpen, setMobileOpen }}
    >
      <TooltipProvider delayDuration={120}>
        <div className="flex h-screen overflow-hidden bg-background">
          <Sidebar />
          <div className="flex flex-1 flex-col overflow-hidden min-w-0">
            <Header />
            <main className="flex-1 overflow-auto">
              <div className="mx-auto max-w-7xl px-4 py-6 md:px-6 lg:px-8 animate-in fade-in duration-300">
                {children}
              </div>
            </main>
          </div>
        </div>
      </TooltipProvider>
    </SidebarContext.Provider>
  );
}
