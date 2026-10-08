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

function CourseDetailPageContent() {
  const params = useParams();
  const courseId = params?.id as string;
  const router = useRouter();
  const { token, user } = useAuth();

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
      setError(err.message || "Impossible de charger le cours.");
    } finally {
      setIsLoading(false);
    }
  }, [token, courseId]);

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
      alert(err.message || "Échec de la génération IA.");
    } finally {
      setIsGenerating(false);
    }
  };

  if (isLoading) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-12">
        <div className="h-48 bg-gray-100 rounded-2xl animate-pulse mb-8" />
        <div className="h-96 bg-gray-100 rounded-2xl animate-pulse" />
      </div>
    );
  }

  if (error || !course) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12 text-center">
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700 max-w-md mx-auto mb-4">
          {error || "Cours introuvable."}
        </div>
        <Link
          href="/courses"
          className="text-sm font-semibold text-blue-600 hover:underline"
        >
          ← Revenir à la liste des cours
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
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-gray-500 hover:text-gray-900 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Tous les cours
        </Link>
      </div>

      {/* Course Hero Banner */}
      <div className="bg-white rounded-2xl border border-gray-200 p-6 sm:p-8 shadow-sm">
        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
          <div className="space-y-3 max-w-3xl">
            <div className="flex flex-wrap items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-50 text-blue-700 border border-blue-200">
                {course.level}
              </span>
              <span
                className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                  course.status === "PUBLISHED"
                    ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                    : "bg-amber-50 text-amber-700 border border-amber-200"
                }`}
              >
                {course.status === "PUBLISHED" ? "Publié" : "Brouillon"}
              </span>
              <span className="text-xs text-gray-400">
                Langue : {course.language.toUpperCase()}
              </span>
            </div>

            <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 tracking-tight">
              {course.title}
            </h1>

            <p className="text-sm sm:text-base text-gray-600 leading-relaxed">
              {course.description || "Aucune description fournie pour ce cours."}
            </p>

            <div className="flex items-center gap-4 text-xs text-gray-500 pt-2">
              <div className="flex items-center gap-1.5">
                <Layers className="w-4 h-4 text-blue-500" />
                <span>{course.sections_count} sections</span>
              </div>
              <span>•</span>
              <div className="flex items-center gap-1.5">
                <Clock className="w-4 h-4 text-purple-500" />
                <span>~{course.total_estimated_minutes} min au total</span>
              </div>
              {course.creator_name && (
                <>
                  <span>•</span>
                  <span>Par {course.creator_name}</span>
                </>
              )}
            </div>
          </div>

          {/* Action CTAs */}
          <div className="flex flex-col sm:flex-row lg:flex-col gap-3 shrink-0 w-full lg:w-auto">
            <Link
              href={`/courses/${course.id}/learn`}
              className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl text-sm transition-all shadow-sm"
            >
              <PlayCircle className="w-4 h-4" />
              Commencer le cours
            </Link>

            <Link
              href={`/courses/${course.id}/edit`}
              className="inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-gray-100 hover:bg-gray-200 text-gray-800 font-semibold rounded-xl text-sm transition-colors"
            >
              <Edit className="w-4 h-4" />
              Éditer le cours
            </Link>

            {course.document && (
              <button
                type="button"
                onClick={handleGenerateAI}
                disabled={isGenerating}
                className="inline-flex items-center justify-center gap-1.5 px-4 py-2 border border-indigo-200 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-medium rounded-xl text-xs transition-colors"
              >
                <Sparkles className="w-3.5 h-3.5" />
                {isGenerating ? "Génération..." : "Régénérer avec l'IA"}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Course Outline Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
            <GraduationCap className="w-5 h-5 text-blue-600" />
            Programme & Sommaire du cours
          </h2>
          <span className="text-xs text-gray-400">
            Hiérarchie : Chapitres • Sections • Leçons
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
