"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import es from "@/locales/es.json";
import en from "@/locales/en.json";

export const languages = ["es", "en"] as const;
export type Language = (typeof languages)[number];

const dictionaries: Record<Language, Record<string, string>> = {
  es: es as Record<string, string>,
  en: en as Record<string, string>,
};

interface LanguageContextValue {
  lang: Language;
  setLang: (lang: Language) => void;
  t: (key: string) => string;
}

const LanguageContext = createContext<LanguageContextValue | null>(null);

function detectLanguage(): Language {
  if (typeof window === "undefined") return "en";
  try {
    const stored = window.localStorage.getItem("lang");
    if (stored && (languages as readonly string[]).includes(stored)) {
      return stored as Language;
    }
  } catch {
    // ignore
  }
  const nav = (window.navigator.language || "").toLowerCase();
  if (nav.startsWith("es")) return "es";
  return "en";
}

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLangState] = useState<Language>("en");

  useEffect(() => {
    setLangState(detectLanguage());
  }, []);

  const setLang = (next: Language) => {
    setLangState(next);
    try {
      window.localStorage.setItem("lang", next);
    } catch {
      // ignore
    }
  };

  const t = (key: string) => dictionaries[lang]?.[key] ?? key;

  return React.createElement(
    LanguageContext.Provider,
    { value: { lang, setLang, t } },
    children
  );
}

export function useT() {
  const ctx = useContext(LanguageContext);
  if (!ctx) {
    throw new Error("useT must be used within a LanguageProvider");
  }
  return ctx.t;
}

export function useLanguage() {
  const ctx = useContext(LanguageContext);
  if (!ctx) {
    throw new Error("useLanguage must be used within a LanguageProvider");
  }
  return { lang: ctx.lang, setLang: ctx.setLang };
}