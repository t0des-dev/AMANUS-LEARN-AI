"use client";

import React, { useState, useEffect, useCallback, use } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  HelpCircle,
  Clock,
  Award,
  Play,
  RotateCcw,
  Sparkles,
  BookOpen,
  ChevronRight,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Loader2,
  Calendar,
} from "lucide-react";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { useAuth } from "@/components/auth/AuthProvider";
import { quizService } from "@/services/quizService";
import { Quiz, QuizAttempt } from "@/types/quiz";

interface QuizDetailPageProps {
  params: Promise<{ id: string }>;
}

function QuizDetailContent({ quizId }: { quizId: string }) {
  const router = useRouter();
  const { token, user } = useAuth();

  const [quiz, setQuiz] = useState<Quiz | null>(null);
  const [attempts, setAttempts] = useState<QuizAttempt[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // AI Generation on existing quiz
  const [showAiGenModal, setShowAiGenModal] = useState(false);
  const [genCount, setGenCount] = useState<number>(5);
  const [genPrompt, setGenPrompt] = useState<string>("");
  const [isGenerating, setIsGenerating] = useState(false);

  const loadData = useCallback(async () => {
    if (!token) return;
    setIsLoading(true);
    setError(null);

    try {
      const [quizData, resultsData] = await Promise.all([
        quizService.getQuiz(token, quizId),
        quizService.getResults(token, quizId).catch(() => ({ attempts: [] })),
      ]);
      setQuiz(quizData);
      setAttempts(resultsData.attempts || []);
    } catch (err: any) {
      setError(err.message || "Impossible de charger les détails du quiz.");
    } finally {
      setIsLoading(false);
    }
  }, [token, quizId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleStartQuiz = async () => {
    router.push(`/quizzes/${quizId}/play`);
  };

  const handleGenerateQuestions = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;

    setIsGenerating(true);
    try {
      await quizService.generateQuestions(token, quizId, {
        count: genCount,
        prompt: genPrompt || undefined,
      });
      setShowAiGenModal(false);
      setGenPrompt("");
      await loadData();
    } catch (err: any) {
      setError(err.message || "Erreur de génération des questions.");
    } finally {
      setIsGenerating(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950">
        <div className="flex flex-col items-center text-slate-500">
          <Loader2 className="h-8 w-8 animate-spin text-indigo-600 mb-3" />
          <p className="text-sm">Chargement du quiz...</p>
        </div>
      </div>
    );
  }

  if (error || !quiz) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950 p-4">
        <div className="max-w-md w-full bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 p-8 text-center">
          <AlertCircle className="h-10 w-10 text-rose-500 mx-auto mb-3" />
          <h2 className="text-lg font-bold text-slate-900 dark:text-white mb-2">
            Quiz indisponible
          </h2>
          <p className="text-sm text-slate-600 dark:text-slate-400 mb-6">{error || "Quiz non trouvé."}</p>
          <Link
            href="/quizzes"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold bg-indigo-600 text-white hover:bg-indigo-500 transition"
          >
            Retourner aux quiz
          </Link>
        </div>
      </div>
    );
  }

  const questionCount = quiz.questions?.length ?? quiz.question_count ?? 0;
  const lastAttempt = attempts.length > 0 ? attempts[0] : null;

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 py-10 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Breadcrumb */}
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-500">
          <Link href="/quizzes" className="hover:text-indigo-600">
            Quiz
          </Link>
          <ChevronRight className="h-3.5 w-3.5" />
          <span className="text-slate-900 dark:text-white truncate">{quiz.title}</span>
        </div>

        {/* Hero Card */}
        <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 p-8 shadow-sm">
          <div className="flex flex-wrap items-center gap-2 mb-4">
            <span className="px-3 py-1 rounded-full text-xs font-bold bg-indigo-50 text-indigo-700 border border-indigo-200 dark:bg-indigo-950/40 dark:text-indigo-300 dark:border-indigo-800">
              {quiz.quiz_type === "TRAINING"
                ? "Entraînement"
                : quiz.quiz_type === "EXAM"
                ? "Examen certifiant"
                : "Session de révision"}
            </span>
            <span className="px-3 py-1 rounded-full text-xs font-bold bg-slate-100 text-slate-700 border border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700">
              {quiz.difficulty === "EASY" ? "Facile" : quiz.difficulty === "HARD" ? "Difficile" : "Moyen"}
            </span>
            {quiz.course_title && (
              <span className="flex items-center gap-1.5 text-xs text-slate-500">
                <BookOpen className="h-3.5 w-3.5 text-indigo-500" />
                <span>Cours : {quiz.course_title}</span>
              </span>
            )}
          </div>

          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white mb-3">
            {quiz.title}
          </h1>

          {quiz.description && (
            <p className="text-slate-600 dark:text-slate-300 text-sm sm:text-base leading-relaxed mb-6">
              {quiz.description}
            </p>
          )}

          {/* Metrics summary */}
          <div className="grid grid-cols-3 gap-3 p-4 rounded-2xl bg-slate-50 dark:bg-slate-850 border border-slate-100 dark:border-slate-800 mb-8">
            <div className="text-center">
              <div className="flex items-center justify-center gap-1.5 text-xs text-slate-500 mb-1">
                <HelpCircle className="h-4 w-4 text-indigo-500" />
                <span>Questions</span>
              </div>
              <div className="text-lg font-bold text-slate-900 dark:text-white">
                {questionCount}
              </div>
            </div>

            <div className="text-center border-x border-slate-200 dark:border-slate-800">
              <div className="flex items-center justify-center gap-1.5 text-xs text-slate-500 mb-1">
                <Clock className="h-4 w-4 text-purple-500" />
                <span>Durée</span>
              </div>
              <div className="text-lg font-bold text-slate-900 dark:text-white">
                {quiz.time_limit_minutes ? `${quiz.time_limit_minutes} min` : "Libre"}
              </div>
            </div>

            <div className="text-center">
              <div className="flex items-center justify-center gap-1.5 text-xs text-slate-500 mb-1">
                <Award className="h-4 w-4 text-emerald-500" />
                <span>Score requis</span>
              </div>
              <div className="text-lg font-bold text-slate-900 dark:text-white">
                {quiz.passing_score}%
              </div>
            </div>
          </div>

          {/* Action Row */}
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={handleStartQuiz}
                disabled={questionCount === 0}
                className="inline-flex items-center gap-2 px-6 py-3 rounded-xl font-bold text-sm bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white shadow-lg shadow-indigo-500/20 disabled:opacity-50 transition"
              >
                <Play className="h-4 w-4 fill-current" />
                {lastAttempt ? "Recommencer le quiz" : "Démarrer le quiz"}
              </button>

              <button
                type="button"
                onClick={() => setShowAiGenModal(true)}
                className="inline-flex items-center gap-2 px-4 py-3 rounded-xl font-semibold text-sm bg-slate-100 hover:bg-slate-200 text-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-750 transition"
              >
                <Sparkles className="h-4 w-4 text-indigo-500" />
                Enrichir avec l&apos;IA
              </button>
            </div>

            {lastAttempt && (
              <div className="flex items-center gap-2 text-xs text-slate-500">
                <span>Dernier score :</span>
                <span
                  className={`font-bold ${
                    lastAttempt.is_passed ? "text-emerald-600" : "text-rose-600"
                  }`}
                >
                  {Math.round(lastAttempt.score)}% ({lastAttempt.is_passed ? "Validé" : "Échoué"})
                </span>
                <Link
                  href={`/quizzes/${quizId}/results?attempt_id=${lastAttempt.id}`}
                  className="text-indigo-600 hover:underline font-semibold"
                >
                  Voir résultats
                </Link>
              </div>
            )}
          </div>
        </div>

        {/* Previous Attempts Section */}
        {attempts.length > 0 && (
          <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 p-6 sm:p-8 shadow-sm">
            <h2 className="text-lg font-bold text-slate-900 dark:text-white mb-4">
              Historique des tentatives ({attempts.length})
            </h2>

            <div className="space-y-3">
              {attempts.map((att) => (
                <div
                  key={att.id}
                  className="flex items-center justify-between p-4 rounded-2xl border border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-850/50 hover:bg-slate-50 dark:hover:bg-slate-850 transition"
                >
                  <div className="flex items-center gap-3">
                    {att.is_passed ? (
                      <CheckCircle2 className="h-5 w-5 text-emerald-500 shrink-0" />
                    ) : (
                      <XCircle className="h-5 w-5 text-rose-500 shrink-0" />
                    )}
                    <div>
                      <div className="text-sm font-semibold text-slate-900 dark:text-white">
                        Score : {Math.round(att.score)}% ({att.correct_answers}/{att.total_questions} correctes)
                      </div>
                      <div className="flex items-center gap-2 text-xs text-slate-400 mt-0.5">
                        <Calendar className="h-3 w-3" />
                        <span>
                          {att.completed_at
                            ? new Date(att.completed_at).toLocaleDateString("fr-FR", {
                                day: "numeric",
                                month: "short",
                                hour: "2-digit",
                                minute: "2-digit",
                              })
                            : "En cours"}
                        </span>
                        {att.time_spent_seconds && (
                          <>
                            <span>•</span>
                            <span>{Math.round(att.time_spent_seconds / 60)} min</span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>

                  <Link
                    href={`/quizzes/${quizId}/results?attempt_id=${att.id}`}
                    className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:underline"
                  >
                    Consulter
                    <ChevronRight className="h-3.5 w-3.5" />
                  </Link>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* AI Questions Generation Modal */}
      {showAiGenModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 backdrop-blur-sm p-4">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl max-w-lg w-full p-6 sm:p-8 shadow-2xl">
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-100 dark:border-slate-800">
              <div className="flex items-center gap-2 font-bold text-slate-900 dark:text-white">
                <Sparkles className="h-5 w-5 text-indigo-600" />
                <span>Générer des questions IA</span>
              </div>
              <button
                onClick={() => setShowAiGenModal(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleGenerateQuestions} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase text-slate-700 dark:text-slate-300 mb-1">
                  Nombre de questions à ajouter
                </label>
                <input
                  type="number"
                  min="1"
                  max="15"
                  value={genCount}
                  onChange={(e) => setGenCount(Number(e.target.value))}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white text-sm"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase text-slate-700 dark:text-slate-300 mb-1">
                  Instructions thématiques (optionnel)
                </label>
                <textarea
                  rows={2}
                  placeholder="Ex : Focalise sur les définitions clés du chapitre 2..."
                  value={genPrompt}
                  onChange={(e) => setGenPrompt(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white text-sm"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-3">
                <button
                  type="button"
                  onClick={() => setShowAiGenModal(false)}
                  className="px-4 py-2 text-sm text-slate-500 hover:bg-slate-100 rounded-xl"
                >
                  Annuler
                </button>
                <button
                  type="submit"
                  disabled={isGenerating}
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold bg-indigo-600 hover:bg-indigo-500 text-white shadow-sm disabled:opacity-50"
                >
                  {isGenerating ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Génération en cours...
                    </>
                  ) : (
                    <>
                      <Sparkles className="h-4 w-4" />
                      Générer
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default function QuizDetailPage({ params }: QuizDetailPageProps) {
  const unwrappedParams = use(params);
  return (
    <ProtectedRoute>
      <QuizDetailContent quizId={unwrappedParams.id} />
    </ProtectedRoute>
  );
}
