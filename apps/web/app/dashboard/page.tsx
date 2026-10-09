"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  GraduationCap,
  BookOpen,
  Sparkles,
  MessageSquare,
  Loader2,
  RefreshCw,
  PlusCircle,
} from "lucide-react";
import { ProtectedRoute } from "../../components/auth/ProtectedRoute";
import { useAuth } from "../../components/auth/AuthProvider";
import { useTranslation } from "../../lib/i18n/LanguageContext";
import { learningService } from "../../services/learningService";
import { StudentDashboardData } from "../../types/learning";
import { ContinueLearningCard } from "../../components/learning/ContinueLearningCard";
import { LearningStatsGrid } from "../../components/learning/LearningStatsGrid";
import { WeakTopicsList } from "../../components/learning/WeakTopicsList";
import { RecentActivityList } from "../../components/learning/RecentActivityList";
import { RecommendedRevisionList } from "../../components/learning/RecommendedRevisionList";

function StudentDashboardContent() {
  const { user, token } = useAuth();
  const { t } = useTranslation();
  const [data, setData] = useState<StudentDashboardData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchDashboard = useCallback(async () => {
    if (!token) return;
    try {
      setIsLoading(true);
      setErrorMsg(null);
      const res = await learningService.getDashboard(token);
      setData(res);
    } catch (err: any) {
      setErrorMsg(err.message || t("common.error"));
    } finally {
      setIsLoading(false);
    }
  }, [token, t]);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  if (isLoading) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8 flex flex-col items-center justify-center text-slate-400">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-500 mb-3" />
        <p className="text-sm">{t("dashboard.loading")}</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8 space-y-8">
      {/* Header with learner greeting */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <GraduationCap className="w-7 h-7 text-indigo-400" />
            <h1 className="text-2xl font-bold tracking-tight text-white">
              {t("dashboard.title")}
            </h1>
          </div>
          <p className="mt-1 text-sm text-slate-400">
            {t("dashboard.greeting")}{" "}
            <span className="text-white font-medium">{user?.first_name || "Apprenant"}</span> !{" "}
            {t("dashboard.welcomeSub")}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchDashboard}
            className="flex items-center gap-2 rounded-xl border border-slate-800 bg-slate-900/60 px-3.5 py-2 text-xs font-medium text-slate-300 hover:text-white hover:bg-slate-800 transition"
            title={t("common.loading")}
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>{t("common.filter")}</span>
          </button>
          <Link
            href="/courses"
            className="flex items-center gap-1.5 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white hover:bg-indigo-500 transition shadow-md shadow-indigo-950"
          >
            <PlusCircle className="w-3.5 h-3.5" />
            <span>{t("courses.createBtn")}</span>
          </Link>
        </div>
      </div>

      {errorMsg && (
        <div className="rounded-xl border border-rose-500/30 bg-rose-950/20 p-4 text-xs text-rose-300">
          {errorMsg}
        </div>
      )}

      {/* 1. Continue Learning Card */}
      <ContinueLearningCard item={data?.continue_learning || null} />

      {/* 2. Global Learning Statistics (Calculated from Real Data) */}
      {data && <LearningStatsGrid stats={data.stats} />}

      {/* 3. Main Dashboard Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Weak Topics & AI Revision Suggestions */}
        <div className="space-y-6">
          <WeakTopicsList topics={data?.weak_topics || []} />
          <RecommendedRevisionList recommendations={data?.recommended_revision || []} />
        </div>

        {/* Right Column: Recent Activity & Quick Hub Links */}
        <div className="space-y-6">
          <RecentActivityList activities={data?.recent_activity || []} />

          {/* Quick learning actions card */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5 backdrop-blur-sm">
            <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-indigo-400" />
              <span>{t("home.capBadge")}</span>
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <Link
                href="/courses"
                className="p-3.5 rounded-xl border border-slate-800 bg-slate-950/60 hover:border-indigo-500/50 hover:bg-slate-900 transition flex flex-col items-center text-center group"
              >
                <BookOpen className="w-5 h-5 text-indigo-400 mb-2 group-hover:scale-110 transition" />
                <span className="text-xs font-semibold text-white">{t("nav.courses")}</span>
                <span className="text-[10px] text-slate-500 mt-0.5">{t("courses.outline")}</span>
              </Link>
              <Link
                href="/quizzes"
                className="p-3.5 rounded-xl border border-slate-800 bg-slate-950/60 hover:border-violet-500/50 hover:bg-slate-900 transition flex flex-col items-center text-center group"
              >
                <Sparkles className="w-5 h-5 text-violet-400 mb-2 group-hover:scale-110 transition" />
                <span className="text-xs font-semibold text-white">{t("nav.quizzes")}</span>
                <span className="text-[10px] text-slate-500 mt-0.5">{t("quizzes.subtitle")}</span>
              </Link>
              <Link
                href="/chat"
                className="p-3.5 rounded-xl border border-slate-800 bg-slate-950/60 hover:border-sky-500/50 hover:bg-slate-900 transition flex flex-col items-center text-center group"
              >
                <MessageSquare className="w-5 h-5 text-sky-400 mb-2 group-hover:scale-110 transition" />
                <span className="text-xs font-semibold text-white">{t("nav.aiTutor")}</span>
                <span className="text-[10px] text-slate-500 mt-0.5">{t("chat.subtitle")}</span>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <ProtectedRoute>
      <StudentDashboardContent />
    </ProtectedRoute>
  );
}
