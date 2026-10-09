"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  HelpCircle,
  PlusCircle,
  Sparkles,
  Filter,
  Layers,
  BookOpen,
  Award,
  AlertCircle,
  Loader2,
  FileText,
} from "lucide-react";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { useAuth } from "@/components/auth/AuthProvider";
import { useOrganization } from "@/components/organization/OrganizationContext";
import { useTranslation } from "@/lib/i18n/LanguageContext";
import { quizService } from "@/services/quizService";
import { courseService } from "@/services/courseService";
import { documentService } from "@/services/documentService";
import { Quiz, QuizType, QuizDifficulty } from "@/types/quiz";
import { CourseItem } from "@/types/course";
import { DocumentItem } from "@/types/document";
import { QuizCard } from "@/features/quiz/QuizCard";

function QuizzesPageContent() {
  const { token, user } = useAuth();
  const { currentOrg } = useOrganization();
  const { t } = useTranslation();

  const [quizzes, setQuizzes] = useState<Quiz[]>([]);
  const [courses, setCourses] = useState<CourseItem[]>([]);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [typeFilter, setTypeFilter] = useState<string>("ALL");
  const [difficultyFilter, setDifficultyFilter] = useState<string>("ALL");

  // Create Modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [isAiGenerating, setIsAiGenerating] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [newType, setNewType] = useState<QuizType>("TRAINING");
  const [newDifficulty, setNewDifficulty] = useState<QuizDifficulty>("MEDIUM");
  const [newPassingScore, setNewPassingScore] = useState<number>(70);
  const [newTimeLimit, setNewTimeLimit] = useState<number>(15);
  const [selectedCourseId, setSelectedCourseId] = useState<string>("");
  const [selectedDocId, setSelectedDocId] = useState<string>("");
  const [questionCountToGen, setQuestionCountToGen] = useState<number>(5);
  const [aiPrompt, setAiPrompt] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchQuizzes = useCallback(async () => {
    if (!token) return;
    setIsLoading(true);
    setError(null);

    try {
      const data = await quizService.listQuizzes(token, {
        organization_id: currentOrg?.id || undefined,
        quiz_type: typeFilter !== "ALL" ? (typeFilter as QuizType) : undefined,
        difficulty: difficultyFilter !== "ALL" ? (difficultyFilter as QuizDifficulty) : undefined,
      });
      setQuizzes(data);
    } catch (err: any) {
      setError(err.message || "Impossible de charger les quiz.");
    } finally {
      setIsLoading(false);
    }
  }, [token, currentOrg, typeFilter, difficultyFilter]);

  const fetchCoursesAndDocs = useCallback(async () => {
    if (!token) return;
    try {
      const [coursesData, docsData] = await Promise.all([
        courseService.list(token, { organization_id: currentOrg?.id || undefined }),
        documentService.list(token, { organization_id: currentOrg?.id || undefined }),
      ]);
      setCourses(coursesData);
      setDocuments(docsData);
    } catch {
      // Ignored for dropdowns
    }
  }, [token, currentOrg]);

  useEffect(() => {
    fetchQuizzes();
    fetchCoursesAndDocs();
  }, [fetchQuizzes, fetchCoursesAndDocs]);

  const handleCreateQuiz = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !currentOrg) return;

    setIsSubmitting(true);
    setError(null);

    try {
      // 1. Create Quiz
      const newQuiz = await quizService.createQuiz(token, {
        organization: currentOrg.id,
        course: selectedCourseId || undefined,
        title: newTitle,
        description: newDesc,
        quiz_type: newType,
        difficulty: newDifficulty,
        passing_score: newPassingScore,
        time_limit_minutes: newTimeLimit > 0 ? newTimeLimit : undefined,
      });

      // 2. If AI Generation requested, trigger generation
      if (isAiGenerating) {
        await quizService.generateQuestions(token, newQuiz.id, {
          document_id: selectedDocId || undefined,
          course_id: selectedCourseId || undefined,
          count: questionCountToGen,
          difficulty: newDifficulty,
          prompt: aiPrompt || undefined,
        });
      }

      // Reset and refresh
      setShowCreateModal(false);
      setNewTitle("");
      setNewDesc("");
      setIsAiGenerating(false);
      setSelectedCourseId("");
      setSelectedDocId("");
      setAiPrompt("");
      await fetchQuizzes();
    } catch (err: any) {
      setError(err.message || "Erreur lors de la création du quiz.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 py-10 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-bold uppercase tracking-wider text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-950/60 px-2.5 py-1 rounded-md border border-indigo-100 dark:border-indigo-900">
                Moteur QCM • SPRINT 08
              </span>
            </div>
            <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
              {t("quizzes.title")}
            </h1>
            <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
              {t("quizzes.subtitle")}
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => {
                setIsAiGenerating(true);
                setShowCreateModal(true);
              }}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white shadow-sm transition"
            >
              <Sparkles className="h-4 w-4" />
              {t("quizzes.generateQuiz")}
            </button>
            <button
              onClick={() => {
                setIsAiGenerating(false);
                setShowCreateModal(true);
              }}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-850 shadow-sm transition"
            >
              <PlusCircle className="h-4 w-4" />
              {t("courses.createBtn")}
            </button>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="p-4 rounded-xl border border-rose-200 bg-rose-50 dark:bg-rose-950/40 dark:border-rose-900 text-rose-800 dark:text-rose-200 flex items-center gap-3">
            <AlertCircle className="h-5 w-5 shrink-0 text-rose-600 dark:text-rose-400" />
            <p className="text-sm">{error}</p>
          </div>
        )}

        {/* Filter Bar */}
        <div className="flex flex-wrap items-center justify-between gap-4 p-4 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 uppercase">
              <Filter className="h-3.5 w-3.5" />
              <span>Modes :</span>
            </div>
            {["ALL", "TRAINING", "EXAM", "REVISION"].map((tMode) => (
              <button
                key={tMode}
                onClick={() => setTypeFilter(tMode)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                  typeFilter === tMode
                    ? "bg-indigo-600 text-white"
                    : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200"
                }`}
              >
                {tMode === "ALL"
                  ? t("common.filter")
                  : tMode === "TRAINING"
                  ? "Entraînement"
                  : tMode === "EXAM"
                  ? "Examen"
                  : "Révision"}
              </button>
            ))}
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 uppercase">
              <span>{t("courses.level")} :</span>
            </div>
            {["ALL", "EASY", "MEDIUM", "HARD"].map((d) => (
              <button
                key={d}
                onClick={() => setDifficultyFilter(d)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                  difficultyFilter === d
                    ? "bg-slate-900 text-white dark:bg-white dark:text-slate-900"
                    : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200"
                }`}
              >
                {d === "ALL" ? t("common.filter") : d === "EASY" ? t("courses.levelBeginner") : d === "MEDIUM" ? t("courses.levelIntermediate") : t("courses.levelAdvanced")}
              </button>
            ))}
          </div>
        </div>

        {/* Quiz Catalog */}
        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-20 text-slate-500">
            <Loader2 className="h-8 w-8 animate-spin text-indigo-600 mb-3" />
            <p className="text-sm">{t("common.loading")}</p>
          </div>
        ) : quizzes.length === 0 ? (
          <div className="text-center py-20 bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 p-8 shadow-sm">
            <HelpCircle className="h-12 w-12 text-slate-400 mx-auto mb-4" />
            <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-1">
              {t("quizzes.noQuizzes")}
            </h3>
            <p className="text-sm text-slate-600 dark:text-slate-400 max-w-sm mx-auto mb-6">
              {t("quizzes.noQuizzesDesc")}
            </p>
            <button
              onClick={() => {
                setIsAiGenerating(true);
                setShowCreateModal(true);
              }}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl font-semibold text-sm bg-indigo-600 text-white hover:bg-indigo-500 shadow-sm transition"
            >
              <Sparkles className="h-4 w-4" />
              Générer un quiz IA maintenant
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {quizzes.map((quiz) => (
              <QuizCard key={quiz.id} quiz={quiz} />
            ))}
          </div>
        )}
      </div>

      {/* Create / Generate Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 backdrop-blur-sm p-4">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl max-w-xl w-full p-6 sm:p-8 shadow-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6 pb-4 border-b border-slate-100 dark:border-slate-800">
              <div className="flex items-center gap-2">
                {isAiGenerating ? (
                  <Sparkles className="h-5 w-5 text-indigo-600" />
                ) : (
                  <PlusCircle className="h-5 w-5 text-indigo-600" />
                )}
                <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                  {isAiGenerating ? "Générer un QCM avec l'IA" : "Nouveau Quiz"}
                </h3>
              </div>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateQuiz} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase text-slate-700 dark:text-slate-300 mb-1">
                  Titre du quiz *
                </label>
                <input
                  type="text"
                  required
                  placeholder="Ex : Examen Final - Algorithmique"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase text-slate-700 dark:text-slate-300 mb-1">
                  Description
                </label>
                <textarea
                  rows={2}
                  placeholder="Objectifs et consignes de l'évaluation..."
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold uppercase text-slate-700 dark:text-slate-300 mb-1">
                    Mode
                  </label>
                  <select
                    value={newType}
                    onChange={(e) => setNewType(e.target.value as QuizType)}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value="TRAINING">Entraînement</option>
                    <option value="EXAM">Examen</option>
                    <option value="REVISION">Révision</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold uppercase text-slate-700 dark:text-slate-300 mb-1">
                    Difficulté
                  </label>
                  <select
                    value={newDifficulty}
                    onChange={(e) => setNewDifficulty(e.target.value as QuizDifficulty)}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value="EASY">Facile</option>
                    <option value="MEDIUM">Moyen</option>
                    <option value="HARD">Difficile</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold uppercase text-slate-700 dark:text-slate-300 mb-1">
                    Score minimum requis (%)
                  </label>
                  <input
                    type="number"
                    min="10"
                    max="100"
                    value={newPassingScore}
                    onChange={(e) => setNewPassingScore(Number(e.target.value))}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold uppercase text-slate-700 dark:text-slate-300 mb-1">
                    Durée limite (minutes)
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="180"
                    value={newTimeLimit}
                    onChange={(e) => setNewTimeLimit(Number(e.target.value))}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                  <span className="text-[11px] text-slate-400">0 = Pas de limite de temps</span>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase text-slate-700 dark:text-slate-300 mb-1">
                  Associer à un cours (optionnel)
                </label>
                <select
                  value={selectedCourseId}
                  onChange={(e) => setSelectedCourseId(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="">Aucun cours spécifique</option>
                  {courses.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.title}
                    </option>
                  ))}
                </select>
              </div>

              {/* AI Generation specific fields */}
              {isAiGenerating && (
                <div className="pt-4 border-t border-slate-100 dark:border-slate-800 space-y-4">
                  <div className="p-3 bg-indigo-50/70 dark:bg-indigo-950/40 rounded-xl border border-indigo-100 dark:border-indigo-900 text-xs text-indigo-900 dark:text-indigo-200">
                    L&apos;IA analysera le contenu documentaire pour formuler des questions avec 4 choix, 1 bonne réponse, justification pédagogique et source.
                  </div>

                  <div>
                    <label className="block text-xs font-semibold uppercase text-slate-700 dark:text-slate-300 mb-1">
                      Document source (optionnel)
                    </label>
                    <select
                      value={selectedDocId}
                      onChange={(e) => setSelectedDocId(e.target.value)}
                      className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    >
                      <option value="">Tous les documents de l&apos;organisation</option>
                      {documents.map((d) => (
                        <option key={d.id} value={d.id}>
                          {d.title}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold uppercase text-slate-700 dark:text-slate-300 mb-1">
                      Nombre de questions à générer
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="20"
                      value={questionCountToGen}
                      onChange={(e) => setQuestionCountToGen(Number(e.target.value))}
                      className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                </div>
              )}

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 text-sm font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl"
                >
                  Annuler
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="inline-flex items-center gap-2 px-5 py-2.5 text-sm font-semibold bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl shadow-sm disabled:opacity-50"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Création en cours...
                    </>
                  ) : isAiGenerating ? (
                    <>
                      <Sparkles className="h-4 w-4" />
                      Générer le quiz
                    </>
                  ) : (
                    "Créer le quiz"
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

export default function QuizzesPage() {
  return (
    <ProtectedRoute>
      <QuizzesPageContent />
    </ProtectedRoute>
  );
}
