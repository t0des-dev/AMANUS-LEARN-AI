"use client";

import React from "react";
import Link from "next/link";
import { BookOpen, Clock, Award, Play, ChevronRight, HelpCircle } from "lucide-react";
import { Quiz } from "../../types/quiz";
import { useTranslation } from "../../lib/i18n/LanguageContext";

interface QuizCardProps {
  quiz: Quiz;
  className?: string;
}

const TYPE_CONFIG: Record<string, { key: string; label: string; badge: string }> = {
  TRAINING: {
    key: "quizzes.training",
    label: "Entraînement",
    badge: "bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/40 dark:text-blue-300 dark:border-blue-800",
  },
  EXAM: {
    key: "quizzes.exam",
    label: "Examen",
    badge: "bg-purple-50 text-purple-700 border-purple-200 dark:bg-purple-950/40 dark:text-purple-300 dark:border-purple-800",
  },
  REVISION: {
    key: "quizzes.revision",
    label: "Révision",
    badge: "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800",
  },
};

const DIFFICULTY_CONFIG: Record<string, { key: string; label: string; badge: string }> = {
  EASY: {
    key: "quizzes.easy",
    label: "Facile",
    badge: "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800",
  },
  MEDIUM: {
    key: "quizzes.medium",
    label: "Moyen",
    badge: "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-800",
  },
  HARD: {
    key: "quizzes.hard",
    label: "Difficile",
    badge: "bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950/40 dark:text-rose-300 dark:border-rose-800",
  },
};

export function QuizCard({ quiz, className = "" }: QuizCardProps) {
  const { t } = useTranslation();
  const typeInfo = TYPE_CONFIG[quiz.quiz_type] || TYPE_CONFIG.TRAINING;
  const diffInfo = DIFFICULTY_CONFIG[quiz.difficulty] || DIFFICULTY_CONFIG.MEDIUM;
  const questionCount = quiz.questions?.length ?? quiz.question_count ?? 0;

  return (
    <div
      className={`group flex flex-col justify-between bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 hover:shadow-md hover:border-slate-300 dark:hover:border-slate-700 transition-all duration-200 ${className}`}
    >
      <div>
        {/* Badges */}
        <div className="flex flex-wrap items-center gap-2 mb-3">
          <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border ${typeInfo.badge}`}>
            {t(typeInfo.key, typeInfo.label)}
          </span>
          <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border ${diffInfo.badge}`}>
            {t(diffInfo.key, diffInfo.label)}
          </span>
          {quiz.course_title && (
            <span className="flex items-center gap-1 text-xs text-slate-500 dark:text-slate-400 max-w-[150px] truncate">
              <BookOpen className="h-3 w-3 shrink-0" />
              <span className="truncate">{quiz.course_title}</span>
            </span>
          )}
        </div>

        {/* Title */}
        <Link href={`/quizzes/${quiz.id}`}>
          <h3 className="text-lg font-bold text-slate-900 dark:text-white group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors line-clamp-2 mb-2">
            {quiz.title}
          </h3>
        </Link>

        {/* Description */}
        {quiz.description && (
          <p className="text-sm text-slate-600 dark:text-slate-400 line-clamp-2 mb-4 leading-relaxed">
            {quiz.description}
          </p>
        )}
      </div>

      {/* Footer Info & Action */}
      <div className="pt-4 border-t border-slate-100 dark:border-slate-800 mt-4">
        <div className="grid grid-cols-3 gap-2 text-xs text-slate-500 dark:text-slate-400 mb-4">
          <div className="flex items-center gap-1.5">
            <HelpCircle className="h-3.5 w-3.5 text-indigo-500" />
            <span>{questionCount} questions</span>
          </div>
          <div className="flex items-center gap-1.5 justify-center">
            <Clock className="h-3.5 w-3.5 text-purple-500" />
            <span>{quiz.time_limit_minutes ? `${quiz.time_limit_minutes} min` : t("quizzes.unlimited", "Illimité")}</span>
          </div>
          <div className="flex items-center gap-1.5 justify-end">
            <Award className="h-3.5 w-3.5 text-emerald-500" />
            <span>{t("quizzes.minScore", "Min.")} {quiz.passing_score}%</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Link
            href={`/quizzes/${quiz.id}`}
            className="flex-1 inline-flex items-center justify-center gap-1.5 px-4 py-2 rounded-xl text-sm font-semibold bg-slate-100 text-slate-700 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-750 transition"
          >
            {t("quizzes.details", "Détails")}
            <ChevronRight className="h-4 w-4" />
          </Link>
          <Link
            href={`/quizzes/${quiz.id}/play`}
            className="inline-flex items-center justify-center gap-1.5 px-4 py-2 rounded-xl text-sm font-semibold bg-indigo-600 text-white hover:bg-indigo-500 shadow-sm transition"
          >
            <Play className="h-3.5 w-3.5 fill-current" />
            {t("quizzes.play", "Jouer")}
          </Link>
        </div>
      </div>
    </div>
  );
}
