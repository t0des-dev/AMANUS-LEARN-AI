"use client";

import React from "react";
import {
  Users,
  TrendingUp,
  Award,
  AlertTriangle,
  Clock,
  CheckCircle2,
  BookOpen,
} from "lucide-react";
import { CourseAnalyticsResponse } from "../../types/analytics";

interface CourseAnalyticsProps {
  data: CourseAnalyticsResponse;
}

function formatDuration(seconds: number): string {
  if (!seconds || seconds <= 0) return "0 min";
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes} min`;
}

export const CourseAnalytics: React.FC<CourseAnalyticsProps> = ({ data }) => {
  const { summary, problematic_chapters } = data;

  const kpis = [
    {
      label: "Étudiants inscrits",
      value: summary.total_students.toString(),
      sub: `${summary.completed_students} ont terminé`,
      icon: <Users className="w-5 h-5 text-indigo-400" />,
      color: "border-indigo-500/20",
    },
    {
      label: "Progression moyenne",
      value: `${summary.average_progress.toFixed(0)}%`,
      sub: `Taux de complétion : ${summary.completion_rate.toFixed(0)}%`,
      icon: <TrendingUp className="w-5 h-5 text-emerald-400" />,
      color: "border-emerald-500/20",
    },
    {
      label: "Score moyen aux quiz",
      value: summary.average_score !== null ? `${summary.average_score.toFixed(0)}%` : "--",
      sub: `Taux de réussite : ${summary.pass_rate.toFixed(0)}%`,
      icon: <Award className="w-5 h-5 text-amber-400" />,
      color: "border-amber-500/20",
    },
    {
      label: "Temps total d'étude",
      value: formatDuration(summary.total_study_time_seconds),
      sub: `${summary.total_quiz_attempts} quiz passés`,
      icon: <Clock className="w-5 h-5 text-violet-400" />,
      color: "border-violet-500/20",
    },
  ];

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpis.map((k, idx) => (
          <div
            key={idx}
            className={`rounded-2xl border ${k.color} bg-slate-900/60 p-5 backdrop-blur-sm flex items-center justify-between`}
          >
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                {k.label}
              </p>
              <p className="mt-2 text-2xl font-bold font-mono text-white">
                {k.value}
              </p>
              <p className="mt-0.5 text-[11px] text-slate-500">{k.sub}</p>
            </div>
            <div className="h-11 w-11 rounded-xl bg-slate-800/80 border border-slate-700/50 flex items-center justify-center shrink-0">
              {k.icon}
            </div>
          </div>
        ))}
      </div>

      {/* Chapitres problématiques (Problematic chapters) */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-sm space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-400" />
            <div>
              <h3 className="text-sm font-semibold text-white">
                Chapitres problématiques détectés
              </h3>
              <p className="text-xs text-slate-400">
                Modules nécessitant un ajustement pédagogique (taux d&apos;abandon élevé ou score bas)
              </p>
            </div>
          </div>
          <span className="text-xs font-mono text-slate-500">
            {problematic_chapters.length} module{problematic_chapters.length > 1 ? "s" : ""}
          </span>
        </div>

        {problematic_chapters.length === 0 ? (
          <div className="py-8 text-center text-slate-400 text-xs flex flex-col items-center gap-2">
            <CheckCircle2 className="w-8 h-8 text-emerald-400 opacity-60" />
            <p className="font-medium text-slate-300">Aucun blocage identifié</p>
            <p className="text-[11px] text-slate-500">
              Tous les chapitres bénéficient d&apos;un bon taux de complétion et de notes satisfaisantes.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {problematic_chapters.map((chap) => (
              <div
                key={chap.section_id}
                className={`p-4 rounded-xl border transition flex flex-col sm:flex-row sm:items-center justify-between gap-4 ${
                  chap.is_problematic
                    ? "border-amber-500/30 bg-amber-950/20"
                    : "border-slate-800 bg-slate-950/40"
                }`}
              >
                <div className="space-y-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                      Module #{chap.order}
                    </span>
                    {chap.is_problematic && (
                      <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
                        Attention requise
                      </span>
                    )}
                  </div>
                  <h4 className="text-sm font-semibold text-white truncate">
                    {chap.section_title}
                  </h4>
                </div>

                <div className="flex items-center gap-6 shrink-0 text-xs font-mono">
                  <div>
                    <span className="text-[10px] text-slate-500 block uppercase">
                      Complétion
                    </span>
                    <span className="text-slate-200 font-bold">
                      {chap.completion_rate.toFixed(0)}%
                    </span>
                    <span className="text-[10px] text-slate-500 ml-1">
                      ({chap.students_completed}/{chap.total_students})
                    </span>
                  </div>

                  <div>
                    <span className="text-[10px] text-slate-500 block uppercase">
                      Score moyen
                    </span>
                    <span
                      className={`font-bold ${
                        chap.average_score !== null && chap.average_score < 60
                          ? "text-rose-400"
                          : "text-emerald-400"
                      }`}
                    >
                      {chap.average_score !== null ? `${chap.average_score.toFixed(0)}%` : "--"}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
