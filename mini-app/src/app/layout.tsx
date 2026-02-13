import type { Metadata, Viewport } from "next";
import Script from "next/script";
import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "Онкошкола — Задачи",
  description: "Telegram Mini App для управления задачами",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  viewportFit: "cover",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ru">
      <body>
        {/* Telegram SDK loaded via official CDN; SRI not available as Telegram updates scripts without versioning.
            Security relies on HTTPS + initData signature verification on backend. */}
        <Script
          src="https://telegram.org/js/telegram-web-app.js"
          strategy="beforeInteractive"
          crossOrigin="anonymous"
        />
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
