"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  GraduationCap,
  BookOpen,
  Sparkles,
  Loader2,
  ChevronRight,
  Award,
  Layers,
} from "lucide-react";
import { ProtectedRoute } from "../../components/auth/ProtectedRoute";
import { useAuth } from "../../components/auth/AuthProvider";
import { learningService } from "../../services/learningService";
import { LearningPathItem, StudentDashboardData } from "../../types/learning";
import { ContinueLearningCard } from "../../components/learning/ContinueLearningCard";
import { LearningStatsGrid } from "../../components/learning/LearningStatsGrid";
import { WeakTopicsList } from "../../components/learning/WeakTopicsList";
import { RecentActivityList } from "../../components/learning/RecentActivityList";
import { RecommendedRevisionList } from "../../components/learning/RecommendedRevisionList";

function LearningHubContent() {
  const { user, token } = useAuth();
  const [dashboardData, setDashboardData] = useState<StudentDashboardData | null>(null);
  const [courses, setCourses] = useState<LearningPathItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchData = useCallback(async () => {
    if (!token) return;
    try {
      setIsLoading(true);
      const [dash, crs] = await Promise.all([
        learningService.getDashboard(token),
        learningService.listCourses(token),
      ]);
      setDashboardData(dash);
      setCourses(crs);
    } catch {
      // handled gracefully
    } finally {
      setIsLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (isLoading) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8 flex flex-col items-center justify-center text-slate-400">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-500 mb-3" />
        <p className="text-sm">Chargement de votre moteur d&apos;apprentissage...</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8 space-y-8">
      {/* Title */}
      <div>
        <div className="flex items-center gap-2">
          <GraduationCap className="w-7 h-7 text-indigo-400" />
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Espace d&apos;Apprentissage
          </h1>
        </div>
        <p className="mt-1 text-sm text-slate-400">
          Suivez votre progression continue, vos temps d&apos;étude et vos recommandations adaptatives.
        </p>
      </div>

      {/* Continue Learning */}
      <ContinueLearningCard item={dashboardData?.continue_learning || null} />

      {/* Global Learning Stats */}
      {dashboardData && <LearningStatsGrid stats={dashboardData.stats} />}

      {/* Enrolled Learning Paths */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-indigo-400" />
            <h3 className="text-sm font-semibold text-white">
              Mes Parcours de Formation
            </h3>
          </div>
          <span className="text-xs font-mono text-slate-500">
            {courses.length} formation{courses.length > 1 ? "s" : ""}
          </span>
        </div>

        {courses.length === 0 ? (
          <div className="py-8 text-center text-slate-400 text-xs">
            Vous n&apos;êtes inscrit à aucun parcours actuellement.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {courses.map((item) => (
              <Link
                key={item.id}
                href={`/courses/${item.course.id}`}
                className="p-4 rounded-xl border border-slate-800 bg-slate-950/60 hover:border-indigo-500/50 hover:bg-slate-900/80 transition flex flex-col justify-between group"
              >
                <div>
                  <div className="flex items-center justify-between text-[11px] mb-2">
                    <span className="text-slate-400 font-medium">
                      {item.course.organization_name}
                    </span>
                    <span
                      className={`font-semibold px-2 py-0.5 rounded ${
                        item.status === "COMPLETED"
                          ? "bg-emerald-500/20 text-emerald-300"
                          : item.status === "IN_PROGRESS"
                          ? "bg-indigo-500/20 text-indigo-300"
                          : "bg-slate-800 text-slate-400"
                      }`}
                    >
                      {item.status === "COMPLETED"
                        ? "Terminé"
                        : item.status === "IN_PROGRESS"
                        ? "En cours"
                        : "Non démarré"}
                    </span>
                  </div>

                  <h4 className="text-sm font-bold text-white group-hover:text-indigo-300 transition truncate">
                    {item.course.title}
                  </h4>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-800/80">
                  <div className="flex justify-between text-xs mb-1.5">
                    <span className="text-slate-400">Progression</span>
                    <span className="font-mono font-bold text-indigo-300">
                      {item.progress.toFixed(0)}%
                    </span>
                  </div>
                  <div className="h-1.5 w-full rounded-full bg-slate-800 overflow-hidden">
                    <div
                      className="h-full rounded-full bg-indigo-500"
                      style={{ width: `${item.progress}%` }}
                    />
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>

      {/* Split Grid for Weak Topics & Recommendations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <WeakTopicsList topics={dashboardData?.weak_topics || []} />
        <RecommendedRevisionList recommendations={dashboardData?.recommended_revision || []} />
      </div>

      {/* Recent Activity */}
      <RecentActivityList activities={dashboardData?.recent_activity || []} />
    </div>
  );
}

export default function LearningPage() {
  return (
    <ProtectedRoute>
      <LearningHubContent />
    </ProtectedRoute>
  );
}
