"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { languages, useLanguage, useT } from "@/lib/i18n";
import { Database, Brain, FlaskConical, Package, Home, BarChart3, MessageSquare, FileText } from "lucide-react";

export function Navbar() {
  const pathname = usePathname();
  const t = useT();
  const { lang, setLang } = useLanguage();

  const items = [
    { href: "/", label: t("nav.home"), icon: Home },
    { href: "/datasets", label: t("nav.datasets"), icon: Database },
    { href: "/train", label: t("nav.train"), icon: Brain },
    { href: "/experiments", label: t("nav.experiments"), icon: FlaskConical },
    { href: "/models", label: t("nav.models"), icon: Package },
    { href: "/eda", label: t("nav.eda"), icon: BarChart3 },
    { href: "/chat", label: t("nav.chat"), icon: MessageSquare },
    { href: "/reports", label: t("nav.reports"), icon: FileText },
  ];

  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <Link href="/" className="text-lg font-bold text-slate-900">
          ML Platform
        </Link>
        <div className="flex items-center gap-2">
          <nav className="flex items-center gap-1">
            {items.map((item) => {
              const Icon = item.icon;
              const active = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium",
                    active ? "bg-slate-900 text-white" : "text-slate-700 hover:bg-slate-100"
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </Link>
              );
            })}
          </nav>
          <label className="sr-only" htmlFor="lang-select">{t("nav.language")}</label>
          <select
            id="lang-select"
            value={lang}
            onChange={(e) => setLang(e.target.value as (typeof languages)[number])}
            className="rounded-md border border-slate-300 px-2 py-1 text-sm"
          >
            {languages.map((l) => (
              <option key={l} value={l}>
                {l.toUpperCase()}
              </option>
            ))}
          </select>
        </div>
      </div>
    </header>
  );
}