"use client";

import React, { useState, useEffect, useMemo, useCallback } from "react";
import Link from "next/link";
import {
  Clock,
  Target,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Edit3,
  Bookmark,
  Info,
  Lightbulb,
  AlertTriangle,
  AlertCircle,
  Sparkles,
  Copy,
  Check,
  FileText,
  Layers,
  Maximize2,
  Minimize2,
  Compass,
  ArrowRight,
  ArrowLeft,
  Award,
} from "lucide-react";
import { CourseSectionItem } from "../../types/course";
import { AudioGenerationButton } from "../../components/audio/AudioGenerationButton";
import { useTranslation } from "../../lib/i18n/LanguageContext";

export interface LessonViewerProps {
  courseId: string;
  lesson: CourseSectionItem;
  axisTitle?: string;
  hasPrevAxis?: boolean;
  hasNextAxis?: boolean;
  onNextAxis?: () => void;
  onPrevAxis?: () => void;
  isCompleted?: boolean;
  onToggleComplete?: () => void;
  onNext?: () => void;
  onPrev?: () => void;
  hasPrev?: boolean;
  hasNext?: boolean;
  isTeacher?: boolean;
}

export interface SlideItem {
  id: string;
  type: "intro" | "content" | "summary";
  title: string;
  subtitle?: string;
  content?: string;
  objectives?: string[];
  summaryText?: string;
}

/**
 * Parses inline formatting:
 * - Citations [1], [2], [Doc 1] -> interactive badge
 * - **bold** -> strong
 * - *italic* -> em
 * - `code` -> inline code
 */
function renderInlineContent(text: string): React.ReactNode {
  if (!text) return null;

  const tokens = text.split(/(\[\d+\]|\[Doc\s*\d+\]|\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g);

  return tokens.map((token, idx) => {
    if (!token) return null;

    if (/^\[(\d+|Doc\s*\d+)\]$/.test(token)) {
      return (
        <span
          key={idx}
          className="inline-flex items-center px-1.5 py-0.5 mx-1 rounded text-[11px] font-mono font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 hover:bg-indigo-500/30 hover:text-white transition-all shadow-sm cursor-help select-none align-baseline"
          title="Source documentaire vérifiée"
        >
          {token}
        </span>
      );
    }

    if (token.startsWith("**") && token.endsWith("**")) {
      return (
        <strong key={idx} className="font-bold text-white tracking-wide">
          {token.slice(2, -2)}
        </strong>
      );
    }

    if (token.startsWith("*") && token.endsWith("*") && !token.startsWith("**")) {
      return (
        <em key={idx} className="italic text-slate-200">
          {token.slice(1, -1)}
        </em>
      );
    }

    if (token.startsWith("`") && token.endsWith("`")) {
      return (
        <code
          key={idx}
          className="px-1.5 py-0.5 rounded-md bg-slate-900 border border-slate-800 text-indigo-300 font-mono text-xs shadow-inner"
        >
          {token.slice(1, -1)}
        </code>
      );
    }

    return token;
  });
}

function CodeBlockCard({ code, language }: { code: string; language?: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-950 overflow-hidden my-4 shadow-xl">
      <div className="flex items-center justify-between px-4 py-2 border-b border-slate-800/80 bg-slate-900/60 text-xs text-slate-400 font-mono">
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500/80" />
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500/80" />
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500/80" />
          </div>
          <span className="text-[11px] text-slate-500 ml-2">
            {language || "code"}
          </span>
        </div>
        <button
          type="button"
          onClick={handleCopy}
          className="flex items-center gap-1 text-[11px] hover:text-white transition px-2 py-0.5 rounded-md hover:bg-slate-800"
        >
          {copied ? (
            <>
              <Check className="w-3 h-3 text-emerald-400" />
              <span className="text-emerald-400">Copié</span>
            </>
          ) : (
            <>
              <Copy className="w-3 h-3" />
              <span>Copier</span>
            </>
          )}
        </button>
      </div>
      <pre className="p-4 text-xs sm:text-sm font-mono text-slate-200 overflow-x-auto leading-relaxed">
        <code>{code}</code>
      </pre>
    </div>
  );
}

function MarkdownRenderer({ content, isRTL }: { content: string; isRTL: boolean }) {
  if (!content) return null;

  const rawBlocks = content.split(/\n\n+/);

  return (
    <div
      className={`space-y-5 text-slate-300 leading-relaxed ${
        isRTL ? "text-right" : "text-left"
      }`}
      dir={isRTL ? "rtl" : "ltr"}
    >
      {rawBlocks.map((block, bIdx) => {
        const trimmed = block.trim();
        if (!trimmed) return null;

        // Code Block
        if (trimmed.startsWith("```")) {
          const match = trimmed.match(/^```([a-zA-Z0-9_-]*)\n([\s\S]*?)```$/);
          if (match) {
            return (
              <CodeBlockCard
                key={bIdx}
                language={match[1] || "text"}
                code={match[2].trim()}
              />
            );
          }
        }

        // Heading 1
        if (trimmed.startsWith("# ")) {
          return (
            <h2
              key={bIdx}
              className="text-2xl font-black text-white pt-6 pb-3 border-b border-slate-800/90 tracking-tight flex items-center gap-2.5"
            >
              <span className="w-2 h-6 rounded-full bg-gradient-to-b from-indigo-500 to-purple-600 inline-block" />
              <span>{renderInlineContent(trimmed.replace(/^#\s+/, ""))}</span>
            </h2>
          );
        }

        // Heading 2
        if (trimmed.startsWith("## ")) {
          return (
            <h3
              key={bIdx}
              className="text-lg sm:text-xl font-bold text-slate-100 pt-5 pb-2 border-b border-slate-800/50 tracking-tight flex items-center gap-2"
            >
              <span className="w-1.5 h-4 rounded-full bg-indigo-500 inline-block" />
              <span>{renderInlineContent(trimmed.replace(/^##\s+/, ""))}</span>
            </h3>
          );
        }

        // Heading 3
        if (trimmed.startsWith("### ")) {
          return (
            <h4
              key={bIdx}
              className="text-base font-semibold text-indigo-300 pt-3 pb-1 flex items-center gap-2"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 inline-block" />
              <span>{renderInlineContent(trimmed.replace(/^###\s+/, ""))}</span>
            </h4>
          );
        }

        // Blockquotes & Callouts
        if (trimmed.startsWith(">")) {
          const quoteLines = trimmed
            .split("\n")
            .map((line) => line.replace(/^>\s?/, "").trim())
            .join(" ");

          const lower = quoteLines.toLowerCase();
          const isTip =
            lower.includes("[!tip]") ||
            lower.includes("conseil") ||
            lower.includes("نصيحة") ||
            lower.includes("أفضل ممارسة");
          const isWarning =
            lower.includes("[!warning]") ||
            lower.includes("attention") ||
            lower.includes("تحذير");
          const isImportant =
            lower.includes("[!important]") ||
            lower.includes("important") ||
            lower.includes("تنبيه مهم") ||
            lower.includes("point clé");
          const isDef =
            lower.includes("définition") ||
            lower.includes("تعريف") ||
            lower.includes("règle");

          const cleanQuote = quoteLines.replace(
            /^\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*/i,
            ""
          );

          let borderStyle = "border-indigo-500/40 bg-indigo-950/20 text-indigo-200";
          let icon = <Info className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />;
          let title = "Note clé";

          if (isTip) {
            borderStyle = "border-emerald-500/40 bg-emerald-950/20 text-emerald-200";
            icon = <Lightbulb className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />;
            title = "Conseil didactique";
          } else if (isWarning) {
            borderStyle = "border-rose-500/40 bg-rose-950/20 text-rose-200";
            icon = <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />;
            title = "Point de vigilance";
          } else if (isImportant) {
            borderStyle = "border-amber-500/40 bg-amber-950/20 text-amber-200";
            icon = <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />;
            title = "Élément essentiel";
          } else if (isDef) {
            borderStyle = "border-purple-500/40 bg-purple-950/20 text-purple-200";
            icon = <Sparkles className="w-4 h-4 text-purple-400 shrink-0 mt-0.5" />;
            title = "Définition & Cadre";
          }

          return (
            <div
              key={bIdx}
              className={`rounded-2xl border p-4.5 sm:p-5 my-4 backdrop-blur-sm shadow-md transition-all ${borderStyle} ${
                isRTL ? "border-r-4 pr-5 pl-4" : "border-l-4 pl-5 pr-4"
              }`}
            >
              <div className="flex items-start gap-3">
                {icon}
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-bold uppercase tracking-wider mb-1.5 opacity-90">
                    {title}
                  </div>
                  <div className="text-xs sm:text-sm leading-relaxed">
                    {renderInlineContent(cleanQuote)}
                  </div>
                </div>
              </div>
            </div>
          );
        }

        // Unordered Lists
        if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
          const items = trimmed
            .split("\n")
            .filter((line) => line.trim().startsWith("- ") || line.trim().startsWith("* "));

          return (
            <ul key={bIdx} className="space-y-2.5 my-3 pl-1 sm:pl-2">
              {items.map((item, iIdx) => {
                const text = item.replace(/^[-*]\s+/, "");
                return (
                  <li
                    key={iIdx}
                    className="flex items-start gap-3 text-xs sm:text-sm text-slate-300 leading-relaxed"
                  >
                    <span className="w-2 h-2 rounded-full bg-indigo-400 shrink-0 mt-1.5 shadow-sm shadow-indigo-500/50" />
                    <span className="flex-1">{renderInlineContent(text)}</span>
                  </li>
                );
              })}
            </ul>
          );
        }

        // Numbered Lists
        if (/^\d+\.\s/.test(trimmed)) {
          const items = trimmed.split("\n").filter((line) => /^\d+\.\s/.test(line.trim()));

          return (
            <ol key={bIdx} className="space-y-2.5 my-3 pl-1 sm:pl-2">
              {items.map((item, iIdx) => {
                const match = item.trim().match(/^(\d+)\.\s+(.*)$/);
                const num = match ? match[1] : `${iIdx + 1}`;
                const text = match ? match[2] : item;

                return (
                  <li
                    key={iIdx}
                    className="flex items-start gap-3 text-xs sm:text-sm text-slate-300 leading-relaxed"
                  >
                    <span className="w-5 h-5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 flex items-center justify-center text-[11px] font-mono font-bold shrink-0 mt-0.5 shadow-sm">
                      {num}
                    </span>
                    <span className="flex-1">{renderInlineContent(text)}</span>
                  </li>
                );
              })}
            </ol>
          );
        }

        // Markdown Tables
        if (trimmed.includes("|") && trimmed.split("\n").length >= 2) {
          const lines = trimmed.split("\n").map((l) => l.trim()).filter((l) => l.startsWith("|"));
          if (lines.length >= 2) {
            const headerCells = lines[0]
              .split("|")
              .filter((c, i, arr) => i > 0 && i < arr.length - 1)
              .map((c) => c.trim());

            const bodyRows = lines
              .slice(2)
              .map((row) =>
                row
                  .split("|")
                  .filter((c, i, arr) => i > 0 && i < arr.length - 1)
                  .map((c) => c.trim())
              );

            return (
              <div
                key={bIdx}
                className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/40 my-5 shadow-lg"
              >
                <table className="w-full text-left text-xs sm:text-sm">
                  <thead className="bg-slate-950/80 text-white font-semibold border-b border-slate-800">
                    <tr>
                      {headerCells.map((h, hIdx) => (
                        <th key={hIdx} className="p-3.5">
                          {renderInlineContent(h)}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {bodyRows.map((r, rIdx) => (
                      <tr key={rIdx} className="hover:bg-slate-850/50 transition">
                        {r.map((cell, cIdx) => (
                          <td key={cIdx} className="p-3.5 text-slate-300">
                            {renderInlineContent(cell)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            );
          }
        }

        // Default Paragraph
        return (
          <p
            key={bIdx}
            className="text-xs sm:text-sm sm:leading-relaxed md:text-base md:leading-loose text-slate-300"
          >
            {renderInlineContent(trimmed)}
          </p>
        );
      })}
    </div>
  );
}

/**
 * Splits raw lesson content and pedagogical metadata into a sequence of structured slides.
 */
function buildSlides(
  lesson: CourseSectionItem,
  axisTitle?: string,
  t?: (key: string, defaultText?: string) => string
): SlideItem[] {
  const slides: SlideItem[] = [];

  // Slide 1: Introduction & Learning Objectives
  slides.push({
    id: "slide-intro",
    type: "intro",
    title: lesson.title,
    subtitle: axisTitle || t?.("courses.axisOverview", "نظرة عامة على المحور"),
    objectives: lesson.objectives || [],
    summaryText: lesson.summary || "",
  });

  const rawContent = lesson.content ? lesson.content.trim() : "";

  if (rawContent) {
    // 1. Check if major headings (##) exist to structure slides by topic
    const rawBlocks = rawContent.split(/\n(?=##\s+)/).map((b) => b.trim()).filter(Boolean);

    // Merge any bare heading (block without substantive body) with the following block
    const mergedBlocks: string[] = [];
    for (let i = 0; i < rawBlocks.length; i++) {
      const b = rawBlocks[i];
      const lines = b.split("\n").map((l) => l.trim()).filter(Boolean);
      // If it only has 1 line (just a heading) and there is a subsequent block, merge them
      if (lines.length <= 1 && i < rawBlocks.length - 1) {
        rawBlocks[i + 1] = `${b}\n\n${rawBlocks[i + 1]}`;
      } else {
        mergedBlocks.push(b);
      }
    }

    if (mergedBlocks.length > 1) {
      mergedBlocks.forEach((block, idx) => {
        const firstLine = block.split("\n")[0] || "";
        const cleanTitle = firstLine.replace(/^#{1,3}\s+/, "").replace(/[*_`]/g, "").trim();
        const bodyContent = block.substring(firstLine.length).trim();

        slides.push({
          id: `slide-content-${idx + 1}`,
          type: "content",
          title: cleanTitle || `${lesson.title} - ${idx + 1}`,
          content: bodyContent || block,
        });
      });
    } else if (mergedBlocks.length === 1) {
      const singleBlock = mergedBlocks[0];
      const firstLine = singleBlock.split("\n")[0] || "";
      const isHeading = /^#{1,3}\s+/.test(firstLine);
      const cleanTitle = isHeading
        ? firstLine.replace(/^#{1,3}\s+/, "").replace(/[*_`]/g, "").trim()
        : lesson.title;
      const bodyContent = isHeading
        ? singleBlock.substring(firstLine.length).trim()
        : singleBlock;

      // Partition into readable slides of 2-3 paragraphs
      const paragraphs = (bodyContent || singleBlock).split(/\n\n+/).filter((p) => p.trim());
      if (paragraphs.length <= 2) {
        slides.push({
          id: "slide-content-main",
          type: "content",
          title: cleanTitle || lesson.title,
          content: bodyContent || singleBlock,
        });
      } else {
        const chunkSize = 2;
        for (let i = 0; i < paragraphs.length; i += chunkSize) {
          const slice = paragraphs.slice(i, i + chunkSize);
          slides.push({
            id: `slide-content-${Math.floor(i / chunkSize) + 1}`,
            type: "content",
            title: i === 0 ? cleanTitle : `${cleanTitle} (${Math.floor(i / chunkSize) + 1})`,
            content: slice.join("\n\n"),
          });
        }
      }
    } else {
      // 2. If no headings, partition by double-newlines into 2-3 paragraphs per slide
      const paragraphs = rawContent.split(/\n\n+/).filter((p) => p.trim());
      if (paragraphs.length <= 2) {
        slides.push({
          id: "slide-content-main",
          type: "content",
          title: lesson.title,
          content: rawContent,
        });
      } else {
        const chunkSize = 2;
        for (let i = 0; i < paragraphs.length; i += chunkSize) {
          const slice = paragraphs.slice(i, i + chunkSize);
          const firstSnippet = slice[0].slice(0, 60).replace(/[#*_\n]/g, "").trim();
          slides.push({
            id: `slide-content-${Math.floor(i / chunkSize) + 1}`,
            type: "content",
            title: firstSnippet || `${lesson.title} (${Math.floor(i / chunkSize) + 1})`,
            content: slice.join("\n\n"),
          });
        }
      }
    }
  }

  // Final Slide: Key Takeaways & Self-Check
  slides.push({
    id: "slide-summary",
    type: "summary",
    title: t?.("courses.keyTakeaways", "النقاط الجوهرية والخلاصة") || "Points clés & Synthèse",
    subtitle: lesson.title,
    summaryText:
      lesson.summary ||
      "Consolidation des acquis pédagogiques et validation des objectifs de la leçon.",
    objectives: lesson.objectives || [],
  });

  return slides;
}

export function LessonViewer({
  courseId,
  lesson,
  axisTitle,
  hasPrevAxis = false,
  hasNextAxis = false,
  onNextAxis,
  onPrevAxis,
  isCompleted = false,
  onToggleComplete,
  onNext,
  onPrev,
  hasPrev = false,
  hasNext = false,
  isTeacher = false,
}: LessonViewerProps) {
  const { t, isRTL } = useTranslation();

  // Mode: "slider" (interactive slides) or "reader" (continuous text)
  const [viewMode, setViewMode] = useState<"slider" | "reader">("slider");
  const [currentSlideIndex, setCurrentSlideIndex] = useState(0);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Re-generate slides when lesson or axisTitle changes
  const slides = useMemo(() => {
    return buildSlides(lesson, axisTitle, t);
  }, [lesson, axisTitle, t]);

  // Reset current slide when lesson changes
  useEffect(() => {
    setCurrentSlideIndex(0);
  }, [lesson.id]);

  // Slide navigation handlers
  const totalSlides = slides.length;
  const currentSlide = slides[currentSlideIndex] || slides[0];

  const handleNextSlide = useCallback(() => {
    if (currentSlideIndex < totalSlides - 1) {
      setCurrentSlideIndex((prev) => prev + 1);
    } else if (hasNext && onNext) {
      onNext();
    }
  }, [currentSlideIndex, totalSlides, hasNext, onNext]);

  const handlePrevSlide = useCallback(() => {
    if (currentSlideIndex > 0) {
      setCurrentSlideIndex((prev) => prev - 1);
    } else if (hasPrev && onPrev) {
      onPrev();
    }
  }, [currentSlideIndex, hasPrev, onPrev]);

  // Keyboard navigation for presentation slides
  useEffect(() => {
    if (viewMode !== "slider") return;

    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore if user is inside an input or textarea
      if (
        document.activeElement?.tagName === "INPUT" ||
        document.activeElement?.tagName === "TEXTAREA"
      ) {
        return;
      }

      if (e.key === "Escape" && isFullscreen) {
        setIsFullscreen(false);
      } else if (e.key === "ArrowRight") {
        if (isRTL) {
          handlePrevSlide();
        } else {
          handleNextSlide();
        }
      } else if (e.key === "ArrowLeft") {
        if (isRTL) {
          handleNextSlide();
        } else {
          handlePrevSlide();
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [viewMode, isRTL, isFullscreen, handleNextSlide, handlePrevSlide]);

  const progressPercent = Math.round(((currentSlideIndex + 1) / totalSlides) * 100);

  return (
    <article
      className={`bg-slate-950 text-slate-200 transition-all ${
        isFullscreen
          ? "fixed inset-0 z-50 p-4 sm:p-8 flex flex-col justify-between overflow-y-auto bg-slate-950"
          : "max-w-5xl mx-auto py-6 px-4 sm:px-6 lg:px-8 min-h-screen"
      }`}
    >
      {/* Top Bar: Navigable Axis, View Mode Switcher, and Tools */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-4 mb-6">
        {/* Navigable Axis Breadcrumb */}
        <div className="flex items-center gap-2.5 flex-wrap">
          {axisTitle ? (
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-semibold shadow-sm">
              <Compass className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
              <span className="truncate max-w-[280px] sm:max-w-[400px]">
                {axisTitle}
              </span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 text-xs text-slate-400 font-mono">
              <span className="text-slate-500">
                {t("courses.orderPrefix")}
                {lesson.order + 1}
              </span>
            </div>
          )}

          {/* Quick Axis Navigation Arrows */}
          {(hasPrevAxis || hasNextAxis) && (
            <div className="flex items-center gap-1 bg-slate-900 border border-slate-800 rounded-xl p-0.5 text-xs">
              {hasPrevAxis && onPrevAxis && (
                <button
                  type="button"
                  onClick={onPrevAxis}
                  className="px-2 py-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition flex items-center gap-1 text-[11px]"
                  title={t("courses.prevAxis", "المحور السابق")}
                >
                  <ChevronLeft className={`w-3.5 h-3.5 ${isRTL ? "rotate-180" : ""}`} />
                  <span className="hidden md:inline">{t("courses.prevAxis", "المحور السابق")}</span>
                </button>
              )}
              {hasNextAxis && onNextAxis && (
                <button
                  type="button"
                  onClick={onNextAxis}
                  className="px-2 py-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition flex items-center gap-1 text-[11px]"
                  title={t("courses.nextAxis", "المحور التالي")}
                >
                  <span className="hidden md:inline">{t("courses.nextAxis", "المحور التالي")}</span>
                  <ChevronRight className={`w-3.5 h-3.5 ${isRTL ? "rotate-180" : ""}`} />
                </button>
              )}
            </div>
          )}

          <span className="text-slate-600 hidden sm:inline">•</span>

          <span className="inline-flex items-center gap-1 text-xs text-slate-400 font-mono">
            <Clock className="w-3.5 h-3.5 text-indigo-400" />
            {lesson.estimated_minutes} {t("courses.readingTime")}
          </span>
        </div>

        {/* View Switcher & Action Buttons */}
        <div className="flex items-center gap-2 self-end sm:self-auto">
          {/* Slider vs Reader Toggle */}
          <div className="flex items-center bg-slate-900 border border-slate-800 rounded-xl p-1 shadow-inner">
            <button
              type="button"
              onClick={() => setViewMode("slider")}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold transition ${
                viewMode === "slider"
                  ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              <span>{t("courses.sliderMode", "عرض الشرائح")}</span>
            </button>
            <button
              type="button"
              onClick={() => setViewMode("reader")}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold transition ${
                viewMode === "reader"
                  ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <FileText className="w-3.5 h-3.5" />
              <span>{t("courses.readerMode", "قراءة مستمرة")}</span>
            </button>
          </div>

          {/* Fullscreen Button */}
          {viewMode === "slider" && (
            <button
              type="button"
              onClick={() => setIsFullscreen(!isFullscreen)}
              className="p-1.5 rounded-xl border border-slate-800 bg-slate-900/60 text-slate-400 hover:text-white hover:bg-slate-800 transition"
              title={isFullscreen ? t("courses.exitFullscreen") : t("courses.fullscreen")}
            >
              {isFullscreen ? (
                <Minimize2 className="w-4 h-4" />
              ) : (
                <Maximize2 className="w-4 h-4" />
              )}
            </button>
          )}

          {isTeacher && (
            <Link
              href={`/courses/${courseId}/edit?section=${lesson.id}`}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-slate-800 bg-slate-900/60 text-xs font-medium text-slate-300 hover:text-white hover:bg-slate-800 transition"
            >
              <Edit3 className="w-3.5 h-3.5 text-indigo-400" />
              <span className="hidden md:inline">{t("courses.editCourse", "تعديل")}</span>
            </Link>
          )}

          {onToggleComplete && (
            <button
              type="button"
              onClick={onToggleComplete}
              className={`inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold transition ${
                isCompleted
                  ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                  : "bg-slate-900 border border-slate-800 text-slate-300 hover:bg-slate-800 hover:text-white"
              }`}
            >
              <CheckCircle2
                className={`w-3.5 h-3.5 ${
                  isCompleted ? "text-emerald-400" : "text-slate-500"
                }`}
              />
              <span className="hidden sm:inline">
                {isCompleted
                  ? t("courses.statusPublished", "مكتملة")
                  : t("courses.markCompleted", "تحديد كمكتمل")}
              </span>
            </button>
          )}
        </div>
      </div>

      {/* VIEW MODE 1: INTERACTIVE SLIDER DECK */}
      {viewMode === "slider" ? (
        <div className="flex-1 flex flex-col justify-between space-y-6">
          {/* Slider Progress Bar & Step Counter */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
              <span className="flex items-center gap-2 font-semibold text-slate-300">
                <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 text-[11px] font-bold">
                  {currentSlideIndex + 1}
                </span>
                <span>
                  {t("courses.slide", "شريحة")} {currentSlideIndex + 1} {t("courses.of", "من")} {totalSlides}
                </span>
              </span>
              <span className="text-indigo-400 font-bold">{progressPercent}%</span>
            </div>

            <div className="w-full h-1.5 bg-slate-900 rounded-full overflow-hidden border border-slate-800">
              <div
                className="h-full bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 transition-all duration-300 rounded-full"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          </div>

          {/* Current Slide Display Card */}
          <div className="rounded-3xl border border-slate-800/90 bg-gradient-to-b from-slate-900/90 via-slate-900/60 to-slate-950/90 backdrop-blur-xl shadow-2xl p-6 sm:p-10 flex flex-col justify-between min-h-[480px] relative overflow-hidden transition-all">
            {/* Background Glow */}
            <div className="absolute top-0 right-0 w-80 h-80 bg-indigo-500/5 rounded-full blur-3xl pointer-events-none" />
            <div className="absolute bottom-0 left-0 w-80 h-80 bg-purple-500/5 rounded-full blur-3xl pointer-events-none" />

            {/* Slide Header */}
            <div className="border-b border-slate-800/60 pb-5 mb-6">
              <div className="flex items-center justify-between gap-4 mb-2">
                <span className="inline-flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider px-3 py-1 rounded-full bg-indigo-500/15 text-indigo-300 border border-indigo-500/30">
                  {currentSlide.type === "intro" ? (
                    <>
                      <Sparkles className="w-3 h-3 text-indigo-400" />
                      <span>{t("courses.startSlides", "المقدمة والمنطلقات")}</span>
                    </>
                  ) : currentSlide.type === "summary" ? (
                    <>
                      <Award className="w-3 h-3 text-emerald-400" />
                      <span>{t("courses.keyTakeaways", "الخلاصة والمكتسبات")}</span>
                    </>
                  ) : (
                    <>
                      <Layers className="w-3 h-3 text-purple-400" />
                      <span>{t("courses.slideDeck", "المحور والدرس التفاعلي")}</span>
                    </>
                  )}
                </span>

                <AudioGenerationButton
                  sectionId={lesson.id}
                  sectionTitle={currentSlide.title}
                />
              </div>

              <h2 className="text-xl sm:text-2xl lg:text-3xl font-extrabold text-white tracking-tight leading-snug">
                {currentSlide.title}
              </h2>
            </div>

            {/* Slide Body Content */}
            <div className="flex-1 py-2 overflow-y-auto max-h-[58vh] pr-1 custom-scrollbar">
              {/* Slide Type A: Intro */}
              {currentSlide.type === "intro" && (
                <div className="space-y-6">
                  {currentSlide.summaryText && (
                    <div
                      className={`p-5 rounded-2xl bg-indigo-950/30 border border-indigo-500/30 shadow-md ${
                        isRTL ? "border-r-4 pr-5 pl-4" : "border-l-4 pl-5 pr-4"
                      }`}
                    >
                      <div className="flex items-center gap-2 text-indigo-400 text-xs font-bold uppercase tracking-wider mb-2">
                        <Bookmark className="w-4 h-4" />
                        <span>{t("courses.overview", "Aperçu de la leçon")}</span>
                      </div>
                      <p className="text-sm sm:text-base text-indigo-100 font-medium italic leading-relaxed">
                        « {currentSlide.summaryText} »
                      </p>
                    </div>
                  )}

                  {currentSlide.objectives && currentSlide.objectives.length > 0 && (
                    <div className="bg-emerald-950/20 border border-emerald-500/30 rounded-2xl p-5 backdrop-blur-sm">
                      <div className="flex items-center gap-2 text-emerald-300 text-xs font-bold uppercase tracking-wider mb-3">
                        <Target className="w-4 h-4 text-emerald-400" />
                        <span>{t("courses.learningObjectives", "الأهداف التعليمية")}</span>
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        {currentSlide.objectives.map((obj, idx) => (
                          <div
                            key={idx}
                            className="p-3 rounded-xl bg-slate-900/60 border border-emerald-500/20 flex items-start gap-2.5 text-xs sm:text-sm text-emerald-200/90 leading-relaxed"
                          >
                            <span className="w-4 h-4 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 flex items-center justify-center text-[10px] font-bold shrink-0 mt-0.5">
                              ✓
                            </span>
                            <span>{renderInlineContent(obj)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Slide Type B: Content */}
              {currentSlide.type === "content" && (
                <div className="space-y-4">
                  {currentSlide.content ? (
                    <MarkdownRenderer content={currentSlide.content} isRTL={isRTL} />
                  ) : (
                    <div className="p-8 text-center text-slate-500 text-sm italic">
                      {t("courses.noStructuredContent", "محتوى غير متوفر")}
                    </div>
                  )}
                </div>
              )}

              {/* Slide Type C: Summary */}
              {currentSlide.type === "summary" && (
                <div className="space-y-6">
                  <div className="rounded-2xl border border-emerald-500/30 bg-emerald-950/20 p-6">
                    <div className="flex items-center gap-3 text-emerald-300 text-sm font-bold mb-3">
                      <Award className="w-5 h-5 text-emerald-400" />
                      <span>{t("courses.allSlidesCompleted", "تم استعراض كافة محاور هذا الدرس بنجاح!")}</span>
                    </div>
                    <p className="text-xs sm:text-sm text-emerald-100/90 leading-relaxed mb-4">
                      {currentSlide.summaryText}
                    </p>

                    {currentSlide.objectives && currentSlide.objectives.length > 0 && (
                      <div className="border-t border-emerald-500/20 pt-3">
                        <div className="text-xs font-bold text-emerald-400 uppercase tracking-wider mb-2">
                          {t("courses.learningObjectives", "الأهداف المستوفاة")}
                        </div>
                        <ul className="space-y-1.5 text-xs text-emerald-200">
                          {currentSlide.objectives.map((obj, i) => (
                            <li key={i} className="flex items-center gap-2">
                              <span className="text-emerald-400">✓</span>
                              <span>{obj}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>

                  <div className="flex flex-wrap items-center justify-center gap-3 pt-4">
                    {onToggleComplete && !isCompleted && (
                      <button
                        type="button"
                        onClick={onToggleComplete}
                        className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs shadow-lg shadow-emerald-900/50 flex items-center gap-2 transition"
                      >
                        <CheckCircle2 className="w-4 h-4" />
                        <span>{t("courses.markCompleted", "تحديد كمكتمل")}</span>
                      </button>
                    )}

                    {hasNext && onNext && (
                      <button
                        type="button"
                        onClick={onNext}
                        className="px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs shadow-lg shadow-indigo-900/50 flex items-center gap-2 transition"
                      >
                        <span>{t("courses.nextLesson", "الدرس التالي")}</span>
                        <ChevronRight className={`w-4 h-4 ${isRTL ? "rotate-180" : ""}`} />
                      </button>
                    )}

                    {hasNextAxis && onNextAxis && !hasNext && (
                      <button
                        type="button"
                        onClick={onNextAxis}
                        className="px-6 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-semibold text-xs shadow-lg shadow-purple-900/50 flex items-center gap-2 transition"
                      >
                        <span>{t("courses.nextAxis", "المحور التالي")}</span>
                        <ChevronRight className={`w-4 h-4 ${isRTL ? "rotate-180" : ""}`} />
                      </button>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Slide Navigation Controls */}
            <div className="border-t border-slate-800/60 pt-4 mt-6 flex flex-col sm:flex-row items-center justify-between gap-4">
              {/* Prev Slide Button */}
              <button
                type="button"
                onClick={handlePrevSlide}
                disabled={currentSlideIndex === 0 && !hasPrev}
                className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition ${
                  currentSlideIndex > 0 || hasPrev
                    ? "text-slate-300 bg-slate-900 border border-slate-800 hover:bg-slate-800 hover:text-white"
                    : "text-slate-600 bg-slate-950 border border-slate-900 opacity-40 cursor-not-allowed"
                }`}
              >
                <ChevronLeft className={`w-4 h-4 ${isRTL ? "rotate-180" : ""}`} />
                <span>
                  {currentSlideIndex === 0
                    ? t("courses.prevLesson", "الدرس السابق")
                    : t("courses.prevSlide", "الشريحة السابقة")}
                </span>
              </button>

              {/* Step Dots Indicators */}
              <div className="flex items-center gap-1.5 overflow-x-auto max-w-[260px] sm:max-w-md py-1 px-2">
                {slides.map((s, idx) => (
                  <button
                    key={s.id}
                    type="button"
                    onClick={() => setCurrentSlideIndex(idx)}
                    className={`h-2 rounded-full transition-all duration-300 ${
                      idx === currentSlideIndex
                        ? "w-7 bg-gradient-to-r from-indigo-500 to-purple-500 shadow-sm shadow-indigo-500/50"
                        : "w-2 bg-slate-800 hover:bg-slate-700"
                    }`}
                    title={`${t("courses.slide")} ${idx + 1}: ${s.title}`}
                  />
                ))}
              </div>

              {/* Next Slide Button */}
              <button
                type="button"
                onClick={handleNextSlide}
                className="flex items-center gap-2 px-5 py-2 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 shadow-md shadow-indigo-950 transition"
              >
                <span>
                  {currentSlideIndex === totalSlides - 1
                    ? hasNext
                      ? t("courses.nextLesson", "الدرس التالي")
                      : t("courses.completeAndContinue", "إنهاء")
                    : t("courses.nextSlide", "الشريحة التالية")}
                </span>
                <ChevronRight className={`w-4 h-4 ${isRTL ? "rotate-180" : ""}`} />
              </button>
            </div>
          </div>
        </div>
      ) : (
        /* VIEW MODE 2: CONTINUOUS READER */
        <div className="space-y-8">
          {/* Lesson Title & Audio Action */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <h1 className="text-2xl lg:text-3xl font-extrabold text-white tracking-tight leading-tight">
              {lesson.title}
            </h1>
            <AudioGenerationButton
              sectionId={lesson.id}
              sectionTitle={lesson.title}
            />
          </div>

          {/* Pedagogical Objectives Box */}
          {lesson.objectives && lesson.objectives.length > 0 && (
            <div className="bg-emerald-950/20 border border-emerald-500/30 rounded-2xl p-5 backdrop-blur-sm">
              <div className="flex items-center gap-2 text-emerald-300 text-xs font-bold uppercase tracking-wider mb-3">
                <Target className="w-4 h-4 text-emerald-400" />
                <span>{t("courses.learningObjectives")}</span>
              </div>
              <ul className="space-y-2">
                {lesson.objectives.map((obj, idx) => (
                  <li
                    key={idx}
                    className="text-xs sm:text-sm text-emerald-200/90 flex items-start gap-2.5 leading-relaxed"
                  >
                    <span className="text-emerald-400 font-bold shrink-0">•</span>
                    <span>{renderInlineContent(obj)}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Lesson Summary Callout */}
          {lesson.summary && (
            <div
              className={`p-4 rounded-2xl bg-indigo-950/30 border border-indigo-500/30 shadow-md ${
                isRTL ? "border-r-4 pr-5 pl-4" : "border-l-4 pl-5 pr-4"
              }`}
            >
              <div className="flex items-center gap-2 text-indigo-400 text-xs font-bold uppercase tracking-wider mb-1.5">
                <Bookmark className="w-3.5 h-3.5" />
                <span>{t("courses.overview", "Aperçu synthétique")}</span>
              </div>
              <p className="text-xs sm:text-sm text-indigo-200/95 font-medium italic leading-relaxed">
                « {lesson.summary} »
              </p>
            </div>
          )}

          {/* Rich Markdown Lesson Content Body */}
          <div className="mb-12">
            {lesson.content ? (
              <MarkdownRenderer content={lesson.content} isRTL={isRTL} />
            ) : (
              <div className="rounded-2xl border border-dashed border-slate-800 p-12 text-center text-sm text-slate-500 italic">
                <FileText className="w-8 h-8 text-slate-600 mx-auto mb-2" />
                <p>{t("courses.noStructuredContent")}</p>
              </div>
            )}
          </div>

          {/* Navigation Footer */}
          <div className="border-t border-slate-800 pt-6 flex items-center justify-between gap-4">
            <button
              type="button"
              onClick={onPrev}
              disabled={!hasPrev}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold transition ${
                hasPrev
                  ? "text-slate-300 bg-slate-900 border border-slate-800 hover:bg-slate-800 hover:text-white"
                  : "text-slate-600 bg-slate-950 border border-slate-900 cursor-not-allowed opacity-50"
              }`}
            >
              <ChevronLeft className={`w-4 h-4 ${isRTL ? "rotate-180" : ""}`} />
              <span>{t("courses.prevLesson", "Leçon précédente")}</span>
            </button>

            <button
              type="button"
              onClick={onNext}
              disabled={!hasNext}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-semibold transition shadow-md ${
                hasNext
                  ? "text-white bg-indigo-600 hover:bg-indigo-500 shadow-indigo-950"
                  : "text-slate-600 bg-slate-950 border border-slate-900 cursor-not-allowed opacity-50"
              }`}
            >
              <span>{t("courses.nextLesson", "Leçon suivante")}</span>
              <ChevronRight className={`w-4 h-4 ${isRTL ? "rotate-180" : ""}`} />
            </button>
          </div>
        </div>
      )}
    </article>
  );
}
