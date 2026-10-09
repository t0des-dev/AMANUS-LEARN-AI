"use client";

import React from "react";
import { Clock, CheckCircle2, GraduationCap, Award, Flame } from "lucide-react";
import { LearningStats } from "../../types/learning";
import { useTranslation } from "../../lib/i18n/LanguageContext";

interface LearningStatsGridProps {
  stats: LearningStats;
}

export const LearningStatsGrid: React.FC<LearningStatsGridProps> = ({ stats }) => {
  const { t } = useTranslation();

  const formatDuration = (totalSeconds: number): string => {
    if (!totalSeconds || totalSeconds <= 0) return `0 ${t("dashboard.minutes")}`;
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const hUnit = t("common.hourShort");
    const mUnit = t("common.minShort");
    if (hours > 0) {
      return `${hours}${hUnit} ${minutes}${mUnit}`;
    }
    return `${minutes} ${t("dashboard.minutes")}`;
  };

  const cards = [
    {
      label: t("dashboard.effectiveStudyTime"),
      value: formatDuration(stats.total_study_time_seconds),
      subtext: t("dashboard.recordedSessions"),
      icon: <Clock className="w-5 h-5 text-indigo-400" />,
      border: "border-indigo-500/20",
    },
    {
      label: t("dashboard.completedModules"),
      value: stats.completed_sections_count.toString(),
      subtext: t("dashboard.validatedTopics"),
      icon: <CheckCircle2 className="w-5 h-5 text-emerald-400" />,
      border: "border-emerald-500/20",
    },
    {
      label: t("dashboard.inProgressPaths"),
      value: `${stats.courses_in_progress} / ${stats.total_enrolled_courses}`,
      subtext: `${stats.courses_completed} ${t("dashboard.completedCountSuffix")}`,
      icon: <GraduationCap className="w-5 h-5 text-violet-400" />,
      border: "border-violet-500/20",
    },
    {
      label: t("dashboard.masteryScore"),
      value: stats.average_score !== null ? `${stats.average_score.toFixed(0)}%` : "--",
      subtext: stats.average_score !== null ? t("dashboard.averageEvals") : t("dashboard.noTestPassed"),
      icon: <Award className="w-5 h-5 text-amber-400" />,
      border: "border-amber-500/20",
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card, idx) => (
        <div
          key={idx}
          className={`rounded-2xl border ${card.border} bg-slate-900/60 p-5 backdrop-blur-sm flex items-center justify-between transition hover:border-slate-700`}
        >
          <div className="min-w-0">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              {card.label}
            </p>
            <p className="mt-2 text-2xl font-bold tracking-tight text-white font-mono">
              {card.value}
            </p>
            <p className="mt-0.5 text-[11px] text-slate-500 truncate">
              {card.subtext}
            </p>
          </div>
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-slate-800/80 border border-slate-700/50">
            {card.icon}
          </div>
        </div>
      ))}
    </div>
  );
};
