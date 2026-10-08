"use client";

import React from "react";
import { BookOpen, HelpCircle, Sparkles } from "lucide-react";
import { QuizQuestion } from "../../types/quiz";
import { AnswerOption } from "./AnswerOption";

interface QuestionCardProps {
  question: QuizQuestion;
  questionIndex: number;
  totalQuestions: number;
  selectedAnswerId?: string | null;
  onSelectAnswer?: (answerId: string) => void;
  reviewMode?: boolean;
  className?: string;
}

const DIFFICULTY_MAP: Record<string, { label: string; color: string }> = {
  EASY: {
    label: "Facile",
    color: "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800",
  },
  MEDIUM: {
    label: "Moyen",
    color: "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-800",
  },
  HARD: {
    label: "Difficile",
    color: "bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950/40 dark:text-rose-300 dark:border-rose-800",
  },
};

const OPTION_LABELS = ["A", "B", "C", "D"];

export function QuestionCard({
  question,
  questionIndex,
  totalQuestions,
  selectedAnswerId,
  onSelectAnswer,
  reviewMode = false,
  className = "",
}: QuestionCardProps) {
  const diffInfo = DIFFICULTY_MAP[question.difficulty] || DIFFICULTY_MAP.MEDIUM;

  return (
    <div
      className={`bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 sm:p-8 shadow-sm ${className}`}
    >
      {/* Header with badges */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4 pb-3 border-b border-slate-100 dark:border-slate-800">
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
            Question {questionIndex + 1} / {totalQuestions}
          </span>
          <span
            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${diffInfo.color}`}
          >
            {diffInfo.label}
          </span>
        </div>

        {question.source && (
          <div className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400 max-w-xs truncate">
            <BookOpen className="h-3.5 w-3.5 text-indigo-500 shrink-0" />
            <span className="truncate" title={question.source}>
              Source : {question.source}
            </span>
          </div>
        )}
      </div>

      {/* Question Prompt */}
      <h2 className="text-lg sm:text-xl font-semibold text-slate-900 dark:text-white leading-snug mb-6">
        {question.question}
      </h2>

      {/* Answer options */}
      <div className="space-y-3 mb-6">
        {question.answers.map((ans: any, idx: number) => {
          const isSelected = selectedAnswerId === ans.id;
          const label = OPTION_LABELS[idx] || `${idx + 1}`;

          return (
            <AnswerOption
              key={ans.id}
              label={label}
              text={ans.text}
              selected={isSelected}
              disabled={reviewMode}
              onClick={() => {
                if (!reviewMode && onSelectAnswer) {
                  onSelectAnswer(ans.id);
                }
              }}
              showValidation={reviewMode}
              isCorrect={ans.is_correct}
            />
          );
        })}
      </div>

      {/* Explanation panel (Review mode or if revealed) */}
      {reviewMode && question.explanation && (
        <div className="rounded-xl border border-indigo-100 bg-indigo-50/50 dark:bg-indigo-950/20 dark:border-indigo-900/60 p-4 text-sm text-slate-800 dark:text-slate-200">
          <div className="flex items-center gap-1.5 font-semibold text-indigo-700 dark:text-indigo-300 mb-1.5">
            <HelpCircle className="h-4 w-4" />
            <span>Explication pédagogique</span>
          </div>
          <p className="text-slate-600 dark:text-slate-300 leading-relaxed">
            {question.explanation}
          </p>
        </div>
      )}
    </div>
  );
}
