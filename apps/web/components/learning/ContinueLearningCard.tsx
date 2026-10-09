"use client";

import React from "react";
import Link from "next/link";
import { Play, BookOpen, Clock, ChevronRight, Award } from "lucide-react";
import { ContinueLearningItem } from "../../types/learning";
import { useTranslation } from "../../lib/i18n/LanguageContext";

interface ContinueLearningCardProps {
  item: ContinueLearningItem | null;
}

export const ContinueLearningCard: React.FC<ContinueLearningCardProps> = ({ item }) => {
  const { t } = useTranslation();

  if (!item) {
    return (
      <div className="rounded-2xl border border-slate-800 bg-gradient-to-br from-slate-900/90 to-slate-900/40 p-6 backdrop-blur-sm">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h3 className="text-base font-semibold text-white">{t("dashboard.continueTitle")}</h3>
            <p className="mt-1 text-xs text-slate-400">
              {t("dashboard.noOngoingCourse")}
            </p>
          </div>
          <Link
            href="/courses"
            className="flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white hover:bg-indigo-500 transition shadow-md shadow-indigo-950"
          >
            <BookOpen className="w-4 h-4" />
            <span>{t("dashboard.exploreCourses")}</span>
          </Link>
        </div>
      </div>
    );
  }

  const targetUrl = item.section_id
    ? `/courses/${item.course_id}/learn?section=${item.section_id}`
    : `/courses/${item.course_id}/learn`;

  return (
    <div className="relative overflow-hidden rounded-2xl border border-indigo-500/30 bg-gradient-to-br from-indigo-950/40 via-slate-900/90 to-slate-900 p-6 shadow-xl backdrop-blur-md">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="space-y-3 min-w-0">
          <div className="flex items-center gap-2">
            <span className="flex items-center gap-1.5 rounded-full bg-indigo-500/20 border border-indigo-500/40 px-3 py-1 text-[11px] font-semibold text-indigo-300">
              <span className="h-1.5 w-1.5 rounded-full bg-indigo-400 animate-pulse" />
              {t("dashboard.inProgressBadge")}
            </span>
            {item.section_order && (
              <span className="text-xs text-slate-400 font-mono">
                {t("dashboard.chapterPrefix")}{item.section_order}
              </span>
            )}
          </div>

          <div>
            <h2 className="text-xl font-bold tracking-tight text-white truncate">
              {item.course_title}
            </h2>
            <p className="mt-1 text-sm font-medium text-slate-300 flex items-center gap-1.5">
              <BookOpen className="w-4 h-4 text-indigo-400 shrink-0" />
              <span className="truncate">
                {t("dashboard.nextModule")} {item.section_title || t("dashboard.courseStart")}
              </span>
            </p>
          </div>

          {/* Progress bar */}
          <div className="space-y-1.5 max-w-md pt-1">
            <div className="flex justify-between text-xs">
              <span className="text-slate-400 font-medium">{t("dashboard.globalProgress")}</span>
              <span className="text-indigo-300 font-bold font-mono">{item.progress.toFixed(0)}%</span>
            </div>
            <div className="h-2 w-full rounded-full bg-slate-800 overflow-hidden">
              <div
                className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-violet-500 transition-all duration-500"
                style={{ width: `${Math.max(5, item.progress)}%` }}
              />
            </div>
          </div>
        </div>

        {/* Action Button */}
        <div className="shrink-0 flex items-center">
          <Link
            href={targetUrl}
            className="flex items-center gap-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold px-5 py-3 text-sm shadow-lg shadow-indigo-950/60 transition active:scale-95 group"
          >
            <Play className="w-4 h-4 fill-current group-hover:translate-x-0.5 transition" />
            <span>{t("dashboard.resumeLesson")}</span>
            <ChevronRight className="w-4 h-4 opacity-70 group-hover:translate-x-0.5 transition" />
          </Link>
        </div>
      </div>
    </div>
  );
};
