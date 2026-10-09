"use client";

import React from "react";
import Link from "next/link";
import { History, Clock, BookOpen } from "lucide-react";
import { RecentActivityItem } from "../../types/learning";
import { useTranslation } from "../../lib/i18n/LanguageContext";

interface RecentActivityListProps {
  activities: RecentActivityItem[];
}

export const RecentActivityList: React.FC<RecentActivityListProps> = ({ activities }) => {
  const { t, language } = useTranslation();

  const formatDuration = (totalSeconds: number): string => {
    if (!totalSeconds || totalSeconds <= 0) return `< 1 ${t("dashboard.minutes")}`;
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const hUnit = t("common.hourShort");
    const mUnit = t("common.minShort");
    if (hours > 0) {
      return `${hours}${hUnit} ${minutes}${mUnit}`;
    }
    return `${minutes} ${t("dashboard.minutes")}`;
  };

  const formatDate = (dateStr: string): string => {
    try {
      const d = new Date(dateStr);
      const locale = language === "ar" ? "ar-EG" : language === "en" ? "en-US" : "fr-FR";
      return d.toLocaleDateString(locale, {
        day: "numeric",
        month: "short",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur-sm">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <History className="w-4 h-4 text-violet-400" />
          <h3 className="text-sm font-semibold text-white">{t("dashboard.recentActivityTitle")}</h3>
        </div>
        <span className="text-xs font-mono text-slate-500">
          {activities.length} {t("dashboard.sessionsCount")}
        </span>
      </div>

      {activities.length === 0 ? (
        <div className="py-8 text-center text-slate-400 text-xs">
          {t("dashboard.noRecentActivityRecorded")}
        </div>
      ) : (
        <div className="space-y-2.5">
          {activities.map((act) => (
            <div
              key={act.id}
              className="flex items-center justify-between gap-3 p-3 rounded-xl border border-slate-800 bg-slate-950/40 hover:bg-slate-800/40 transition"
            >
              <div className="min-w-0">
                <Link
                  href={`/courses/${act.course_id}`}
                  className="text-xs font-semibold text-white hover:text-indigo-300 transition truncate block"
                >
                  {act.course_title}
                </Link>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  {formatDate(act.started_at)}
                </p>
              </div>

              <div className="flex items-center gap-1.5 shrink-0 px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-xs font-mono text-slate-300">
                <Clock className="w-3.5 h-3.5 text-indigo-400" />
                <span>{formatDuration(act.duration)}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
