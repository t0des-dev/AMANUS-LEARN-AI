"use client";

import React from "react";
import { Clock, Calendar, Flame } from "lucide-react";
import { StudyTimeDayItem } from "../../types/analytics";

interface StudyTimeChartProps {
  totalSeconds: number;
  studyTimeByDay: StudyTimeDayItem[];
}

function formatDuration(seconds: number): string {
  if (!seconds || seconds <= 0) return "0 min";
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes} min`;
}

export const StudyTimeChart: React.FC<StudyTimeChartProps> = ({
  totalSeconds,
  studyTimeByDay,
}) => {
  const maxMinutes = Math.max(...studyTimeByDay.map((d) => d.duration_minutes), 1);

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-sm space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Clock className="w-5 h-5 text-indigo-400" />
            <h3 className="text-sm font-semibold text-white">
              Temps d&apos;étude des 7 derniers jours
            </h3>
          </div>
          <p className="mt-1 text-xs text-slate-400">
            Sessions actives enregistrées sur vos modules
          </p>
        </div>

        <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-slate-950 border border-slate-800">
          <span className="text-xs text-slate-400">Cumul total :</span>
          <span className="text-sm font-mono font-bold text-indigo-300">
            {formatDuration(totalSeconds)}
          </span>
        </div>
      </div>

      {/* 7 Days Bar Chart */}
      <div className="h-44 flex items-end gap-3 pt-6 pb-2 px-2 border-b border-slate-800">
        {studyTimeByDay.map((item, idx) => {
          const heightPercent = Math.max(4, Math.round((item.duration_minutes / maxMinutes) * 100));
          const hasTime = item.duration_minutes > 0;

          return (
            <div
              key={idx}
              className="flex-1 flex flex-col items-center h-full justify-end group relative"
            >
              {/* Tooltip on hover */}
              <div className="absolute -top-10 z-20 hidden group-hover:flex flex-col items-center pointer-events-none">
                <div className="px-2 py-1 rounded bg-slate-950 border border-slate-700 text-[10px] font-mono text-white shadow-xl whitespace-nowrap">
                  {item.date}: <span className="font-bold">{item.duration_minutes} min</span>
                </div>
                <div className="w-1.5 h-1.5 bg-slate-950 rotate-45 -mt-1 border-r border-b border-slate-700" />
              </div>

              {/* Bar */}
              <div
                className={`w-full max-w-[32px] rounded-t-lg transition-all duration-300 ${
                  hasTime
                    ? "bg-gradient-to-t from-indigo-600 to-indigo-400 group-hover:from-indigo-500 group-hover:to-indigo-300 shadow-md shadow-indigo-950/40"
                    : "bg-slate-800/40"
                }`}
                style={{ height: `${heightPercent}%` }}
              />

              {/* Day label */}
              <span className="text-[11px] font-medium text-slate-400 mt-2 capitalize">
                {item.day_label}
              </span>
            </div>
          );
        })}
      </div>

      <div className="flex items-center justify-between text-xs text-slate-500">
        <span>Min : 0 min</span>
        <span>Pic journalier : {maxMinutes.toFixed(0)} min</span>
      </div>
    </div>
  );
};
