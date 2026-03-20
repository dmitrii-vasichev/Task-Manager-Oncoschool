import type { Metadata } from "next";
import { Manrope, Commissioner } from "next/font/google";
import localFont from "next/font/local";
import Script from "next/script";
import "./globals.css";
import { AuthProvider } from "@/components/layout/AuthProvider";
import { AppShell } from "@/components/layout/AppShell";
import { ToastProvider } from "@/components/shared/Toast";
import { PageTitleProvider } from "@/hooks/usePageTitle";

const manrope = Manrope({
  subsets: ["cyrillic", "latin"],
  variable: "--font-heading",
  display: "swap",
});

const commissioner = Commissioner({
  subsets: ["cyrillic", "latin"],
  variable: "--font-body",
  display: "swap",
});

const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
  weight: "100 900",
});

export const metadata: Metadata = {
  title: {
    template: "%s — Онкошкола",
    default: "Онкошкола — Портал",
  },
  description: "Рабочий портал команды Онкошколы",
  icons: {
    icon: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ru">
      <head>
        <Script
          src="https://telegram.org/js/telegram-web-app.js"
          strategy="beforeInteractive"
        />
      </head>
      <body
        className={`${manrope.variable} ${commissioner.variable} ${geistMono.variable} antialiased`}
      >
        <AuthProvider>
          <ToastProvider>
            <PageTitleProvider>
              <AppShell>{children}</AppShell>
            </PageTitleProvider>
          </ToastProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
