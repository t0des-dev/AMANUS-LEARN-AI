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
} from "lucide-react";
import { ProtectedRoute } from "../../../components/auth/ProtectedRoute";
import { useAuth } from "../../../components/auth/AuthProvider";
import { courseService } from "../../../services/courseService";
import { CourseItem } from "../../../types/course";
import { CourseOutline } from "../../../features/course/CourseOutline";
import { useTranslation } from "../../../lib/i18n/LanguageContext";

function CourseDetailPageContent() {
  const params = useParams();
  const courseId = params?.id as string;
  const router = useRouter();
  const { token, user } = useAuth();
  const { t, isRTL } = useTranslation();

  const [course, setCourse] = useState<CourseItem | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);

  const fetchCourse = useCallback(async () => {
    if (!token || !courseId) return;
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
    } catch (err: any) {
      alert(err.message || t("common.error"));
    } finally {
      setIsGenerating(false);
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
