import type { Metadata } from "next";
import "./globals.css";
import { Navbar } from "@/components/Navbar";
import { LanguageProvider } from "@/lib/i18n";

export const metadata: Metadata = {
  title: "ML Platform",
  description: "Machine learning training frontend",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 text-slate-900">
        <LanguageProvider>
          <Navbar />
          <main className="container-page">{children}</main>
        </LanguageProvider>
      </body>
    </html>
  );
}
