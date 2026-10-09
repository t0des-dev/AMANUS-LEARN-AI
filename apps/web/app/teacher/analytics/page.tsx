"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  GraduationCap,
  Users,
  BookOpen,
  Loader2,
  RefreshCw,
  AlertCircle,
  ChevronDown,
  Layers,
  ArrowLeft,
  Sparkles,
} from "lucide-react";
import { ProtectedRoute } from "../../../components/auth/ProtectedRoute";
import { useAuth } from "../../../components/auth/AuthProvider";
import { useOrganization } from "../../../components/organization/OrganizationContext";
import { analyticsService } from "../../../services/analyticsService";
import { courseService } from "../../../services/courseService";
import {
  CourseAnalyticsResponse,
  StudentPerformanceItem,
} from "../../../types/analytics";
import { CourseItem } from "../../../types/course";
import { CourseAnalytics } from "../../../components/analytics/CourseAnalytics";
import { StudentPerformance } from "../../../components/analytics/StudentPerformance";
import { useTranslation } from "../../../lib/i18n/LanguageContext";

function TeacherAnalyticsContent() {
  const { t } = useTranslation();
  const { token, user } = useAuth();
  const { currentOrg } = useOrganization();

  const [courses, setCourses] = useState<CourseItem[]>([]);
  const [selectedCourseId, setSelectedCourseId] = useState<string>("");
  const [courseAnalytics, setCourseAnalytics] = useState<CourseAnalyticsResponse | null>(null);
  const [studentsPerf, setStudentsPerf] = useState<StudentPerformanceItem[]>([]);
  const [isLoadingCourses, setIsLoadingCourses] = useState(true);
  const [isLoadingAnalytics, setIsLoadingAnalytics] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Fetch courses taught in the organization
  const fetchCourses = useCallback(async () => {
    if (!token) return;
    try {
      setIsLoadingCourses(true);
      setErrorMsg(null);
      const list = await courseService.list(token, {
        organization_id: currentOrg?.id,
      });
      setCourses(list);
      if (list.length > 0) {
        setSelectedCourseId((prev) => (prev && list.some((c) => c.id === prev) ? prev : list[0].id));
      } else {
        setSelectedCourseId("");
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Erreur lors du chargement des cours.");
    } finally {
      setIsLoadingCourses(false);
    }
  }, [token, currentOrg?.id]);

  useEffect(() => {
    fetchCourses();
  }, [fetchCourses]);

  // Fetch analytics for selected course
  const fetchCourseData = useCallback(async () => {
    if (!token || !selectedCourseId) {
      setCourseAnalytics(null);
      setStudentsPerf([]);
      return;
    }
    try {
      setIsLoadingAnalytics(true);
      setErrorMsg(null);
      const [analyticsData, studentsData] = await Promise.all([
        analyticsService.getCourseAnalytics(token, selectedCourseId),
        analyticsService.getCourseStudentsPerformance(token, selectedCourseId),
      ]);
      setCourseAnalytics(analyticsData);
      setStudentsPerf(studentsData);
    } catch (err: any) {
      setErrorMsg(
        err.message ||
          "Accès refusé ou données indisponibles pour ce cours. Seuls les enseignants peuvent consulter ces statistiques."
      );
      setCourseAnalytics(null);
      setStudentsPerf([]);
    } finally {
      setIsLoadingAnalytics(false);
    }
  }, [token, selectedCourseId]);

  useEffect(() => {
    fetchCourseData();
  }, [fetchCourseData]);

  if (isLoadingCourses) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8 flex flex-col items-center justify-center text-slate-400">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-500 mb-3" />
        <p className="text-sm">{t("analytics.loadingCohort", "Chargement des cours de l'organisation...")}</p>
      </div>
    );
  }

  const selectedCourse = courses.find((c) => c.id === selectedCourseId);

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8 space-y-8">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <GraduationCap className="w-7 h-7 text-indigo-400" />
            <h1 className="text-2xl font-bold tracking-tight text-white">
              {t("analytics.teacherTitle", "Espace Analytics Enseignant")}
            </h1>
          </div>
          <p className="mt-1 text-sm text-slate-400">
            {t("analytics.teacherSub", "Suivi des cohortes d'étudiants, identification des chapitres problématiques et taux de réussite.")}
          </p>
        </div>

        {/* Course Selector Dropdown */}
        <div className="flex items-center gap-3">
          {courses.length > 0 && (
            <div className="relative">
              <select
                value={selectedCourseId}
                onChange={(e) => setSelectedCourseId(e.target.value)}
                className="appearance-none bg-slate-900 border border-slate-700 rounded-xl px-4 py-2 pr-9 text-xs font-semibold text-white focus:outline-none focus:border-indigo-500 cursor-pointer transition shadow-md"
              >
                {courses.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.title}
                  </option>
                ))}
              </select>
              <ChevronDown className="w-4 h-4 text-slate-400 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>
          )}

          <button
            onClick={fetchCourseData}
            disabled={!selectedCourseId || isLoadingAnalytics}
            className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:bg-slate-800 transition disabled:opacity-40"
            title={t("analytics.refreshStats", "Actualiser les statistiques")}
          >
            <RefreshCw className={`w-4 h-4 ${isLoadingAnalytics ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {errorMsg && (
        <div className="rounded-xl border border-rose-500/30 bg-rose-950/20 p-4 text-xs text-rose-300 flex items-start gap-2.5">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-400 mt-0.5" />
          <span>{errorMsg}</span>
        </div>
      )}

      {courses.length === 0 ? (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-12 text-center text-slate-400 text-sm">
          <BookOpen className="w-10 h-10 mx-auto mb-3 opacity-30 text-indigo-400" />
          <h3 className="text-base font-semibold text-white">{t("analytics.noCoursesFound", "Aucun cours trouvé")}</h3>
          <p className="mt-1 text-xs text-slate-500 max-w-md mx-auto">
            {t("analytics.noCoursesDesc", "Créez ou publiez des cours dans votre organisation pour afficher les analyses pédagogiques.")}
          </p>
          <div className="mt-6">
            <Link
              href="/courses"
              className="px-4 py-2 rounded-xl bg-indigo-600 text-white font-semibold text-xs hover:bg-indigo-500 transition"
            >
              {t("analytics.manageCourses", "Gérer les cours")}
            </Link>
          </div>
        </div>
      ) : isLoadingAnalytics ? (
        <div className="py-20 flex flex-col items-center justify-center text-slate-400">
          <Loader2 className="w-8 h-8 animate-spin text-indigo-500 mb-3" />
          <p className="text-sm">{t("analytics.aggregating", "Agrégation des statistiques de cohorte en cours...")}</p>
        </div>
      ) : courseAnalytics ? (
        <div className="space-y-8">
          {/* 1. Course Cohort Analytics & Problematic Chapters */}
          <CourseAnalytics data={courseAnalytics} />

          {/* 2. Individual Student Tracking Table */}
          <StudentPerformance students={studentsPerf} />
        </div>
      ) : null}
    </div>
  );
}

export default function TeacherAnalyticsPage() {
  return (
    <ProtectedRoute>
      <TeacherAnalyticsContent />
    </ProtectedRoute>
  );
}
