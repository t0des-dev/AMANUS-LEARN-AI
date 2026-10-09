"use client";

import React, { useState, useEffect } from "react";
import { Mic, Check, Globe, User, Sparkles } from "lucide-react";
import { TTSVoice } from "../../types/audio";
import { audioService } from "../../services/audioService";
import { useAuth } from "../auth/AuthProvider";
import { useTranslation } from "../../lib/i18n/LanguageContext";

interface VoiceSelectorProps {
  selectedVoiceId: string;
  selectedProvider: string;
  initialLanguage?: string;
  onSelectVoice: (voiceId: string, provider: string, language?: string) => void;
  className?: string;
}

export function VoiceSelector({
  selectedVoiceId,
  selectedProvider,
  initialLanguage,
  onSelectVoice,
  className = "",
}: VoiceSelectorProps) {
  const { token } = useAuth();
  const { t, language: currentAppLang } = useTranslation();
  const [voices, setVoices] = useState<TTSVoice[]>([]);
  const [languageFilter, setLanguageFilter] = useState<string>(
    initialLanguage || (currentAppLang === "ar" ? "ar" : currentAppLang === "en" ? "en" : "fr")
  );
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadVoices() {
      if (!token) return;
      try {
        const list = await audioService.listVoices(token);
        setVoices(list);
      } catch {
        // Fallback default mock voices if API fails
        setVoices([
          {
            id: "pierre",
            name: "Pierre",
            language: "fr",
            gender: "male",
            provider: "mock",
            description: "Voix masculine posée, claire et académique.",
          },
          {
            id: "marie",
            name: "Marie",
            language: "fr",
            gender: "female",
            provider: "mock",
            description: "Voix féminine dynamique et chaleureuse.",
          },
          {
            id: "clara",
            name: "Clara",
            language: "fr",
            gender: "female",
            provider: "mock",
            description: "Voix féminine douce, idéale pour les révisions.",
          },
          {
            id: "tariq",
            name: "Tariq (طارق)",
            language: "ar",
            gender: "male",
            provider: "mock",
            description: "Voix masculine arabe claire, éloquente et académique.",
          },
          {
            id: "layla",
            name: "Layla (ليلى)",
            language: "ar",
            gender: "female",
            provider: "mock",
            description: "Voix féminine arabe douce, dynamique et pédagogique.",
          },
          {
            id: "omar",
            name: "Omar (عمر)",
            language: "ar",
            gender: "male",
            provider: "mock",
            description: "Voix masculine arabe posée et chaleureuse pour les cours.",
          },
          {
            id: "fatima",
            name: "Fatima (فاطمة)",
            language: "ar",
            gender: "female",
            provider: "mock",
            description: "Voix féminine arabe claire, professionnelle et articulée.",
          },
          {
            id: "adam",
            name: "Adam",
            language: "en",
            gender: "male",
            provider: "mock",
            description: "English male narrator, articulate and balanced.",
          },
          {
            id: "rachel",
            name: "Rachel",
            language: "en",
            gender: "female",
            provider: "mock",
            description: "English female speaker, professional and clear.",
          },
          {
            id: "alloy",
            name: "Alloy (OpenAI)",
            language: "fr",
            gender: "neutral",
            provider: "openai",
            description: "Voix OpenAI fluide et polyvalente.",
          },
        ]);
      } finally {
        setIsLoading(false);
      }
    }
    loadVoices();
  }, [token]);

  const filteredVoices = voices.filter((v) =>
    languageFilter ? v.language.toLowerCase() === languageFilter.toLowerCase() : true
  );

  return (
    <div className={`flex flex-col gap-3 ${className}`}>
      {/* Language toggle tabs */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-2">
        <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
          <Mic className="h-3.5 w-3.5 text-indigo-400" />
          <span>{t("audio.selectVoice")}</span>
        </label>

        <div className="flex items-center gap-1 bg-slate-900 rounded-lg p-0.5 border border-slate-800">
          <button
            type="button"
            onClick={() => setLanguageFilter("fr")}
            className={`px-2 py-0.5 text-[10px] font-semibold rounded-md transition ${
              languageFilter === "fr"
                ? "bg-indigo-600 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            🇫🇷 Français
          </button>
          <button
            type="button"
            onClick={() => setLanguageFilter("ar")}
            className={`px-2 py-0.5 text-[10px] font-semibold rounded-md transition ${
              languageFilter === "ar"
                ? "bg-indigo-600 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            🇸🇦 العربية (AR)
          </button>
          <button
            type="button"
            onClick={() => setLanguageFilter("en")}
            className={`px-2 py-0.5 text-[10px] font-semibold rounded-md transition ${
              languageFilter === "en"
                ? "bg-indigo-600 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            🇬🇧 English
          </button>
        </div>
      </div>

      {/* Voice cards grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-56 overflow-y-auto pr-1">
        {isLoading ? (
          <div className="col-span-2 py-4 text-center text-xs text-slate-500">
            {t("audio.loadingVoices")}
          </div>
        ) : filteredVoices.length === 0 ? (
          <div className="col-span-2 py-4 text-center text-xs text-slate-500">
            {t("audio.noVoicesForLanguage")}
          </div>
        ) : (
          filteredVoices.map((voice) => {
            const isSelected =
              selectedVoiceId === voice.id && selectedProvider === voice.provider;

            return (
              <button
                key={`${voice.provider}-${voice.id}-${voice.language}`}
                type="button"
                onClick={() => onSelectVoice(voice.id, voice.provider, voice.language)}
                className={`flex items-start justify-between rounded-xl border p-2.5 text-left transition ${
                  isSelected
                    ? "border-indigo-500 bg-indigo-950/40 shadow-sm shadow-indigo-950 ring-1 ring-indigo-500"
                    : "border-slate-800/80 bg-slate-900/60 hover:border-slate-700 hover:bg-slate-900"
                }`}
              >
                <div className="flex items-start gap-2 overflow-hidden">
                  <div
                    className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-lg ${
                      isSelected
                        ? "bg-indigo-600 text-white"
                        : "bg-slate-800 text-slate-400"
                    }`}
                  >
                    <User className="h-3.5 w-3.5" />
                  </div>

                  <div className="overflow-hidden">
                    <div className="flex items-center gap-1.5">
                      <span className="text-xs font-semibold text-slate-100 truncate">
                        {voice.name}
                      </span>
                      <span className="rounded bg-slate-800 px-1 py-0.2 text-[9px] uppercase font-mono text-slate-400">
                        {voice.provider}
                      </span>
                    </div>
                    <p className="mt-0.5 text-[10px] text-slate-400 line-clamp-1">
                      {voice.description || `${voice.gender} • ${voice.language}`}
                    </p>
                  </div>
                </div>

                {isSelected && (
                  <div className="flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-indigo-500 text-white">
                    <Check className="h-2.5 w-2.5 stroke-[3]" />
                  </div>
                )}
              </button>
            );
          })
        )}
      </div>
    </div>
  );
}
