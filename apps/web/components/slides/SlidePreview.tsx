"use client";

import React, { useState, useEffect } from "react";
import {
  ChevronLeft,
  ChevronRight,
  Maximize2,
  Minimize2,
  MessageSquareQuote,
  Sparkles,
  BookOpen,
} from "lucide-react";
import { Presentation, PresentationSlide, PresentationTheme } from "../../types/presentation";

interface SlidePreviewProps {
  presentation: Presentation;
  currentSlide: PresentationSlide | null;
  currentIndex: number;
  totalSlides: number;
  onPrev: () => void;
  onNext: () => void;
}

const THEME_STYLES: Record<
  PresentationTheme,
  {
    bg: string;
    cardBg: string;
    cardBorder: string;
    titleColor: string;
    subtitleColor: string;
    textColor: string;
    accentColor: string;
    footerColor: string;
  }
> = {
  modern_dark: {
    bg: "bg-slate-950 text-slate-100",
    cardBg: "bg-slate-900/90",
    cardBorder: "border-slate-800",
    titleColor: "text-white",
    subtitleColor: "text-slate-400",
    textColor: "text-slate-200",
    accentColor: "text-indigo-400",
    footerColor: "text-slate-500",
  },
  minimal_light: {
    bg: "bg-slate-50 text-slate-900",
    cardBg: "bg-white",
    cardBorder: "border-slate-200 shadow-sm",
    titleColor: "text-slate-900",
    subtitleColor: "text-slate-600",
    textColor: "text-slate-800",
    accentColor: "text-blue-600",
    footerColor: "text-slate-400",
  },
  academic_indigo: {
    bg: "bg-[#0f0c29] text-indigo-50",
    cardBg: "bg-[#1f1b4e]/80",
    cardBorder: "border-indigo-900/70",
    titleColor: "text-white",
    subtitleColor: "text-indigo-200",
    textColor: "text-indigo-100",
    accentColor: "text-amber-400",
    footerColor: "text-indigo-400",
  },
  corporate_blue: {
    bg: "bg-[#0b192c] text-slate-100",
    cardBg: "bg-[#1e3e62]/40",
    cardBorder: "border-[#1e3e62]",
    titleColor: "text-white",
    subtitleColor: "text-sky-200",
    textColor: "text-slate-200",
    accentColor: "text-sky-400",
    footerColor: "text-slate-400",
  },
};

export const SlidePreview: React.FC<SlidePreviewProps> = ({
  presentation,
  currentSlide,
  currentIndex,
  totalSlides,
  onPrev,
  onNext,
}) => {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showNotes, setShowNotes] = useState(false);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }
      if (e.key === "ArrowLeft") {
        onPrev();
      } else if (e.key === "ArrowRight" || e.key === " ") {
        onNext();
      } else if (e.key === "f" || e.key === "F") {
        setIsFullscreen((prev) => !prev);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onPrev, onNext]);

  if (!currentSlide) {
    return (
      <div className="flex-1 flex items-center justify-center bg-slate-950 p-8 text-slate-500">
        Sélectionnez une diapositive pour afficher la prévisualisation.
      </div>
    );
  }

  const themeConfig = THEME_STYLES[presentation.theme] || THEME_STYLES.modern_dark;
  const isTitleSlide = currentIndex === 0;

  const isArabic = (text?: string | null) => {
    if (!text) return false;
    return /[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]/.test(text);
  };

  const isSlideArabic = isArabic(currentSlide.title) || isArabic(currentSlide.content);

  // Check if content has two columns
  const isTwoColumn = (currentSlide.content || "").includes(" || ");
  const [leftColRaw, rightColRaw] = isTwoColumn
    ? (currentSlide.content || "").split(" || ")
    : ["", ""];
  const leftBullets = (leftColRaw || "")
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean);
  const rightBullets = (rightColRaw || "")
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean);

  // Split lines into clean pedagogical bullet points
  const bulletLines = (currentSlide.content || "")
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean);

  return (
    <div
      className={`relative flex flex-col items-center justify-center ${
        isFullscreen
          ? "fixed inset-0 z-50 bg-black p-4 md:p-8"
          : "flex-1 bg-slate-950/70 p-4 lg:p-8 overflow-hidden"
      }`}
    >
      {/* 16:9 Aspect Ratio Container */}
      <div className="w-full max-w-5xl aspect-[16/9] relative shadow-2xl rounded-2xl overflow-hidden border border-slate-800 transition-all">
        {/* Main Slide Board with theme background */}
        <div
          dir={isSlideArabic ? "rtl" : "ltr"}
          className={`w-full h-full p-8 md:p-12 flex flex-col justify-between select-none ${themeConfig.bg} ${
            isSlideArabic ? "text-right" : "text-left"
          }`}
        >
          {/* Top Bar: Badge & Course Title */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span
                className={`text-xs md:text-sm font-semibold tracking-wider uppercase font-mono px-3 py-1 rounded-full bg-black/20 ${themeConfig.accentColor}`}
              >
                {presentation.course_title || "Amanus Learn AI"}
              </span>
            </div>
            <div className={`text-xs md:text-sm font-mono ${themeConfig.footerColor}`}>
              {isSlideArabic
                ? `الشريحة ${currentIndex + 1} / ${totalSlides}`
                : `Diapositive ${currentIndex + 1} / ${totalSlides}`}
            </div>
          </div>

          {/* Slide Body */}
          {isTitleSlide ? (
            /* Title / Cover Slide Layout */
            <div
              className={`my-auto rounded-2xl p-8 md:p-12 border ${themeConfig.cardBg} ${themeConfig.cardBorder} flex flex-col justify-center items-center text-center`}
            >
              <div
                className={`flex items-center gap-2 text-xs md:text-sm font-bold tracking-widest uppercase mb-4 ${themeConfig.accentColor}`}
              >
                <BookOpen className="w-4 h-4" />
                <span>
                  {isSlideArabic ? "دعامة تعليمية تفاعلية" : "Support de Cours Interactif"}
                </span>
              </div>
              <h1
                className={`text-3xl md:text-5xl font-extrabold tracking-tight mb-6 max-w-3xl ${themeConfig.titleColor}`}
              >
                {currentSlide.title || presentation.title}
              </h1>
              {bulletLines.length > 0 && (
                <div className={`space-y-2 max-w-xl text-sm md:text-base ${themeConfig.subtitleColor}`}>
                  {bulletLines.map((line, idx) => (
                    <p key={idx}>{line}</p>
                  ))}
                </div>
              )}
            </div>
          ) : isTwoColumn ? (
            /* Two-Column Side-by-Side Layout */
            <div className="my-auto flex flex-col justify-center">
              <h2
                className={`text-2xl md:text-4xl font-bold tracking-tight mb-6 ${themeConfig.titleColor}`}
              >
                {currentSlide.title}
              </h2>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div
                  className={`rounded-2xl p-5 border ${themeConfig.cardBg} ${themeConfig.cardBorder} space-y-3`}
                >
                  {leftBullets.map((line, idx) => {
                    const cleanText = line.replace(/^[•\-*]\s*/, "");
                    return (
                      <div key={idx} className="flex items-start gap-3">
                        <span
                          className={`mt-1.5 w-2 h-2 rounded-full shrink-0 bg-current ${themeConfig.accentColor}`}
                        />
                        <p
                          className={`text-sm md:text-base font-normal leading-relaxed ${themeConfig.textColor}`}
                        >
                          {cleanText}
                        </p>
                      </div>
                    );
                  })}
                </div>

                <div
                  className={`rounded-2xl p-5 border ${themeConfig.cardBg} ${themeConfig.cardBorder} space-y-3`}
                >
                  {rightBullets.map((line, idx) => {
                    const cleanText = line.replace(/^[•\-*]\s*/, "");
                    return (
                      <div key={idx} className="flex items-start gap-3">
                        <span
                          className={`mt-1.5 w-2 h-2 rounded-full shrink-0 bg-current ${themeConfig.accentColor}`}
                        />
                        <p
                          className={`text-sm md:text-base font-normal leading-relaxed ${themeConfig.textColor}`}
                        >
                          {cleanText}
                        </p>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          ) : (
            /* Standard Content / Summary Slide Layout */
            <div className="my-auto flex flex-col justify-center">
              <h2
                className={`text-2xl md:text-4xl font-bold tracking-tight mb-6 ${themeConfig.titleColor}`}
              >
                {currentSlide.title}
              </h2>

              <div
                className={`rounded-2xl p-6 md:p-8 border ${themeConfig.cardBg} ${themeConfig.cardBorder} space-y-4`}
              >
                {bulletLines.length === 0 ? (
                  <p className="text-slate-500 italic text-sm">
                    {isSlideArabic
                      ? "لا يوجد محتوى لهذه الشريحة. استخدم المحرر على اليمين."
                      : "Aucun contenu pour cette diapositive. Utilisez l'éditeur à droite."}
                  </p>
                ) : (
                  bulletLines.map((line, idx) => {
                    const cleanText = line.replace(/^[•\-*✓]\s*/, "");
                    const isCheck = line.startsWith("✓");
                    return (
                      <div key={idx} className="flex items-start gap-3">
                        {isCheck ? (
                          <span
                            className={`mt-0.5 font-bold text-sm shrink-0 ${themeConfig.accentColor}`}
                          >
                            ✓
                          </span>
                        ) : (
                          <span
                            className={`mt-1.5 w-2 h-2 rounded-full shrink-0 bg-current ${themeConfig.accentColor}`}
                          />
                        )}
                        <p
                          className={`text-base md:text-xl font-normal leading-relaxed ${themeConfig.textColor}`}
                        >
                          {cleanText}
                        </p>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          )}

          {/* Slide Footer */}
          <div className="flex items-center justify-between text-xs md:text-sm border-t border-white/10 pt-4">
            <span className={themeConfig.footerColor}>
              Amanus Learn AI • {presentation.title}
            </span>
            {currentSlide.image_prompt && (
              <span
                className={`flex items-center gap-1.5 text-xs truncate max-w-xs ${themeConfig.accentColor}`}
                title={currentSlide.image_prompt}
              >
                <Sparkles className="w-3.5 h-3.5 shrink-0" />
                <span className="truncate">Visuel suggéré disponible</span>
              </span>
            )}
          </div>
        </div>

        {/* Floating Navigation Arrows on Left & Right */}
        <button
          onClick={onPrev}
          disabled={currentIndex === 0}
          title="Précédent (Flèche gauche)"
          className="absolute left-3 top-1/2 -translate-y-1/2 p-2.5 rounded-full bg-black/40 hover:bg-black/70 text-white backdrop-blur-md transition disabled:opacity-0"
        >
          <ChevronLeft className="w-5 h-5" />
        </button>
        <button
          onClick={onNext}
          disabled={currentIndex === totalSlides - 1}
          title="Suivant (Flèche droite / Espace)"
          className="absolute right-3 top-1/2 -translate-y-1/2 p-2.5 rounded-full bg-black/40 hover:bg-black/70 text-white backdrop-blur-md transition disabled:opacity-0"
        >
          <ChevronRight className="w-5 h-5" />
        </button>
      </div>

      {/* Floating Controls Bar under preview */}
      <div className="mt-4 flex items-center gap-3">
        <button
          onClick={onPrev}
          disabled={currentIndex === 0}
          className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs font-medium text-slate-300 hover:text-white hover:bg-slate-800 disabled:opacity-40 transition flex items-center gap-1"
        >
          <ChevronLeft className="w-3.5 h-3.5" />
          Précédent
        </button>
        <span className="text-xs font-mono text-slate-400 px-2">
          {currentIndex + 1} / {totalSlides}
        </span>
        <button
          onClick={onNext}
          disabled={currentIndex === totalSlides - 1}
          className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs font-medium text-slate-300 hover:text-white hover:bg-slate-800 disabled:opacity-40 transition flex items-center gap-1"
        >
          Suivant
          <ChevronRight className="w-3.5 h-3.5" />
        </button>

        <div className="h-4 w-px bg-slate-800 mx-1" />

        <button
          onClick={() => setShowNotes(!showNotes)}
          className={`px-3 py-1.5 rounded-lg border text-xs font-medium transition flex items-center gap-1.5 ${
            showNotes
              ? "bg-indigo-600/20 border-indigo-500 text-indigo-300"
              : "bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200"
          }`}
        >
          <MessageSquareQuote className="w-3.5 h-3.5" />
          <span>Notes orateur</span>
        </button>

        <button
          onClick={() => setIsFullscreen(!isFullscreen)}
          className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-white transition"
          title={isFullscreen ? "Quitter plein écran (Esc)" : "Mode Plein Écran (F)"}
        >
          {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
        </button>
      </div>

      {/* Collapsible Speaker Notes Drawer */}
      {showNotes && (
        <div className="mt-3 w-full max-w-5xl bg-slate-900/90 border border-slate-800 rounded-xl p-4 text-xs text-slate-300 backdrop-blur-sm animate-in fade-in slide-in-from-top-2">
          <div className="flex items-center gap-2 text-indigo-400 font-semibold mb-1.5">
            <MessageSquareQuote className="w-4 h-4" />
            <span>Notes du présentateur pour cette slide</span>
          </div>
          <p className="leading-relaxed whitespace-pre-wrap text-slate-300 font-sans">
            {currentSlide.speaker_notes || "Aucune note orateur rédigée."}
          </p>
        </div>
      )}
    </div>
  );
};
