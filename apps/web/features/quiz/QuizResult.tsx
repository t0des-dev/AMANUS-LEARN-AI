"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Award,
  CheckCircle2,
  XCircle,
  Clock,
  RotateCcw,
  BookOpen,
  ChevronDown,
  ChevronUp,
  Sparkles,
  ArrowRight,
} from "lucide-react";
import { Quiz, QuizAttempt } from "../../types/quiz";
import { QuestionCard } from "./QuestionCard";

interface QuizResultProps {
  attempt: QuizAttempt;
  quiz?: Quiz | null;
  onRetry?: () => void;
  className?: string;
}

export function QuizResult({
  attempt,
  quiz,
  onRetry,
  className = "",
}: QuizResultProps) {
  const [showDetailedReview, setShowDetailedReview] = useState(true);

  const isPassed = attempt.is_passed;
  const scorePercent = Math.round(attempt.score);
  const correctCount = attempt.correct_answers;
  const totalCount = attempt.total_questions;
  const wrongCount = totalCount - correctCount;

  // Format time spent (seconds to mm:ss)
  const formatTimeSpent = (seconds: number | null) => {
    if (!seconds) return "Non mesuré";
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    if (mins === 0) return `${secs} sec`;
    return `${mins} min ${secs} sec`;
  };

  return (
    <div className={`space-y-8 ${className}`}>
      {/* Hero Score Banner */}
      <div
        className={`relative overflow-hidden rounded-3xl p-8 sm:p-10 border shadow-sm text-center ${
          isPassed
            ? "bg-gradient-to-b from-emerald-500/10 via-emerald-500/5 to-transparent border-emerald-500/30"
            : "bg-gradient-to-b from-rose-500/10 via-rose-500/5 to-transparent border-rose-500/30"
        }`}
      >
        <div className="inline-flex items-center justify-center p-3.5 rounded-2xl mb-4 bg-white dark:bg-slate-900 shadow-md">
          {isPassed ? (
            <CheckCircle2 className="h-10 w-10 text-emerald-500" />
          ) : (
            <XCircle className="h-10 w-10 text-rose-500" />
          )}
        </div>

        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white mb-2">
          {isPassed ? "Félicitations, vous avez réussi !" : "Quiz non validé, continuez vos efforts !"}
        </h1>

        <p className="text-slate-600 dark:text-slate-400 text-sm sm:text-base max-w-lg mx-auto mb-6">
          {isPassed
            ? `Vous avez obtenu le score requis pour valider ce module (${attempt.quiz_passing_score}% nécessaire).`
            : `Le score minimum requis était de ${attempt.quiz_passing_score}%. Réessayez pour consolider vos acquis.`}
        </p>

        {/* Score Ring / Big Numbers */}
        <div className="flex items-center justify-center gap-3 mb-8">
          <span
            className={`text-5xl sm:text-6xl font-black tracking-tight ${
              isPassed ? "text-emerald-600 dark:text-emerald-400" : "text-rose-600 dark:text-rose-400"
            }`}
          >
            {scorePercent}%
          </span>
        </div>

        {/* Quick Stats Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 max-w-2xl mx-auto">
          <div className="bg-white dark:bg-slate-900/80 rounded-2xl border border-slate-200/80 dark:border-slate-800 p-4">
            <div className="flex items-center justify-center gap-1.5 text-xs text-slate-500 dark:text-slate-400 mb-1">
              <CheckCircle2 className="h-4 w-4 text-emerald-500" />
              <span>Correctes</span>
            </div>
            <div className="text-xl font-bold text-slate-900 dark:text-white">
              {correctCount} / {totalCount}
            </div>
          </div>

          <div className="bg-white dark:bg-slate-900/80 rounded-2xl border border-slate-200/80 dark:border-slate-800 p-4">
            <div className="flex items-center justify-center gap-1.5 text-xs text-slate-500 dark:text-slate-400 mb-1">
              <XCircle className="h-4 w-4 text-rose-500" />
              <span>Erreurs</span>
            </div>
            <div className="text-xl font-bold text-slate-900 dark:text-white">
              {wrongCount}
            </div>
          </div>

          <div className="bg-white dark:bg-slate-900/80 rounded-2xl border border-slate-200/80 dark:border-slate-800 p-4">
            <div className="flex items-center justify-center gap-1.5 text-xs text-slate-500 dark:text-slate-400 mb-1">
              <Clock className="h-4 w-4 text-indigo-500" />
              <span>Temps</span>
            </div>
            <div className="text-xl font-bold text-slate-900 dark:text-white">
              {formatTimeSpent(attempt.time_spent_seconds)}
            </div>
          </div>

          <div className="bg-white dark:bg-slate-900/80 rounded-2xl border border-slate-200/80 dark:border-slate-800 p-4">
            <div className="flex items-center justify-center gap-1.5 text-xs text-slate-500 dark:text-slate-400 mb-1">
              <Award className="h-4 w-4 text-amber-500" />
              <span>Objectif</span>
            </div>
            <div className="text-xl font-bold text-slate-900 dark:text-white">
              {attempt.quiz_passing_score}%
            </div>
          </div>
        </div>

        {/* Call to Actions */}
        <div className="flex flex-wrap items-center justify-center gap-3 mt-8">
          {onRetry && (
            <button
              type="button"
              onClick={onRetry}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl font-semibold text-sm bg-indigo-600 text-white hover:bg-indigo-500 shadow-sm transition"
            >
              <RotateCcw className="h-4 w-4" />
              Recommencer le quiz
            </button>
          )}

          <Link
            href="/quizzes"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl font-semibold text-sm bg-slate-100 text-slate-700 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700 transition"
          >
            Tous les quiz
          </Link>

          {quiz?.course && (
            <Link
              href={`/courses/${quiz.course}`}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl font-semibold text-sm border border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-850 transition"
            >
              <BookOpen className="h-4 w-4" />
              Retour au cours
            </Link>
          )}
        </div>
      </div>

      {/* Review Section Toggle */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <span>Correction & Explications pédagogiques</span>
            <span className="text-xs font-normal text-slate-500">
              ({attempt.results_breakdown.length} questions)
            </span>
          </h2>
          <button
            type="button"
            onClick={() => setShowDetailedReview(!showDetailedReview)}
            className="inline-flex items-center gap-1 text-sm font-semibold text-indigo-600 dark:text-indigo-400 hover:underline"
          >
            {showDetailedReview ? (
              <>
                <span>Masquer les détails</span>
                <ChevronUp className="h-4 w-4" />
              </>
            ) : (
              <>
                <span>Afficher les détails</span>
                <ChevronDown className="h-4 w-4" />
              </>
            )}
          </button>
        </div>

        {/* Questions Breakdown list */}
        {showDetailedReview && (
          <div className="space-y-6">
            {attempt.results_breakdown.map((item: any, idx: number) => {
              // Construct a question object matching QuizQuestion format for QuestionCard
              const fullQuestion = quiz?.questions?.find((q: any) => q.id === item.question_id);

              return (
                <div
                  key={item.question_id}
                  className={`rounded-2xl border p-6 bg-white dark:bg-slate-900 ${
                    item.is_correct
                      ? "border-emerald-200 dark:border-emerald-900/60"
                      : "border-rose-200 dark:border-rose-900/60"
                  }`}
                >
                  <div className="flex items-center justify-between gap-3 mb-4">
                    <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                      Question {idx + 1}
                    </span>
                    <span
                      className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold ${
                        item.is_correct
                          ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300"
                          : "bg-rose-50 text-rose-700 dark:bg-rose-950/50 dark:text-rose-300"
                      }`}
                    >
                      {item.is_correct ? (
                        <>
                          <CheckCircle2 className="h-3.5 w-3.5" />
                          Correct (+{item.points_earned} pt)
                        </>
                      ) : (
                        <>
                          <XCircle className="h-3.5 w-3.5" />
                          Erreur (0 pt)
                        </>
                      )}
                    </span>
                  </div>

                  <h3 className="text-base font-semibold text-slate-900 dark:text-white mb-4">
                    {item.question_text}
                  </h3>

                  {/* Answers breakdown */}
                  {fullQuestion && (
                    <div className="space-y-2 mb-4">
                      {fullQuestion.answers.map((ans: any, ansIdx: number) => {
                        const isStudentChoice = item.selected_answer_id === ans.id;
                        const isRightAnswer = ans.is_correct ?? (item.correct_answer_id === ans.id);
                        const label = ["A", "B", "C", "D"][ansIdx] || `${ansIdx + 1}`;

                        return (
                          <div
                            key={ans.id}
                            className={`flex items-start gap-3 p-3 rounded-xl border text-sm ${
                              isRightAnswer
                                ? "bg-emerald-50/70 border-emerald-400 text-emerald-950 dark:bg-emerald-950/40 dark:border-emerald-700 dark:text-emerald-200 font-medium"
                                : isStudentChoice && !isRightAnswer
                                ? "bg-rose-50/70 border-rose-400 text-rose-950 dark:bg-rose-950/40 dark:border-rose-700 dark:text-rose-200 line-through"
                                : "bg-slate-50/50 border-slate-200 dark:bg-slate-800/40 dark:border-slate-800 text-slate-600 dark:text-slate-400"
                            }`}
                          >
                            <span className="font-bold text-xs uppercase px-2 py-0.5 rounded bg-white dark:bg-slate-800 border shrink-0">
                              {label}
                            </span>
                            <span className="flex-1">{ans.text}</span>
                            {isRightAnswer && (
                              <span className="text-xs font-bold text-emerald-700 dark:text-emerald-300">
                                Bonne réponse
                              </span>
                            )}
                            {isStudentChoice && !isRightAnswer && (
                              <span className="text-xs font-bold text-rose-700 dark:text-rose-300">
                                Votre choix
                              </span>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}

                  {/* Pedagogical Explanation & Source */}
                  {(item.explanation || fullQuestion?.explanation) && (
                    <div className="rounded-xl bg-slate-50 dark:bg-slate-850 p-4 border border-slate-200/80 dark:border-slate-800 text-xs sm:text-sm text-slate-700 dark:text-slate-300 space-y-1.5">
                      <div className="font-semibold text-indigo-600 dark:text-indigo-400 flex items-center gap-1.5">
                        <Sparkles className="h-3.5 w-3.5" />
                        <span>Explication pédagogique</span>
                      </div>
                      <p>{item.explanation || fullQuestion?.explanation}</p>
                      {fullQuestion?.source && (
                        <div className="text-slate-500 pt-1 text-xs">
                          Source : {fullQuestion.source}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
