"use client";

import React from "react";
import { CheckCircle2, Clock, BookOpen } from "lucide-react";
import { useTranslation } from "../../lib/i18n/LanguageContext";

interface CourseProgressProps {
  totalLessons: number;
  completedLessons: number;
  totalMinutes: number;
  className?: string;
}

export function CourseProgress({
  totalLessons,
  completedLessons,
  totalMinutes,
  className = "",
}: CourseProgressProps) {
  const { t } = useTranslation();
  const percent = totalLessons > 0 ? Math.round((completedLessons / totalLessons) * 100) : 0;
  const remaining = Math.max(0, totalLessons - completedLessons);

  return (
    <div className={`bg-slate-900/80 rounded-2xl border border-slate-800 p-3.5 shadow-md ${className}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold text-slate-300">{t("courses.progress")}</span>
        <span className="text-xs font-bold font-mono text-indigo-400">{percent}%</span>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-slate-800 rounded-full h-2 mb-3 overflow-hidden">
        <div
          className="bg-gradient-to-r from-indigo-500 to-emerald-400 h-2 rounded-full transition-all duration-500 ease-out"
          style={{ width: `${percent}%` }}
        />
      </div>

      {/* Quick Metrics */}
      <div className="flex items-center justify-between gap-2 text-[11px] text-slate-400 pt-2 border-t border-slate-800/80 font-mono">
        <div className="flex items-center gap-1 text-emerald-400">
          <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
          <span>
            {completedLessons} / {totalLessons} {t("courses.completed")}
          </span>
        </div>
        <div className="flex items-center gap-1 text-slate-400">
          <BookOpen className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
          <span>{remaining} {t("courses.remaining")}</span>
        </div>
        <div className="flex items-center gap-1 text-slate-400">
          <Clock className="w-3.5 h-3.5 text-purple-400 shrink-0" />
          <span>~{totalMinutes} min</span>
        </div>
      </div>
    </div>
  );
}
