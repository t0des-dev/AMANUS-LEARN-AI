import React from "react";
import { Award, CheckCircle2, XCircle, TrendingUp } from "lucide-react";
import { ScoreHistoryItem } from "../../types/analytics";
import { useTranslation } from "../../lib/i18n/LanguageContext";

interface ScoreChartProps {
  averageScore: number | null;
  successRate: number;
  scoresHistory: ScoreHistoryItem[];
}

export const ScoreChart: React.FC<ScoreChartProps> = ({
  averageScore,
  successRate,
  scoresHistory,
}) => {
  const { t } = useTranslation();

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-sm space-y-6">
      {/* Header with summary stats */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Award className="w-5 h-5 text-amber-400" />
            <h3 className="text-sm font-semibold text-white">
              {t("analytics.scoresEvolution")}
            </h3>
          </div>
          <p className="mt-1 text-xs text-slate-400">
            {t("quizzes.subtitle")}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-center">
            <span className="text-[10px] text-slate-500 uppercase block font-semibold">
              {t("analytics.averageScoreKpi")}
            </span>
            <span className="text-sm font-mono font-bold text-amber-400">
              {averageScore !== null ? `${averageScore.toFixed(0)}%` : "--"}
            </span>
          </div>
          <div className="px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-center">
            <span className="text-[10px] text-slate-500 uppercase block font-semibold">
              {t("dashboard.masteryScore")}
            </span>
            <span className="text-sm font-mono font-bold text-emerald-400">
              {successRate.toFixed(0)}%
            </span>
          </div>
        </div>
      </div>

      {/* Visual Bar Trend of recent attempts */}
      {scoresHistory.length === 0 ? (
        <div className="py-12 text-center text-xs text-slate-500">
          {t("analytics.noScoresYet")}
        </div>
      ) : (
        <div className="space-y-4">
          <div className="h-44 flex items-end gap-2 pt-6 pb-2 px-2 border-b border-slate-800">
            {scoresHistory.map((item, idx) => {
              const heightPercent = Math.max(8, Math.min(100, item.score));
              const isPass = item.passed;

              return (
                <div
                  key={item.id || idx}
                  className="flex-1 flex flex-col items-center h-full justify-end group relative"
                >
                  {/* Tooltip on hover */}
                  <div className="absolute -top-12 z-20 hidden group-hover:flex flex-col items-center pointer-events-none">
                    <div className="px-2 py-1 rounded bg-slate-950 border border-slate-700 text-[10px] font-mono text-white shadow-xl whitespace-nowrap">
                      {item.quiz_title}: <span className="font-bold">{item.score}%</span> ({isPass ? t("common.success") : t("common.error")})
                    </div>
                    <div className="w-1.5 h-1.5 bg-slate-950 rotate-45 -mt-1 border-r border-b border-slate-700" />
                  </div>

                  {/* Score bar */}
                  <div
                    className={`w-full max-w-[28px] rounded-t-lg transition-all duration-300 ${
                      isPass
                        ? "bg-gradient-to-t from-emerald-600 to-emerald-400 group-hover:brightness-110"
                        : "bg-gradient-to-t from-rose-600 to-amber-500 group-hover:brightness-110"
                    }`}
                    style={{ height: `${heightPercent}%` }}
                  />

                  {/* Label under bar */}
                  <span className="text-[10px] font-mono text-slate-500 mt-2 truncate max-w-full text-center">
                    {item.score.toFixed(0)}%
                  </span>
                </div>
              );
            })}
          </div>

          {/* List of recent scores */}
          <div className="space-y-2 max-h-48 overflow-y-auto pr-1 custom-scrollbar">
            {scoresHistory.map((item) => (
              <div
                key={item.id}
                className="flex items-center justify-between p-2.5 rounded-xl border border-slate-800/80 bg-slate-950/40 text-xs"
              >
                <div className="flex items-center gap-2 min-w-0">
                  {item.passed ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                  ) : (
                    <XCircle className="w-4 h-4 text-rose-400 shrink-0" />
                  )}
                  <span className="font-medium text-white truncate">
                    {item.quiz_title}
                  </span>
                </div>
                <div className="flex items-center gap-3 shrink-0 font-mono text-slate-400">
                  <span>{item.date}</span>
                  <span
                    className={`font-bold px-2 py-0.5 rounded ${
                      item.passed
                        ? "bg-emerald-500/20 text-emerald-300"
                        : "bg-rose-500/20 text-rose-300"
                    }`}
                  >
                    {item.score.toFixed(0)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
