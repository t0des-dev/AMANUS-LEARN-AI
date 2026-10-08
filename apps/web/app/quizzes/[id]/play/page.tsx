"use client";

import React, { useState, useEffect, useCallback, use, useRef } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  ChevronLeft,
  ChevronRight,
  Send,
  AlertCircle,
  Loader2,
  CheckCircle2,
  HelpCircle,
  X,
} from "lucide-react";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { useAuth } from "@/components/auth/AuthProvider";
import { quizService } from "@/services/quizService";
import { Quiz, QuizAttempt, QuizQuestion } from "@/types/quiz";
import { QuizTimer } from "@/features/quiz/QuizTimer";
import { QuizProgress } from "@/features/quiz/QuizProgress";
import { QuestionCard } from "@/features/quiz/QuestionCard";

interface QuizPlayPageProps {
  params: Promise<{ id: string }>;
}

function QuizPlayContent({ quizId }: { quizId: string }) {
  const router = useRouter();
  const { token } = useAuth();

  const [quiz, setQuiz] = useState<Quiz | null>(null);
  const [attempt, setAttempt] = useState<QuizAttempt | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Player state
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showConfirmSubmit, setShowConfirmSubmit] = useState(false);

  const isSubmittingRef = useRef(false);
  isSubmittingRef.current = isSubmitting;

  // Initialize Quiz & Attempt
  const initQuizSession = useCallback(async () => {
    if (!token) return;
    setIsLoading(true);
    setError(null);

    try {
      // 1. Fetch quiz details with questions
      const quizData = await quizService.getQuiz(token, quizId);
      setQuiz(quizData);

      // 2. Start attempt
      const attemptData = await quizService.startQuiz(token, quizId);
      setAttempt(attemptData);
    } catch (err: any) {
      setError(err.message || "Impossible de démarrer la session de quiz.");
    } finally {
      setIsLoading(false);
    }
  }, [token, quizId]);

  useEffect(() => {
    initQuizSession();
  }, [initQuizSession]);

  // Answer selection handler
  const handleSelectAnswer = (questionId: string, answerId: string) => {
    setSelectedAnswers((prev) => ({
      ...prev,
      [questionId]: answerId,
    }));
  };

  // Submit quiz function
  const handleSubmit = useCallback(async () => {
    if (!token || !attempt || isSubmittingRef.current) return;
    setIsSubmitting(true);
    setError(null);

    try {
      const answersPayload = Object.entries(selectedAnswers).map(
        ([question_id, selected_answer_id]) => ({
          question_id,
          selected_answer_id,
        })
      );

      const submittedAttempt = await quizService.submitQuiz(token, quizId, {
        attempt_id: attempt.id,
        answers: answersPayload,
      });

      // Redirect to results
      router.push(`/quizzes/${quizId}/results?attempt_id=${submittedAttempt.id}`);
    } catch (err: any) {
      setError(err.message || "Erreur lors de la soumission du quiz.");
      setIsSubmitting(false);
    }
  }, [token, attempt, quizId, selectedAnswers, router]);

  // Timer expired callback
  const handleTimeUp = useCallback(() => {
    handleSubmit();
  }, [handleSubmit]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950">
        <div className="flex flex-col items-center text-slate-500">
          <Loader2 className="h-8 w-8 animate-spin text-indigo-600 mb-3" />
          <p className="text-sm">Préparation du quiz et initialisation du chronomètre...</p>
        </div>
      </div>
    );
  }

  if (error || !quiz || !quiz.questions || quiz.questions.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950 p-4">
        <div className="max-w-md w-full bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 p-8 text-center">
          <AlertCircle className="h-10 w-10 text-rose-500 mx-auto mb-3" />
          <h2 className="text-lg font-bold text-slate-900 dark:text-white mb-2">
            Impossible de jouer
          </h2>
          <p className="text-sm text-slate-600 dark:text-slate-400 mb-6">
            {error || "Ce quiz ne contient aucune question pour le moment."}
          </p>
          <Link
            href={`/quizzes/${quizId}`}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold bg-indigo-600 text-white hover:bg-indigo-500 transition"
          >
            Retour au quiz
          </Link>
        </div>
      </div>
    );
  }

  const currentQuestion = quiz.questions[currentIndex];
  const totalQuestions = quiz.questions.length;
  const answeredCount = Object.keys(selectedAnswers).length;
  const unansweredCount = totalQuestions - answeredCount;

  // Build a quick map for QuizProgress pills
  const answeredMap: Record<number, boolean> = {};
  quiz.questions.forEach((q: QuizQuestion, idx: number) => {
    if (selectedAnswers[q.id]) {
      answeredMap[idx] = true;
    }
  });

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 py-6 sm:py-10 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto space-y-6">
        {/* Sticky Header with Timer & Quiz Info */}
        <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <div>
            <h1 className="text-base sm:text-lg font-bold text-slate-900 dark:text-white truncate max-w-sm">
              {quiz.title}
            </h1>
            <span className="text-xs text-slate-500">
              Mode {quiz.quiz_type} • Seuil {quiz.passing_score}%
            </span>
          </div>

          <div className="flex items-center gap-3">
            {quiz.time_limit_minutes && quiz.time_limit_minutes > 0 ? (
              <QuizTimer
                timeLimitMinutes={quiz.time_limit_minutes}
                onTimeUp={handleTimeUp}
                isPaused={isSubmitting}
              />
            ) : (
              <span className="text-xs font-semibold text-slate-500 bg-slate-100 dark:bg-slate-800 px-3 py-1.5 rounded-lg">
                Temps libre
              </span>
            )}

            <button
              type="button"
              onClick={() => {
                if (unansweredCount > 0) {
                  setShowConfirmSubmit(true);
                } else {
                  handleSubmit();
                }
              }}
              disabled={isSubmitting}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold bg-indigo-600 hover:bg-indigo-500 text-white shadow-sm disabled:opacity-50 transition"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Soumission...
                </>
              ) : (
                <>
                  <Send className="h-3.5 w-3.5" />
                  Terminer
                </>
              )}
            </button>
          </div>
        </div>

        {/* Progress Tracker */}
        <QuizProgress
          currentIndex={currentIndex}
          totalQuestions={totalQuestions}
          answeredCount={answeredCount}
          onJumpToQuestion={(idx: number) => setCurrentIndex(idx)}
          answeredMap={answeredMap}
        />

        {/* Current Question Card */}
        {currentQuestion && (
          <QuestionCard
            question={currentQuestion}
            questionIndex={currentIndex}
            totalQuestions={totalQuestions}
            selectedAnswerId={selectedAnswers[currentQuestion.id] || null}
            onSelectAnswer={(ansId: string) => handleSelectAnswer(currentQuestion.id, ansId)}
          />
        )}

        {/* Bottom Navigation Buttons */}
        <div className="flex items-center justify-between gap-4 pt-2">
          <button
            type="button"
            onClick={() => setCurrentIndex((prev) => Math.max(0, prev - 1))}
            disabled={currentIndex === 0}
            className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl text-sm font-semibold border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-850 disabled:opacity-40 transition"
          >
            <ChevronLeft className="h-4 w-4" />
            Précédente
          </button>

          {currentIndex < totalQuestions - 1 ? (
            <button
              type="button"
              onClick={() => setCurrentIndex((prev) => Math.min(totalQuestions - 1, prev + 1))}
              className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-xl text-sm font-semibold bg-indigo-600 hover:bg-indigo-500 text-white shadow-sm transition"
            >
              Suivante
              <ChevronRight className="h-4 w-4" />
            </button>
          ) : (
            <button
              type="button"
              onClick={() => {
                if (unansweredCount > 0) {
                  setShowConfirmSubmit(true);
                } else {
                  handleSubmit();
                }
              }}
              disabled={isSubmitting}
              className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-xl text-sm font-semibold bg-emerald-600 hover:bg-emerald-500 text-white shadow-sm disabled:opacity-50 transition"
            >
              <CheckCircle2 className="h-4 w-4" />
              Soumettre le quiz
            </button>
          )}
        </div>
      </div>

      {/* Confirmation Modal if Unanswered Questions */}
      {showConfirmSubmit && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 backdrop-blur-sm p-4">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl max-w-md w-full p-6 sm:p-8 shadow-2xl text-center">
            <div className="inline-flex items-center justify-center p-3 rounded-2xl bg-amber-50 text-amber-600 dark:bg-amber-950/50 mb-4">
              <AlertCircle className="h-8 w-8" />
            </div>

            <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-2">
              Questions non répondues
            </h3>

            <p className="text-sm text-slate-600 dark:text-slate-400 mb-6">
              Il vous reste <span className="font-bold text-amber-600">{unansweredCount}</span> question(s) sans réponse sur les {totalQuestions}. Voulez-vous vraiment valider votre tentative maintenant ?
            </p>

            <div className="flex items-center justify-center gap-3">
              <button
                type="button"
                onClick={() => setShowConfirmSubmit(false)}
                className="px-4 py-2.5 text-sm font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 rounded-xl"
              >
                Continuer à répondre
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowConfirmSubmit(false);
                  handleSubmit();
                }}
                disabled={isSubmitting}
                className="px-5 py-2.5 text-sm font-semibold bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl shadow-sm"
              >
                Confirmer la soumission
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function QuizPlayPage({ params }: QuizPlayPageProps) {
  const unwrappedParams = use(params);
  return (
    <ProtectedRoute>
      <QuizPlayContent quizId={unwrappedParams.id} />
    </ProtectedRoute>
  );
}
