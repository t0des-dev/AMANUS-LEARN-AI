"use client";

import React from "react";
import Link from "next/link";
import { AlertTriangle, CheckCircle, ArrowRight, BookOpen } from "lucide-react";
import { WeakTopicItem } from "../../types/learning";

interface WeakTopicsListProps {
  topics: WeakTopicItem[];
}

export const WeakTopicsList: React.FC<WeakTopicsListProps> = ({ topics }) => {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur-sm">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-400" />
          <h3 className="text-sm font-semibold text-white">
            Chapitres à consolider (Score &lt; 60%)
          </h3>
        </div>
        <span className="text-xs font-mono text-slate-500">
          {topics.length} point{topics.length > 1 ? "s" : ""} d&apos;attention
        </span>
      </div>

      {topics.length === 0 ? (
        <div className="py-8 text-center text-slate-400 text-xs flex flex-col items-center gap-2">
          <CheckCircle className="w-8 h-8 text-emerald-400 opacity-60" />
          <p className="font-medium text-slate-300">Excellente maîtrise générale !</p>
          <p className="text-[11px] text-slate-500 max-w-xs">
            Aucun chapitre faible identifié. Continuez à valider vos évaluations.
          </p>
        </div>
      ) : (
        <div className="space-y-2.5">
          {topics.map((t, idx) => {
            const targetUrl = t.section_id
              ? `/courses/${t.course_id}/learn?section=${t.section_id}`
              : `/courses/${t.course_id}`;

            return (
              <div
                key={idx}
                className="flex items-center justify-between gap-3 p-3 rounded-xl border border-rose-500/20 bg-rose-950/20 hover:bg-rose-950/30 transition group"
              >
                <div className="min-w-0">
                  <h4 className="text-xs font-semibold text-white truncate group-hover:text-rose-200 transition">
                    {t.section_title}
                  </h4>
                  <p className="text-[11px] text-slate-400 truncate mt-0.5">
                    Cours : {t.course_title}
                  </p>
                </div>

                <div className="flex items-center gap-2.5 shrink-0">
                  <span className="px-2 py-0.5 rounded-md font-mono text-xs font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">
                    {t.score.toFixed(0)}%
                  </span>
                  <Link
                    href={targetUrl}
                    className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition"
                    title="Réviser cette notion"
                  >
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
