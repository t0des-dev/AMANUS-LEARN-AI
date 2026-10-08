"use client";

import React, { useState } from "react";
import { Users, Search, Clock, Award, CheckCircle2, AlertCircle } from "lucide-react";
import { StudentPerformanceItem } from "../../types/analytics";

interface StudentPerformanceProps {
  students: StudentPerformanceItem[];
}

function formatDuration(seconds: number): string {
  if (!seconds || seconds <= 0) return "0 min";
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes} min`;
}

function formatDate(dateStr: string): string {
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString("fr-FR", {
      day: "numeric",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return dateStr;
  }
}

export const StudentPerformance: React.FC<StudentPerformanceProps> = ({ students }) => {
  const [search, setSearch] = useState("");

  const filtered = students.filter(
    (s) =>
      s.full_name.toLowerCase().includes(search.toLowerCase()) ||
      s.email.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-sm space-y-4">
      {/* Header & Search */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Users className="w-5 h-5 text-indigo-400" />
            <h3 className="text-sm font-semibold text-white">
              Performances individuelles des apprenants
            </h3>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Suivi nominatif de l&apos;avancement et de l&apos;assiduité des étudiants inscrits
          </p>
        </div>

        {/* Search input */}
        <div className="relative w-full sm:w-64">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Rechercher un apprenant..."
            className="w-full pl-9 pr-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-indigo-500 transition"
          />
        </div>
      </div>

      {/* Students Table */}
      {filtered.length === 0 ? (
        <div className="py-12 text-center text-xs text-slate-500">
          {search ? "Aucun étudiant ne correspond à votre recherche." : "Aucun étudiant inscrit pour l'instant."}
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 uppercase text-[10px] tracking-wider">
                <th className="py-3 px-3">Étudiant</th>
                <th className="py-3 px-3">Statut</th>
                <th className="py-3 px-3">Progression</th>
                <th className="py-3 px-3">Temps d&apos;étude</th>
                <th className="py-3 px-3">Score moyen</th>
                <th className="py-3 px-3">Dernière activité</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-sans">
              {filtered.map((s) => {
                const isCompleted = s.status === "COMPLETED";
                const isLowScore = s.average_score !== null && s.average_score < 60;

                return (
                  <tr key={s.student_id} className="hover:bg-slate-800/30 transition">
                    <td className="py-3.5 px-3">
                      <div className="font-semibold text-white truncate max-w-[180px]">
                        {s.full_name}
                      </div>
                      <div className="text-[11px] text-slate-500 truncate max-w-[180px]">
                        {s.email}
                      </div>
                    </td>

                    <td className="py-3.5 px-3">
                      <span
                        className={`text-[10px] font-semibold px-2 py-0.5 rounded ${
                          isCompleted
                            ? "bg-emerald-500/20 text-emerald-300"
                            : s.status === "IN_PROGRESS"
                            ? "bg-indigo-500/20 text-indigo-300"
                            : "bg-slate-800 text-slate-400"
                        }`}
                      >
                        {isCompleted ? "Terminé" : s.status === "IN_PROGRESS" ? "En cours" : "Non démarré"}
                      </span>
                    </td>

                    <td className="py-3.5 px-3">
                      <div className="w-28 space-y-1">
                        <div className="flex justify-between text-[11px] font-mono">
                          <span className="text-slate-300 font-bold">{s.progress.toFixed(0)}%</span>
                        </div>
                        <div className="h-1.5 w-full rounded-full bg-slate-800 overflow-hidden">
                          <div
                            className={`h-full rounded-full ${
                              isCompleted ? "bg-emerald-500" : "bg-indigo-500"
                            }`}
                            style={{ width: `${s.progress}%` }}
                          />
                        </div>
                      </div>
                    </td>

                    <td className="py-3.5 px-3 font-mono text-slate-300">
                      {formatDuration(s.total_study_time_seconds)}
                    </td>

                    <td className="py-3.5 px-3 font-mono font-bold">
                      {s.average_score !== null ? (
                        <span className={isLowScore ? "text-rose-400" : "text-emerald-400"}>
                          {s.average_score.toFixed(0)}%
                        </span>
                      ) : (
                        <span className="text-slate-600 font-normal">--</span>
                      )}
                    </td>

                    <td className="py-3.5 px-3 text-slate-400 font-mono text-[11px]">
                      {formatDate(s.last_activity_at)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
