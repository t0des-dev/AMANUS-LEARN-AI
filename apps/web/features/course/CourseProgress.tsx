"use client";

import React from "react";
import { CheckCircle2, Clock, BookOpen } from "lucide-react";

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
  const percent = totalLessons > 0 ? Math.round((completedLessons / totalLessons) * 100) : 0;

  return (
    <div className={`bg-white rounded-xl border border-gray-200 p-4 shadow-sm ${className}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-gray-700">Progression du cours</span>
        <span className="text-sm font-bold text-blue-600">{percent}%</span>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-gray-100 rounded-full h-2.5 mb-4 overflow-hidden">
        <div
          className="bg-blue-600 h-2.5 rounded-full transition-all duration-500 ease-out"
          style={{ width: `${percent}%` }}
        />
      </div>

      {/* Quick Metrics */}
      <div className="grid grid-cols-3 gap-2 text-xs text-gray-500 pt-2 border-t border-gray-100">
        <div className="flex items-center gap-1.5">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
          <span>
            {completedLessons} / {totalLessons} terminées
          </span>
        </div>
        <div className="flex items-center gap-1.5 justify-center">
          <BookOpen className="w-3.5 h-3.5 text-blue-500" />
          <span>{totalLessons - completedLessons} restantes</span>
        </div>
        <div className="flex items-center gap-1.5 justify-end">
          <Clock className="w-3.5 h-3.5 text-purple-500" />
          <span>~{totalMinutes} min</span>
        </div>
      </div>
    </div>
  );
}
