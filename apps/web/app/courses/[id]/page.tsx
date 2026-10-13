"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  GraduationCap,
  PlayCircle,
  Edit,
  Clock,
  Layers,
  Sparkles,
  AlertCircle,
  Share2,
  Download,
  FileText,
  Radio,
  BookOpen,
} from "lucide-react";
import { ProtectedRoute } from "../../../components/auth/ProtectedRoute";
import { useAuth } from "../../../components/auth/AuthProvider";
import { courseService } from "../../../services/courseService";
import { podcastService } from "../../../services/podcastService";
import { flashcardService } from "../../../services/flashcardService";
import { CourseItem } from "../../../types/course";
import { CourseOutline } from "../../../features/course/CourseOutline";
import { CitationViewerDrawer } from "../../../components/citation/CitationViewerDrawer";
import { useTranslation } from "../../../lib/i18n/LanguageContext";
import { useToast } from "../../../components/toast/ToastProvider";

function CourseDetailPageContent() {
  const params = useParams();
  const courseId = params?.id as string;
  const router = useRouter();
  const toast = useToast();
  const { token, user } = useAuth();
  const { t, isRTL } = useTranslation();

  const [course, setCourse] = useState<CourseItem | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);

  const fetchCourse = useCallback(async () => {
    if (!token || !courseId || courseId === "null" || courseId === "undefined") {
      setIsLoading(false);
      return;
    }
    setIsLoading(true);
    setError(null);

    try {
      const data = await courseService.get(token, courseId);
      setCourse(data);
    } catch (err: any) {
      setError(err.message || t("common.error"));
    } finally {
      setIsLoading(false);
    }
  }, [token, courseId, t]);

  useEffect(() => {
    fetchCourse();
  }, [fetchCourse]);

  const handleGenerateAI = async () => {
    if (!token || !course) return;
    setIsGenerating(true);
    try {
      const updated = await courseService.generate(token, course.id);
      setCourse(updated);
      toast.success("Cours régénéré avec succès par l'IA.");
    } catch (err: any) {
      toast.error(err.message || t("common.error"), "Génération IA");
    } finally {
      setIsGenerating(false);
    }
  };

  const [isExporting, setIsExporting] = useState<string | null>(null);

  const handleExportDocx = async () => {
    if (!token || !course) return;
    setIsExporting("docx");
    try {
      const blob = await courseService.exportDocx(token, course.id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${course.title.replace(/\s+/g, "_")}.docx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      toast.success("Document Word téléchargé avec succès.");
    } catch (err: any) {
      toast.error(err.message || "Erreur lors de l'export Word", "Export Word");
    } finally {
      setIsExporting(null);
    }
  };

  const handleExportMarkdown = async () => {
    if (!token || !course) return;
    setIsExporting("md");
    try {
      const text = await courseService.exportMarkdown(token, course.id);
      const blob = new Blob([text], { type: "text/markdown;charset=utf-8" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${course.title.replace(/\s+/g, "_")}.md`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      toast.success("Document Markdown téléchargé avec succès.");
    } catch (err: any) {
      toast.error(err.message || "Erreur lors de l'export Markdown", "Export Markdown");
    } finally {
      setIsExporting(null);
    }
  };

  const [isGeneratingPodcast, setIsGeneratingPodcast] = useState(false);
  const [isOpeningFlashcards, setIsOpeningFlashcards] = useState(false);
  const [isCitationDrawerOpen, setIsCitationDrawerOpen] = useState(false);

  const handlePodcastClick = async () => {
    if (!token || !course) return;
    setIsGeneratingPodcast(true);
    try {
      const existing = await podcastService.listPodcasts(token, { course_id: course.id });
      if (existing.length > 0) {
        router.push(`/podcasts/${existing[0].id}`);
        return;
      }
      const episode = await podcastService.generatePodcast(token, {
        course_id: course.id,
        document_id: course.document || undefined,
        language: "fr",
      });
      router.push(`/podcasts/${episode.id}`);
    } catch (err: any) {
      toast.error(err.message || "Erreur lors de la génération du podcast.", "Podcast");
    } finally {
      setIsGeneratingPodcast(false);
    }
  };

  const handleFlashcardsClick = async () => {
    if (!token || !course) return;
    setIsOpeningFlashcards(true);
    try {
      const decks = await flashcardService.listDecks(token, { course_id: course.id });
      if (decks.length > 0) {
        router.push(`/flashcards/${decks[0].id}`);
        return;
      }
      const newDeck = await flashcardService.createDeck(token, {
        organization_id: course.organization,
        course_id: course.id,
        title: `Flashcards : ${course.title}`,
        description: `Paquet de révision espacée SM-2 pour le cours ${course.title}`,
        cards: [
          {
            front: `Quel est le concept clé de ${course.title} ?`,
            back: `Les fondements méthodologiques et les principes théoriques présentés dans le cours.`,
            hint: `Revoir le chapitre 1`,
            source_citation: `[1]`,
          },
          {
            front: `Comment appliquer les compétences de ce cours en pratique ?`,
            back: `En suivant le protocole structuré étape par étape et en validant les critères de succès.`,
            hint: `Revoir les cas pratiques`,
            source_citation: `[2]`,
          },
        ],
      });
      router.push(`/flashcards/${newDeck.id}`);
    } catch (err: any) {
      toast.error(err.message || "Erreur lors de l'accès aux flashcards.", "Flashcards");
    } finally {
      setIsOpeningFlashcards(false);
    }
  };

  const getLevelLabel = (level: string) => {
    switch (level) {
      case "BEGINNER":
        return t("courses.levelBeginner");
      case "INTERMEDIATE":
        return t("courses.levelIntermediate");
      case "ADVANCED":
        return t("courses.levelAdvanced");
      default:
        return level;
    }
  };

  if (isLoading) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-12 space-y-6">
        <div className="h-48 bg-slate-900/60 border border-slate-800 rounded-3xl animate-pulse" />
        <div className="h-96 bg-slate-900/60 border border-slate-800 rounded-3xl animate-pulse" />
      </div>
    );
  }

  if (error || !course) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12 text-center">
        <div className="p-4 bg-rose-950/20 border border-rose-500/30 rounded-2xl text-xs text-rose-300 max-w-md mx-auto mb-4">
          {error || t("courses.noCourses")}
        </div>
        <Link
          href="/courses"
          className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 transition"
        >
          {t("courses.backToCourses")}
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Back button */}
      <div>
        <Link
          href="/courses"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className={`w-3.5 h-3.5 ${isRTL ? "rotate-180" : ""}`} />
          <span>{t("courses.allCourses")}</span>
        </Link>
      </div>

      {/* Course Hero Banner */}
      <div className="rounded-3xl border border-slate-800 bg-slate-900/60 p-6 sm:p-8 shadow-xl backdrop-blur-sm">
        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
          <div className="space-y-3.5 max-w-3xl">
            <div className="flex flex-wrap items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 font-mono">
                {getLevelLabel(course.level)}
              </span>
              <span
                className={`px-2.5 py-0.5 rounded-full text-[11px] font-semibold ${
                  course.status === "PUBLISHED"
                    ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                    : "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                }`}
              >
                {course.status === "PUBLISHED" ? t("courses.statusPublished") : t("courses.statusDraft")}
              </span>
              <span className="text-xs text-slate-500 font-mono">
                {t("courses.language")}: {course.language.toUpperCase()}
              </span>
            </div>

            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight leading-tight">
              {course.title}
            </h1>

            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
              {course.description || t("courses.noDesc")}
            </p>

            <div className="flex items-center gap-4 text-xs text-slate-400 pt-2 font-mono">
              <div className="flex items-center gap-1.5 text-indigo-400">
                <Layers className="w-4 h-4" />
                <span>{course.sections_count} {t("courses.chaptersCount")}</span>
              </div>
              <span>•</span>
              <div className="flex items-center gap-1.5 text-purple-400">
                <Clock className="w-4 h-4" />
                <span>~{course.total_estimated_minutes}m {t("courses.totalDuration")}</span>
              </div>
              {course.creator_name && (
                <>
                  <span>•</span>
                  <span>{t("courses.createdBy")} {course.creator_name}</span>
                </>
              )}
            </div>
          </div>

          {/* Action CTAs */}
          <div className="flex flex-col sm:flex-row lg:flex-col gap-3 shrink-0 w-full lg:w-auto">
            <Link
              href={`/courses/${course.id}/learn`}
              className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-xl text-xs sm:text-sm transition shadow-lg shadow-indigo-950 active:scale-95"
            >
              <PlayCircle className="w-4 h-4" />
              <span>{t("courses.startCourse")}</span>
            </Link>

            <Link
              href={`/courses/${course.id}/edit`}
              className="inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-200 font-semibold rounded-xl text-xs sm:text-sm transition"
            >
              <Edit className="w-4 h-4" />
              <span>{t("courses.editCourseTitle")}</span>
            </Link>

            {/* Mode Podcast & Flashcards */}
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={handlePodcastClick}
                disabled={isGeneratingPodcast}
                className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-2.5 bg-purple-950/40 hover:bg-purple-950/70 text-purple-300 border border-purple-500/30 font-semibold rounded-xl text-xs transition active:scale-95 shadow-md shadow-purple-950/30"
                title="Écouter le podcast pédagogique à deux voix (Camille & Alex)"
              >
                <Radio className={`w-3.5 h-3.5 text-purple-400 ${isGeneratingPodcast ? "animate-pulse" : ""}`} />
                <span>{isGeneratingPodcast ? "Génération..." : "Podcast (2 Voix)"}</span>
              </button>

              <button
                type="button"
                onClick={handleFlashcardsClick}
                disabled={isOpeningFlashcards}
                className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-2.5 bg-amber-950/40 hover:bg-amber-950/70 text-amber-300 border border-amber-500/30 font-semibold rounded-xl text-xs transition active:scale-95 shadow-md shadow-amber-950/30"
                title="S'entraîner avec les flashcards et répétition espacée (SM-2)"
              >
                <Layers className="w-3.5 h-3.5 text-amber-400" />
                <span>{isOpeningFlashcards ? "Chargement..." : "Flashcards SM-2"}</span>
              </button>
            </div>

            {course.document && (
              <button
                type="button"
                onClick={() => setIsCitationDrawerOpen(true)}
                className="inline-flex items-center justify-center gap-1.5 px-3 py-2 bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 font-medium rounded-xl text-xs transition"
                title="Inspecter les extraits originaux du document et citations"
              >
                <BookOpen className="w-3.5 h-3.5 text-indigo-400" />
                <span>Sources & Citations</span>
              </button>
            )}

            {course.document && (
              <button
                type="button"
                onClick={handleGenerateAI}
                disabled={isGenerating}
                className="inline-flex items-center justify-center gap-1.5 px-4 py-2 border border-indigo-500/30 bg-indigo-950/40 hover:bg-indigo-950/60 text-indigo-300 font-medium rounded-xl text-xs transition"
              >
                <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                <span>{isGenerating ? t("courses.regeneratingAI") : t("courses.regenerateAI")}</span>
              </button>
            )}

            {/* Export Buttons */}
            <div className="flex items-center gap-2 pt-1">
              <button
                type="button"
                onClick={handleExportDocx}
                disabled={isExporting !== null}
                className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-2 bg-slate-800/80 hover:bg-slate-700/80 text-slate-200 border border-slate-700/60 font-medium rounded-xl text-xs transition active:scale-95"
                title="Exporter le cours au format Word (.docx)"
              >
                <Download className="w-3.5 h-3.5 text-blue-400" />
                <span>{isExporting === "docx" ? "Export..." : "Word"}</span>
              </button>
              <button
                type="button"
                onClick={handleExportMarkdown}
                disabled={isExporting !== null}
                className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-2 bg-slate-800/80 hover:bg-slate-700/80 text-slate-200 border border-slate-700/60 font-medium rounded-xl text-xs transition active:scale-95"
                title="Exporter le cours au format Markdown (.md)"
              >
                <FileText className="w-3.5 h-3.5 text-emerald-400" />
                <span>{isExporting === "md" ? "Export..." : "Markdown"}</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Course Outline Section */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <GraduationCap className="w-5 h-5 text-indigo-400" />
            <span>{t("courses.programSummary")}</span>
          </h2>
          <span className="text-xs text-slate-500 font-mono">
            {t("courses.hierarchyLabel")}
          </span>
        </div>

        <CourseOutline course={course} isTeacher={true} />
      </div>

      {/* Interactive Citation Drawer */}
      {course.document && (
        <CitationViewerDrawer
          isOpen={isCitationDrawerOpen}
          onClose={() => setIsCitationDrawerOpen(false)}
          documentId={course.document}
          documentTitle={course.title}
        />
      )}
    </div>
  );
}

export default function CourseDetailPage() {
  return (
    <ProtectedRoute>
      <CourseDetailPageContent />
    </ProtectedRoute>
  );
}
