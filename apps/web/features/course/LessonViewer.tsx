"use client";

import React, { useState } from "react";
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
  Terminal,
  FileText,
} from "lucide-react";
import { CourseSectionItem } from "../../types/course";
import { AudioGenerationButton } from "../../components/audio/AudioGenerationButton";
import { useTranslation } from "../../lib/i18n/LanguageContext";

interface LessonViewerProps {
  courseId: string;
  lesson: CourseSectionItem;
  isCompleted?: boolean;
  onToggleComplete?: () => void;
  onNext?: () => void;
  onPrev?: () => void;
  hasPrev?: boolean;
  hasNext?: boolean;
  isTeacher?: boolean;
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

  // Tokenize by citation pattern, bold, italic, code
  const tokens = text.split(/(\[\d+\]|\[Doc\s*\d+\]|\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g);

  return tokens.map((token, idx) => {
    if (!token) return null;

    // Citation [1], [2], [Doc 1]
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

    // Bold **text**
    if (token.startsWith("**") && token.endsWith("**")) {
      return (
        <strong key={idx} className="font-bold text-white tracking-wide">
          {token.slice(2, -2)}
        </strong>
      );
    }

    // Italic *text*
    if (token.startsWith("*") && token.endsWith("*") && !token.startsWith("**")) {
      return (
        <em key={idx} className="italic text-slate-200">
          {token.slice(1, -1)}
        </em>
      );
    }

    // Inline code `code`
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

  // Split content by code block boundaries or double newlines
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

        // 1. Code Block ```lang ... ```
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

        // 2. Heading 1 (# ...)
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

        // 3. Heading 2 (## ...)
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

        // 4. Heading 3 (### ...)
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

        // 5. Callouts & Blockquotes (> ...)
        if (trimmed.startsWith(">")) {
          const quoteLines = trimmed
            .split("\n")
            .map((line) => line.replace(/^>\s?/, "").trim())
            .join(" ");

          const lower = quoteLines.toLowerCase();
          const isTip = lower.includes("[!tip]") || lower.includes("conseil") || lower.includes("نصيحة") || lower.includes("أفضل ممارسة");
          const isWarning = lower.includes("[!warning]") || lower.includes("attention") || lower.includes("تحذير");
          const isImportant = lower.includes("[!important]") || lower.includes("important") || lower.includes("تنبيه مهم") || lower.includes("point clé");
          const isDef = lower.includes("définition") || lower.includes("تعريف") || lower.includes("règle");

          const cleanQuote = quoteLines
            .replace(/^\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*/i, "");

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

        // 6. Unordered Lists (- or *)
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

        // 7. Numbered Lists (1. 2. 3.)
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

        // 8. Markdown Tables (| col | col |)
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

export function LessonViewer({
  courseId,
  lesson,
  isCompleted = false,
  onToggleComplete,
  onNext,
  onPrev,
  hasPrev = false,
  hasNext = false,
  isTeacher = false,
}: LessonViewerProps) {
  const { t, isRTL } = useTranslation();

  return (
    <article className="max-w-4xl mx-auto py-8 px-6 lg:px-10 bg-slate-950 text-slate-200 min-h-screen">
      {/* Top action bar */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-6">
        <div className="flex items-center gap-3 text-xs text-slate-400 font-mono">
          <span className="flex items-center gap-1.5 text-indigo-400">
            <Clock className="w-3.5 h-3.5" />
            {lesson.estimated_minutes} {t("courses.readingTime")}
          </span>
          <span>•</span>
          <span className="text-slate-500">
            {t("courses.orderPrefix")}
            {lesson.order + 1}
          </span>
        </div>

        <div className="flex items-center gap-2">
          {isTeacher && (
            <Link
              href={`/courses/${courseId}/edit?section=${lesson.id}`}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-slate-800 bg-slate-900/60 text-xs font-medium text-slate-300 hover:text-white hover:bg-slate-800 transition"
            >
              <Edit3 className="w-3.5 h-3.5 text-indigo-400" />
              <span>{t("courses.editCourse", "Modifier cette leçon")}</span>
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
              <span>
                {isCompleted
                  ? t("courses.statusPublished", "Terminée")
                  : t("courses.markCompleted", "Marquer comme terminée")}
              </span>
            </button>
          )}
        </div>
      </div>

      {/* Lesson Title & Audio Action */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
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
        <div className="bg-emerald-950/20 border border-emerald-500/30 rounded-2xl p-5 mb-8 backdrop-blur-sm">
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
          className={`p-4 rounded-2xl mb-8 bg-indigo-950/30 border border-indigo-500/30 shadow-md ${
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
    </article>
  );
}
