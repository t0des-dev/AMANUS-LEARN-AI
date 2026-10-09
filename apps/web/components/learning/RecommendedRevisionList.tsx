"use client";

import React from "react";
import Link from "next/link";
import { Sparkles, ArrowRight, Zap, Target } from "lucide-react";
import { RecommendedRevisionItem } from "../../types/learning";
import { useTranslation } from "../../lib/i18n/LanguageContext";

interface RecommendedRevisionListProps {
  recommendations: RecommendedRevisionItem[];
}

export const RecommendedRevisionList: React.FC<RecommendedRevisionListProps> = ({
  recommendations,
}) => {
  const { t } = useTranslation();

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur-sm">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-amber-400" />
          <h3 className="text-sm font-semibold text-white">{t("dashboard.recommendedAiRevisions")}</h3>
        </div>
        <span className="text-xs font-mono text-slate-500">
          {recommendations.length} {t("dashboard.suggestionsCount")}
        </span>
      </div>

      {recommendations.length === 0 ? (
        <div className="py-8 text-center text-slate-400 text-xs">
          {t("dashboard.noUrgentRevisions")}
        </div>
      ) : (
        <div className="space-y-2.5">
          {recommendations.map((rec, idx) => {
            const isWeak = rec.type === "weak_topic";
            const targetUrl = rec.section_id
              ? `/courses/${rec.course_id}/learn?section=${rec.section_id}`
              : `/courses/${rec.course_id}`;

            return (
              <div
                key={idx}
                className={`flex items-center justify-between gap-3 p-3.5 rounded-xl border transition ${
                  isWeak
                    ? "border-amber-500/20 bg-amber-950/20 hover:bg-amber-950/30"
                    : "border-indigo-500/20 bg-indigo-950/20 hover:bg-indigo-950/30"
                }`}
              >
                <div className="min-w-0">
                  <div className="flex items-center gap-1.5 mb-1">
                    {isWeak ? (
                      <span className="text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
                        {t("dashboard.highPriority")}
                      </span>
                    ) : (
                      <span className="text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                        {t("dashboard.inProgressStatus")}
                      </span>
                    )}
                    <span className="text-xs text-slate-400 truncate">
                      {rec.course_title}
                    </span>
                  </div>

                  <h4 className="text-xs font-semibold text-white truncate">
                    {rec.title}
                  </h4>
                  <p className="text-[11px] text-slate-400 mt-0.5 truncate">
                    {rec.reason}
                  </p>
                </div>

                <Link
                  href={targetUrl}
                  className={`flex items-center gap-1 text-xs font-semibold px-3 py-1.5 rounded-lg shrink-0 transition ${
                    isWeak
                      ? "bg-amber-600 hover:bg-amber-500 text-white"
                      : "bg-indigo-600 hover:bg-indigo-500 text-white"
                  }`}
                >
                  <span>{t("dashboard.reviewBtn")}</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
