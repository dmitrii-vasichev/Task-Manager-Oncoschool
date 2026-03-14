"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Home } from "lucide-react";

export default function NotFound() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <div className="flex flex-col items-center text-center max-w-md animate-fade-in-up">
        {/* Illustration */}
        <svg
          viewBox="0 0 200 150"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="w-64 h-48 mb-6"
        >
          {/* Background shapes */}
          <circle cx="100" cy="75" r="55" className="fill-muted/40" />
          <circle cx="100" cy="75" r="40" className="fill-muted/60" />

          {/* Page with fold */}
          <rect
            x="62"
            y="30"
            width="76"
            height="90"
            rx="10"
            className="fill-card stroke-border"
            strokeWidth="2"
          />
          <path
            d="M114 30H130C135 30 138 33 138 38V30L114 30Z"
            className="fill-border/30"
          />
          <path
            d="M114 30V46C114 51 118 55 123 55H138"
            className="stroke-border"
            strokeWidth="2"
            fill="none"
          />

          {/* 404 text */}
          <text
            x="100"
            y="85"
            textAnchor="middle"
            className="fill-primary/25"
            fontSize="36"
            fontWeight="800"
          >
            404
          </text>

          {/* Magnifying glass */}
          <circle
            cx="140"
            cy="105"
            r="14"
            className="fill-accent/8 stroke-accent/40"
            strokeWidth="2"
          />
          <line
            x1="150"
            y1="115"
            x2="162"
            y2="127"
            className="stroke-accent/40"
            strokeWidth="3"
            strokeLinecap="round"
          />
          <text
            x="140"
            y="110"
            textAnchor="middle"
            className="fill-accent/40"
            fontSize="14"
            fontWeight="700"
          >
            ?
          </text>

          {/* Decorative dots */}
          <circle cx="40" cy="45" r="3" className="fill-primary/20" />
          <circle cx="165" cy="40" r="2.5" className="fill-accent/25" />
          <circle cx="50" cy="110" r="2" className="fill-status-progress-fg/15" />
          <circle cx="160" cy="80" r="2" className="fill-accent/15" />
          <circle cx="42" cy="75" r="1.5" className="fill-primary/15" />
        </svg>

        <h1 className="text-3xl font-heading font-bold tracking-tight text-foreground mb-2">
          Страница не найдена
        </h1>
        <p className="text-muted-foreground text-sm leading-relaxed mb-8">
          К сожалению, запрашиваемая страница не существует или была перемещена.
          Проверьте адрес или вернитесь на главную.
        </p>

        <div className="flex items-center gap-3">
          <Link href="/">
            <Button className="rounded-xl gap-2">
              <Home className="h-4 w-4" />
              На главную
            </Button>
          </Link>
          <Button
            variant="outline"
            className="rounded-xl gap-2"
            onClick={() => history.back()}
          >
            <ArrowLeft className="h-4 w-4" />
            Назад
          </Button>
        </div>
      </div>
    </div>
  );
}
