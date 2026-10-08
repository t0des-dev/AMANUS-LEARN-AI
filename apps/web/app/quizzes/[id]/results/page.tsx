"use client";

import React, { useState, useEffect, useCallback, use, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { ChevronRight, AlertCircle, Loader2 } from "lucide-react";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { useAuth } from "@/components/auth/AuthProvider";
import { quizService } from "@/services/quizService";
import { Quiz, QuizAttempt } from "@/types/quiz";
import { QuizResult } from "@/features/quiz/QuizResult";

interface QuizResultsPageProps {
  params: Promise<{ id: string }>;
}

function QuizResultsContent({ quizId }: { quizId: string }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const attemptIdParam = searchParams.get("attempt_id");

  const { token } = useAuth();
  const [quiz, setQuiz] = useState<Quiz | null>(null);
  const [attempt, setAttempt] = useState<QuizAttempt | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadResults = useCallback(async () => {
    if (!token) return;
    setIsLoading(true);
    setError(null);

    try {
      // 1. Fetch quiz details
      const quizData = await quizService.getQuiz(token, quizId);
      setQuiz(quizData);

      // 2. Fetch attempts
      const resultsData = await quizService.getResults(token, quizId);
      const attempts = resultsData.attempts || [];

      if (attempts.length === 0) {
        setError("Aucune tentative enregistrée pour ce quiz.");
        return;
      }

      // Pick specific attempt by ID or latest
      let targetAttempt = attempts[0];
      if (attemptIdParam) {
        const found = attempts.find((a: QuizAttempt) => a.id === attemptIdParam);
        if (found) targetAttempt = found;
      }

      setAttempt(targetAttempt);
    } catch (err: any) {
      setError(err.message || "Impossible de charger les résultats.");
    } finally {
      setIsLoading(false);
    }
  }, [token, quizId, attemptIdParam]);

  useEffect(() => {
    loadResults();
  }, [loadResults]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950">
        <div className="flex flex-col items-center text-slate-500">
          <Loader2 className="h-8 w-8 animate-spin text-indigo-600 mb-3" />
          <p className="text-sm">Calcul du score et analyse des réponses...</p>
        </div>
      </div>
    );
  }

  if (error || !attempt) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950 p-4">
        <div className="max-w-md w-full bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 p-8 text-center">
          <AlertCircle className="h-10 w-10 text-rose-500 mx-auto mb-3" />
          <h2 className="text-lg font-bold text-slate-900 dark:text-white mb-2">
            Résultats non disponibles
          </h2>
          <p className="text-sm text-slate-600 dark:text-slate-400 mb-6">
            {error || "Tentative introuvable."}
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

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 py-10 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto space-y-6">
        {/* Breadcrumb */}
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-500">
          <Link href="/quizzes" className="hover:text-indigo-600">
            Quiz
          </Link>
          <ChevronRight className="h-3.5 w-3.5" />
          <Link href={`/quizzes/${quizId}`} className="hover:text-indigo-600 truncate max-w-xs">
            {quiz?.title || "Détails"}
          </Link>
          <ChevronRight className="h-3.5 w-3.5" />
          <span className="text-slate-900 dark:text-white">Résultats</span>
        </div>

        {/* Results Component */}
        <QuizResult
          attempt={attempt}
          quiz={quiz}
          onRetry={() => router.push(`/quizzes/${quizId}/play`)}
        />
      </div>
    </div>
  );
}

export default function QuizResultsPage({ params }: QuizResultsPageProps) {
  const unwrappedParams = use(params);
  return (
    <ProtectedRoute>
      <Suspense
        fallback={
          <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950">
            <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
          </div>
        }
      >
        <QuizResultsContent quizId={unwrappedParams.id} />
      </Suspense>
    </ProtectedRoute>
  );
}
