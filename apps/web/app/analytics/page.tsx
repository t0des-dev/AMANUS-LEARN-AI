"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  BarChart3,
  Clock,
  CheckCircle2,
  Award,
  GraduationCap,
  Sparkles,
  Loader2,
  RefreshCw,
  BookOpen,
} from "lucide-react";
import { ProtectedRoute } from "../../components/auth/ProtectedRoute";
import { useAuth } from "../../components/auth/AuthProvider";
import { analyticsService } from "../../services/analyticsService";
import { StudentAnalyticsResponse } from "../../types/analytics";
import { ProgressChart } from "../../components/analytics/ProgressChart";
import { ScoreChart } from "../../components/analytics/ScoreChart";
import { StudyTimeChart } from "../../components/analytics/StudyTimeChart";
import { useTranslation } from "../../lib/i18n/LanguageContext";

function StudentAnalyticsContent() {
  const { t } = useTranslation();
  const { token, user } = useAuth();
  const [data, setData] = useState<StudentAnalyticsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const formatDuration = (seconds: number): string => {
    if (!seconds || seconds <= 0) return `0 ${t("dashboard.minutes")}`;
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const hUnit = t("common.hourShort");
    const mUnit = t("common.minShort");
    if (hours > 0) return `${hours}${hUnit} ${minutes}${mUnit}`;
    return `${minutes} ${t("dashboard.minutes")}`;
  };

  const fetchAnalytics = useCallback(async () => {
    if (!token) return;
    try {
      setIsLoading(true);
      setErrorMsg(null);
      const res = await analyticsService.getStudentAnalytics(token);
      setData(res);
    } catch (err: any) {
      setErrorMsg(err.message || t("analytics.errorLoading"));
    } finally {
      setIsLoading(false);
    }
  }, [token, t]);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  if (isLoading) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8 flex flex-col items-center justify-center text-slate-400">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-500 mb-3" />
        <p className="text-sm">{t("analytics.calculating")}</p>
      </div>
    );
  }

  const summary = data?.summary;

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <BarChart3 className="w-7 h-7 text-indigo-400" />
            <h1 className="text-2xl font-bold tracking-tight text-white">
              {t("analytics.studentTitle")}
            </h1>
          </div>
          <p className="mt-1 text-sm text-slate-400">
            {t("analytics.studentSubtitle")}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchAnalytics}
            className="flex items-center gap-2 rounded-xl border border-slate-800 bg-slate-900/60 px-3.5 py-2 text-xs font-medium text-slate-300 hover:text-white hover:bg-slate-800 transition"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>{t("common.refresh")}</span>
          </button>
          <Link
            href="/dashboard"
            className="flex items-center gap-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 px-3.5 py-2 text-xs font-medium text-slate-200 transition"
          >
            <BookOpen className="w-3.5 h-3.5" />
            <span>{t("nav.dashboard")}</span>
          </Link>
        </div>
      </div>

      {errorMsg && (
        <div className="rounded-xl border border-rose-500/30 bg-rose-950/20 p-4 text-xs text-rose-300">
          {errorMsg}
        </div>
      )}

      {/* KPI Cards Row */}
      {summary && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3.5">
          <div className="p-4 rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 block">
              {t("analytics.studyTimeKpi")}
            </span>
            <span className="text-lg font-bold font-mono text-white mt-1 block">
              {formatDuration(summary.total_study_time_seconds)}
            </span>
          </div>

          <div className="p-4 rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 block">
              {t("analytics.completedCoursesKpi")}
            </span>
            <span className="text-lg font-bold font-mono text-emerald-400 mt-1 block">
              {summary.completed_courses_count} / {summary.enrolled_courses_count}
            </span>
          </div>

          <div className="p-4 rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 block">
              {t("analytics.progressKpi")}
            </span>
            <span className="text-lg font-bold font-mono text-indigo-400 mt-1 block">
              {summary.overall_progress.toFixed(0)}%
            </span>
          </div>

          <div className="p-4 rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 block">
              {t("analytics.quizzesTakenKpi")}
            </span>
            <span className="text-lg font-bold font-mono text-violet-400 mt-1 block">
              {summary.total_quizzes_taken}
            </span>
          </div>

          <div className="p-4 rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 block">
              {t("dashboard.masteryScore")}
            </span>
            <span className="text-lg font-bold font-mono text-emerald-400 mt-1 block">
              {summary.success_rate.toFixed(0)}%
            </span>
          </div>

          <div className="p-4 rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 block">
              {t("analytics.averageScoreKpi")}
            </span>
            <span className="text-lg font-bold font-mono text-amber-400 mt-1 block">
              {summary.average_score !== null ? `${summary.average_score.toFixed(0)}%` : "--"}
            </span>
          </div>
        </div>
      )}

      {/* Main Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Study Time Breakdown & Progress Chart */}
        <div className="space-y-6">
          <StudyTimeChart
            totalSeconds={summary?.total_study_time_seconds || 0}
            studyTimeByDay={data?.study_time_by_day || []}
          />
          <ProgressChart
            overallProgress={summary?.overall_progress || 0}
            coursesProgress={data?.courses_progress || []}
          />
        </div>

        {/* Right Column: Score Trend & History */}
        <div className="space-y-6">
          <ScoreChart
            averageScore={summary?.average_score ?? null}
            successRate={summary?.success_rate || 0}
            scoresHistory={data?.scores_history || []}
          />
        </div>
      </div>
    </div>
  );
}

export default function AnalyticsPage() {
  return (
    <ProtectedRoute>
      <StudentAnalyticsContent />
    </ProtectedRoute>
  );
}
