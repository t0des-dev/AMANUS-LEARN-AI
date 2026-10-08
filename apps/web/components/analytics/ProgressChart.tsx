"use client";

import React from "react";
import Link from "next/link";
import { Layers, ArrowRight, CheckCircle2, Clock } from "lucide-react";
import { CourseProgressItem } from "../../types/analytics";

interface ProgressChartProps {
  overallProgress: number;
  coursesProgress: CourseProgressItem[];
}

export const ProgressChart: React.FC<ProgressChartProps> = ({
  overallProgress,
  coursesProgress,
}) => {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-sm space-y-6">
      {/* Overall Progress Gauge Card */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-xl bg-slate-950/60 border border-slate-800">
        <div className="space-y-1">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Progression d&apos;apprentissage globale
          </span>
          <p className="text-sm text-slate-300">
            Moyenne pondérée sur tous vos parcours de formation inscrits
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="relative flex items-center justify-center">
            <span className="text-2xl font-bold font-mono text-indigo-400">
              {overallProgress.toFixed(0)}%
            </span>
          </div>
        </div>
      </div>

      {/* Per Course Progress Breakdown */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-indigo-400" />
            <h3 className="text-sm font-semibold text-white">
              Progression par formation
            </h3>
          </div>
          <span className="text-xs font-mono text-slate-500">
            {coursesProgress.length} cours
          </span>
        </div>

        {coursesProgress.length === 0 ? (
          <div className="py-8 text-center text-xs text-slate-500">
            Aucun cours suivi pour le moment.
          </div>
        ) : (
          <div className="space-y-3.5">
            {coursesProgress.map((item) => {
              const isCompleted = item.progress >= 100;
              return (
                <div
                  key={item.course_id}
                  className="p-3.5 rounded-xl border border-slate-800/80 bg-slate-950/40 hover:bg-slate-950/70 transition space-y-2 group"
                >
                  <div className="flex items-center justify-between gap-2">
                    <Link
                      href={`/courses/${item.course_id}`}
                      className="text-xs font-semibold text-white group-hover:text-indigo-300 transition truncate"
                    >
                      {item.course_title}
                    </Link>

                    <div className="flex items-center gap-2 shrink-0">
                      <span
                        className={`text-[10px] font-semibold px-2 py-0.5 rounded ${
                          isCompleted
                            ? "bg-emerald-500/20 text-emerald-300"
                            : item.status === "IN_PROGRESS"
                            ? "bg-indigo-500/20 text-indigo-300"
                            : "bg-slate-800 text-slate-400"
                        }`}
                      >
                        {isCompleted
                          ? "Terminé"
                          : item.status === "IN_PROGRESS"
                          ? "En cours"
                          : "Non démarré"}
                      </span>
                      <span className="text-xs font-mono font-bold text-slate-300">
                        {item.progress.toFixed(0)}%
                      </span>
                    </div>
                  </div>

                  {/* Progress bar */}
                  <div className="h-1.5 w-full rounded-full bg-slate-800 overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        isCompleted
                          ? "bg-emerald-500"
                          : "bg-gradient-to-r from-indigo-500 to-violet-500"
                      }`}
                      style={{ width: `${Math.max(3, item.progress)}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
