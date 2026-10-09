"use client";

import React from "react";
import Link from "next/link";
import {
  Clock,
  Target,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Edit3,
  Bookmark,
  Share2,
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
          <span className="text-slate-500">{t("courses.orderPrefix")}{lesson.order + 1}</span>
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
                {isCompleted ? t("courses.statusPublished", "Terminée") : t("courses.markCompleted", "Marquer comme terminée")}
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
                <span>{obj}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Lesson Summary if available */}
      {lesson.summary && (
        <div className="bg-indigo-950/20 border-l-4 border-indigo-500 p-4 rounded-r-2xl mb-8">
          <p className="text-xs sm:text-sm text-indigo-200/90 font-medium italic leading-relaxed">
            « {lesson.summary} »
          </p>
        </div>
      )}

      {/* Lesson Content Body */}
      <div className="prose prose-invert max-w-none text-slate-300 leading-relaxed space-y-4 mb-12">
        {lesson.content ? (
          lesson.content.split("\n\n").map((paragraph, pIdx) => {
            if (paragraph.startsWith("# ")) {
              return (
                <h2 key={pIdx} className="text-xl font-bold text-white pt-4 border-b border-slate-800 pb-2">
                  {paragraph.replace(/^#\s+/, "")}
                </h2>
              );
            }
            if (paragraph.startsWith("## ")) {
              return (
                <h3 key={pIdx} className="text-lg font-bold text-slate-100 pt-3">
                  {paragraph.replace(/^##\s+/, "")}
                </h3>
              );
            }
            if (paragraph.startsWith("- ") || paragraph.startsWith("* ")) {
              return (
                <ul key={pIdx} className="list-disc pl-5 space-y-1.5 text-slate-300">
                  {paragraph.split("\n").map((item, iIdx) => (
                    <li key={iIdx} className="text-sm">
                      {item.replace(/^[-*]\s+/, "")}
                    </li>
                  ))}
                </ul>
              );
            }
            return (
              <p key={pIdx} className="text-sm lg:text-base leading-relaxed text-slate-300">
                {paragraph}
              </p>
            );
          })
        ) : (
          <div className="text-center py-12 text-sm text-slate-500 italic">
            {t("courses.noStructuredContent")}
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
