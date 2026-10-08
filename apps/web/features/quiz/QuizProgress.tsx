"use client";

import React from "react";
import { CheckCircle2, Circle } from "lucide-react";

interface QuizProgressProps {
  currentIndex: number;
  totalQuestions: number;
  answeredCount: number;
  onJumpToQuestion?: (index: number) => void;
  answeredMap?: Record<number, boolean>;
  className?: string;
}

export function QuizProgress({
  currentIndex,
  totalQuestions,
  answeredCount,
  onJumpToQuestion,
  answeredMap = {},
  className = "",
}: QuizProgressProps) {
  const percent = totalQuestions > 0 ? Math.round((answeredCount / totalQuestions) * 100) : 0;

  return (
    <div className={`w-full bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-4 shadow-sm ${className}`}>
      <div className="flex items-center justify-between text-xs sm:text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-slate-900 dark:text-white">
            Question {currentIndex + 1}
          </span>
          <span className="text-slate-400">sur {totalQuestions}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-indigo-600 dark:text-indigo-400 font-semibold">{answeredCount}</span>
          <span className="text-slate-400">répondues ({percent}%)</span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2 mb-3 overflow-hidden">
        <div
          className="bg-gradient-to-r from-indigo-500 to-violet-500 h-2 rounded-full transition-all duration-300 ease-out"
          style={{ width: `${percent}%` }}
        />
      </div>

      {/* Question Selector Pills */}
      {onJumpToQuestion && totalQuestions > 0 && (
        <div className="flex flex-wrap items-center gap-1.5 pt-2 border-t border-slate-100 dark:border-slate-800">
          {Array.from({ length: totalQuestions }).map((_, idx) => {
            const isCurrent = idx === currentIndex;
            const isAnswered = answeredMap[idx] || false;

            return (
              <button
                key={idx}
                type="button"
                onClick={() => onJumpToQuestion(idx)}
                className={`relative flex items-center justify-center w-7 h-7 rounded-lg text-xs font-semibold transition-all ${
                  isCurrent
                    ? "bg-indigo-600 text-white shadow-sm ring-2 ring-indigo-400 ring-offset-1 dark:ring-offset-slate-900"
                    : isAnswered
                    ? "bg-indigo-50 text-indigo-700 hover:bg-indigo-100 dark:bg-indigo-950/50 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800"
                    : "bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-400"
                }`}
                aria-label={`Aller à la question ${idx + 1}`}
              >
                {idx + 1}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
