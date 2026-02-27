import type { ReactNode } from "react";
import "./globals.css";
import "./xterm.css";

export const metadata = {
  title: "Substrate",
  description: "AI-governed delivery platform",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="bg-token-canvas text-token-primary antialiased">
        {children}
      </body>
    </html>
  );
}
