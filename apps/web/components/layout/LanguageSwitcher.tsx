"use client";

import React, { useState, useRef, useEffect } from "react";
import { Globe, ChevronDown, Check } from "lucide-react";
import { useTranslation } from "../../lib/i18n/LanguageContext";
import { Language } from "../../lib/i18n/translations";

interface LanguageOption {
  code: Language;
  label: string;
  nativeLabel: string;
  flag: string;
}

const LANGUAGES: LanguageOption[] = [
  { code: "fr", label: "Français", nativeLabel: "Français", flag: "🇫🇷" },
  { code: "ar", label: "Arabe", nativeLabel: "العربية", flag: "🇸🇦" },
  { code: "en", label: "Anglais", nativeLabel: "English", flag: "🇬🇧" },
];

export function LanguageSwitcher({ className = "" }: { className?: string }) {
  const { language, setLanguage } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const currentLang = LANGUAGES.find((l) => l.code === language) || LANGUAGES[0];

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div ref={dropdownRef} className={`relative inline-block text-left ${className}`}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-1.5 rounded-xl border border-slate-800 bg-slate-900/80 px-2.5 py-1.5 text-xs font-medium text-slate-200 transition hover:border-slate-700 hover:bg-slate-800/90 hover:text-white focus:outline-none focus:ring-1 focus:ring-indigo-500 shadow-sm"
        aria-label="Changer de langue / Change language / تغيير اللغة"
      >
        <span className="text-sm leading-none">{currentLang.flag}</span>
        <span className="font-semibold text-[11px]">{currentLang.nativeLabel}</span>
        <ChevronDown className={`h-3 w-3 text-slate-400 transition-transform duration-200 ${isOpen ? "rotate-180" : ""}`} />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-1.5 w-44 origin-top-right rounded-2xl border border-slate-800 bg-slate-950/95 p-1.5 shadow-2xl backdrop-blur-xl ring-1 ring-black ring-opacity-5 z-50">
          <div className="px-2 py-1 text-[10px] font-semibold uppercase tracking-wider text-slate-400 border-b border-slate-800/60 mb-1 flex items-center gap-1.5">
            <Globe className="h-3 w-3 text-indigo-400" />
            <span>Langue / Language / اللغة</span>
          </div>

          <div className="space-y-0.5">
            {LANGUAGES.map((lang) => {
              const isSelected = lang.code === language;
              return (
                <button
                  key={lang.code}
                  type="button"
                  onClick={() => {
                    setLanguage(lang.code);
                    setIsOpen(false);
                  }}
                  className={`flex w-full items-center justify-between rounded-xl px-2.5 py-1.5 text-xs font-medium transition ${
                    isSelected
                      ? "bg-indigo-600/20 text-indigo-300 font-semibold border border-indigo-500/30"
                      : "text-slate-300 hover:bg-slate-900 hover:text-white"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span className="text-sm">{lang.flag}</span>
                    <span>{lang.nativeLabel}</span>
                  </div>
                  {isSelected && <Check className="h-3.5 w-3.5 text-indigo-400" />}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
