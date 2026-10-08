"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Download,
  Palette,
  Loader2,
  Check,
  ArrowLeft,
  Share2,
  Sparkles,
} from "lucide-react";
import {
  Presentation,
  PresentationTheme,
  UpdatePresentationPayload,
} from "../../types/presentation";

interface PresentationToolbarProps {
  presentation: Presentation;
  onUpdateMetadata: (payload: UpdatePresentationPayload) => Promise<void>;
  onExport: (asyncMode?: boolean) => Promise<void>;
  isExporting: boolean;
  isSavingMeta: boolean;
}

const THEME_OPTIONS: { id: PresentationTheme; label: string; previewColor: string }[] = [
  { id: "modern_dark", label: "Moderne Sombre", previewColor: "bg-slate-900 border-indigo-500" },
  { id: "minimal_light", label: "Minimaliste Clair", previewColor: "bg-slate-100 border-blue-500" },
  { id: "academic_indigo", label: "Académique Indigo", previewColor: "bg-indigo-950 border-amber-400" },
  { id: "corporate_blue", label: "Entreprise Bleu", previewColor: "bg-[#0b192c] border-sky-400" },
];

export const PresentationToolbar: React.FC<PresentationToolbarProps> = ({
  presentation,
  onUpdateMetadata,
  onExport,
  isExporting,
  isSavingMeta,
}) => {
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [titleValue, setTitleValue] = useState(presentation.title);
  const [themeDropdownOpen, setThemeDropdownOpen] = useState(false);

  const handleTitleSubmit = async () => {
    setIsEditingTitle(false);
    if (titleValue.trim() && titleValue !== presentation.title) {
      await onUpdateMetadata({ title: titleValue.trim() });
    } else {
      setTitleValue(presentation.title);
    }
  };

  const handleThemeChange = async (theme: PresentationTheme) => {
    setThemeDropdownOpen(false);
    if (theme !== presentation.theme) {
      await onUpdateMetadata({ theme });
    }
  };

  return (
    <header className="h-16 bg-slate-900 border-b border-slate-800 px-4 lg:px-6 flex items-center justify-between gap-4 z-20">
      {/* Left: Back Link & Title */}
      <div className="flex items-center gap-3 min-w-0">
        <Link
          href={`/courses/${presentation.course}`}
          className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition shrink-0"
          title="Retour au cours"
        >
          <ArrowLeft className="w-4 h-4" />
        </Link>

        <div className="min-w-0 flex flex-col">
          {/* Editable Title */}
          {isEditingTitle ? (
            <input
              type="text"
              autoFocus
              value={titleValue}
              onChange={(e) => setTitleValue(e.target.value)}
              onBlur={handleTitleSubmit}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleTitleSubmit();
                if (e.key === "Escape") {
                  setTitleValue(presentation.title);
                  setIsEditingTitle(false);
                }
              }}
              className="text-sm font-bold text-white bg-slate-950 px-2 py-0.5 rounded border border-indigo-500 focus:outline-none"
            />
          ) : (
            <div
              onClick={() => {
                setTitleValue(presentation.title);
                setIsEditingTitle(true);
              }}
              className="flex items-center gap-1.5 cursor-pointer group"
              title="Cliquer pour renommer"
            >
              <h1 className="text-sm font-bold text-slate-100 group-hover:text-indigo-300 truncate transition">
                {presentation.title}
              </h1>
              <span className="text-[10px] text-slate-500 opacity-0 group-hover:opacity-100 transition">
                (modifier)
              </span>
            </div>
          )}

          {/* Subtitle / Breadcrumb */}
          <span className="text-xs text-slate-400 truncate">
            Cours : {presentation.course_title || "Cours source"}
          </span>
        </div>
      </div>

      {/* Right: Theme Picker & Export PPTX */}
      <div className="flex items-center gap-2.5 shrink-0">
        {/* Theme Picker Dropdown */}
        <div className="relative">
          <button
            onClick={() => setThemeDropdownOpen(!themeDropdownOpen)}
            disabled={isSavingMeta}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800/80 hover:bg-slate-800 border border-slate-700/80 text-xs font-medium text-slate-200 transition"
          >
            <Palette className="w-3.5 h-3.5 text-indigo-400" />
            <span className="hidden sm:inline">Thème :</span>
            <span className="capitalize">
              {THEME_OPTIONS.find((t) => t.id === presentation.theme)?.label || presentation.theme}
            </span>
          </button>

          {themeDropdownOpen && (
            <div className="absolute right-0 mt-2 w-52 bg-slate-900 border border-slate-800 rounded-xl shadow-2xl p-1.5 space-y-1 z-50">
              <div className="px-2 py-1 text-[10px] font-semibold uppercase tracking-wider text-slate-500">
                Choisir un style visuel
              </div>
              {THEME_OPTIONS.map((th) => (
                <button
                  key={th.id}
                  onClick={() => handleThemeChange(th.id)}
                  className={`w-full flex items-center justify-between px-2.5 py-2 rounded-lg text-xs transition ${
                    presentation.theme === th.id
                      ? "bg-indigo-600/20 text-indigo-300 font-semibold"
                      : "text-slate-300 hover:bg-slate-800 hover:text-white"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span className={`w-3.5 h-3.5 rounded-full border ${th.previewColor}`} />
                    <span>{th.label}</span>
                  </div>
                  {presentation.theme === th.id && <Check className="w-3.5 h-3.5 text-indigo-400" />}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Existing Export Download link if storage_key is set */}
        {presentation.export_url && (
          <a
            href={presentation.export_url}
            target="_blank"
            rel="noopener noreferrer"
            download
            className="hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-950/40 border border-emerald-800/80 text-xs font-semibold text-emerald-300 hover:bg-emerald-900/60 transition"
            title="Télécharger le dernier fichier PPTX exporté"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Fichier PPTX</span>
          </a>
        )}

        {/* Export PPTX button */}
        <button
          onClick={() => onExport(false)}
          disabled={isExporting}
          className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold text-xs transition shadow-md shadow-indigo-950 active:scale-95"
        >
          {isExporting ? (
            <>
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              <span>Génération PPTX...</span>
            </>
          ) : (
            <>
              <Download className="w-3.5 h-3.5" />
              <span>Exporter PPTX</span>
            </>
          )}
        </button>
      </div>
    </header>
  );
};
