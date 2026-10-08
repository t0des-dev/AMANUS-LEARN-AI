"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { Language, translations } from "./translations";

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string, fallback?: string) => string;
  dir: "ltr" | "rtl";
  isRTL: boolean;
}

const LanguageContext = createContext<LanguageContextType>({
  language: "fr",
  setLanguage: () => {},
  t: (key: string, fallback?: string) => fallback || key,
  dir: "ltr",
  isRTL: false,
});

const STORAGE_KEY = "amanus_preferred_lang";

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState<Language>("fr");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY) as Language | null;
      if (saved && (saved === "fr" || saved === "ar" || saved === "en")) {
        setLanguageState(saved);
        applyDocumentDirection(saved);
      } else {
        applyDocumentDirection("fr");
      }
    } catch {
      // Fallback
      applyDocumentDirection("fr");
    }
    setMounted(true);
  }, []);

  const applyDocumentDirection = (lang: Language) => {
    if (typeof document !== "undefined") {
      const isArabic = lang === "ar";
      document.documentElement.lang = lang;
      document.documentElement.dir = isArabic ? "rtl" : "ltr";
      if (isArabic) {
        document.documentElement.classList.add("font-arabic");
      } else {
        document.documentElement.classList.remove("font-arabic");
      }
    }
  };

  const setLanguage = (lang: Language) => {
    setLanguageState(lang);
    try {
      localStorage.setItem(STORAGE_KEY, lang);
    } catch {
      // Ignore localStorage errors
    }
    applyDocumentDirection(lang);
  };

  const t = (key: string, fallback?: string): string => {
    const dict = translations[language];
    if (dict && dict[key]) {
      return dict[key];
    }
    // Fallback to French if missing
    if (translations.fr && translations.fr[key]) {
      return translations.fr[key];
    }
    return fallback !== undefined ? fallback : key;
  };

  const isRTL = language === "ar";
  const dir: "ltr" | "rtl" = isRTL ? "rtl" : "ltr";

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t, dir, isRTL }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useTranslation() {
  const context = useContext(LanguageContext);
  if (!context) {
    return {
      language: "fr" as Language,
      setLanguage: () => {},
      t: (key: string, fallback?: string) => fallback || key,
      dir: "ltr" as const,
      isRTL: false,
    };
  }
  return context;
}
