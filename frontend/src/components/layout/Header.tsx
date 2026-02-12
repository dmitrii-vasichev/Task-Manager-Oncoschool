"use client";

import { useState, useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import {
  Search,
  Bell,
  ChevronRight,
  LayoutDashboard,
  CheckSquare,
  CalendarDays,
  BarChart3,
  FileText,
  Users,
  Settings,
} from "lucide-react";
import { useCurrentUser } from "@/hooks/useCurrentUser";
import { UserAvatar } from "@/components/shared/UserAvatar";
import { MobileMenuTrigger } from "./Sidebar";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";

/* ------------------------------------------------
   Page config — titles and breadcrumbs
   ------------------------------------------------ */
interface PageMeta {
  title: string;
  icon: React.ElementType;
  parent?: string;
}

const PAGE_META: Record<string, PageMeta> = {
  "/": { title: "Dashboard", icon: LayoutDashboard },
  "/tasks": { title: "Задачи", icon: CheckSquare },
  "/meetings": { title: "Встречи", icon: CalendarDays },
  "/analytics": { title: "Аналитика", icon: BarChart3 },
  "/summary": { title: "Zoom Summary", icon: FileText },
  "/team": { title: "Команда", icon: Users },
  "/settings": { title: "Настройки", icon: Settings },
};

function getPageMeta(pathname: string): PageMeta & { crumbs: { label: string; href?: string }[] } {
  // Check for detail pages like /tasks/42
  const segments = pathname.split("/").filter(Boolean);

  if (segments.length >= 2) {
    const parentPath = `/${segments[0]}`;
    const parentMeta = PAGE_META[parentPath];
    if (parentMeta) {
      return {
        ...parentMeta,
        title: `#${segments[1]}`,
        parent: parentPath,
        crumbs: [
          { label: parentMeta.title, href: parentPath },
          { label: `#${segments[1]}` },
        ],
      };
    }
  }

  const meta = PAGE_META[pathname] || { title: "Онкошкола", icon: LayoutDashboard };
  return {
    ...meta,
    crumbs: [{ label: meta.title }],
  };
}

/* ------------------------------------------------
   Command palette search items
   ------------------------------------------------ */
interface SearchItem {
  label: string;
  href: string;
  icon: React.ElementType;
  keywords: string[];
}

const SEARCH_ITEMS: SearchItem[] = [
  { label: "Dashboard", href: "/", icon: LayoutDashboard, keywords: ["дашборд", "главная", "обзор"] },
  { label: "Задачи", href: "/tasks", icon: CheckSquare, keywords: ["tasks", "канбан", "доска"] },
  { label: "Встречи", href: "/meetings", icon: CalendarDays, keywords: ["meetings", "митинги", "собрания"] },
  { label: "Аналитика", href: "/analytics", icon: BarChart3, keywords: ["analytics", "графики", "статистика"] },
  { label: "Zoom Summary", href: "/summary", icon: FileText, keywords: ["summary", "зум", "протокол"] },
  { label: "Команда", href: "/team", icon: Users, keywords: ["team", "участники", "люди"] },
  { label: "Настройки", href: "/settings", icon: Settings, keywords: ["settings", "конфигурация", "ai"] },
];

/* ------------------------------------------------
   Command Palette
   ------------------------------------------------ */
function CommandPalette({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
}) {
  const [query, setQuery] = useState("");
  const router = useRouter();

  const filtered = query.length === 0
    ? SEARCH_ITEMS
    : SEARCH_ITEMS.filter((item) => {
        const q = query.toLowerCase();
        return (
          item.label.toLowerCase().includes(q) ||
          item.keywords.some((k) => k.includes(q))
        );
      });

  function navigate(href: string) {
    router.push(href);
    onOpenChange(false);
    setQuery("");
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md p-0 gap-0 overflow-hidden">
        <DialogTitle className="sr-only">Поиск</DialogTitle>
        <div className="flex items-center gap-2 border-b px-4">
          <Search className="h-4 w-4 text-muted-foreground shrink-0" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Найти страницу..."
            className="border-0 shadow-none focus-visible:ring-0 h-12 px-0"
            autoFocus
          />
          <kbd className="hidden sm:inline-flex h-5 items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground">
            ESC
          </kbd>
        </div>
        <div className="max-h-[300px] overflow-y-auto p-2">
          {filtered.length === 0 ? (
            <p className="py-6 text-center text-sm text-muted-foreground">
              Ничего не найдено
            </p>
          ) : (
            <div className="flex flex-col gap-0.5">
              {filtered.map((item) => (
                <button
                  key={item.href}
                  onClick={() => navigate(item.href)}
                  className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-left hover:bg-muted transition-colors"
                >
                  <item.icon className="h-4 w-4 text-muted-foreground shrink-0" />
                  <span>{item.label}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

/* ------------------------------------------------
   Header
   ------------------------------------------------ */
export function Header() {
  const pathname = usePathname();
  const { user } = useCurrentUser();
  const [searchOpen, setSearchOpen] = useState(false);

  // Cmd+K / Ctrl+K shortcut
  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setSearchOpen(true);
      }
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, []);

  const pageMeta = getPageMeta(pathname);

  return (
    <>
      <header className="flex h-16 items-center justify-between border-b bg-card/60 backdrop-blur-sm px-4 md:px-6 shrink-0">
        {/* Left — Mobile menu + Breadcrumbs */}
        <div className="flex items-center gap-2 min-w-0">
          <MobileMenuTrigger />

          {/* Breadcrumbs */}
          <nav className="flex items-center gap-1 min-w-0">
            {pageMeta.crumbs.map((crumb, i) => (
              <div key={i} className="flex items-center gap-1 min-w-0">
                {i > 0 && (
                  <ChevronRight className="h-3.5 w-3.5 text-muted-foreground/60 shrink-0" />
                )}
                {crumb.href ? (
                  <a
                    href={crumb.href}
                    className="text-sm text-muted-foreground hover:text-foreground transition-colors truncate"
                  >
                    {crumb.label}
                  </a>
                ) : (
                  <h1 className="text-sm font-semibold truncate">
                    {crumb.label}
                  </h1>
                )}
              </div>
            ))}
          </nav>
        </div>

        {/* Right — Search, Notifications, Avatar */}
        <div className="flex items-center gap-1">
          {/* Search trigger */}
          <Button
            variant="ghost"
            size="sm"
            className="gap-2 text-muted-foreground hover:text-foreground"
            onClick={() => setSearchOpen(true)}
          >
            <Search className="h-4 w-4" />
            <span className="hidden lg:inline text-xs">Поиск</span>
            <kbd className="hidden lg:inline-flex h-5 items-center gap-0.5 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground">
              <span className="text-xs">⌘</span>K
            </kbd>
          </Button>

          {/* Notifications */}
          <Button
            variant="ghost"
            size="icon"
            className="relative text-muted-foreground hover:text-foreground"
          >
            <Bell className="h-4 w-4" />
            {/* Badge — hidden for now, ready for real notifications */}
            {/* <span className="absolute -top-0.5 -right-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-accent text-[10px] font-bold text-accent-foreground">
              3
            </span> */}
          </Button>

          {/* User avatar */}
          {user && (
            <div className="ml-1">
              <UserAvatar name={user.full_name} size="sm" />
            </div>
          )}
        </div>
      </header>

      {/* Command Palette */}
      <CommandPalette open={searchOpen} onOpenChange={setSearchOpen} />
    </>
  );
}
