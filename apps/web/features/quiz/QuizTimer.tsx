"use client";

import React, { useEffect, useState, useRef } from "react";
import { Clock, AlertTriangle } from "lucide-react";

interface QuizTimerProps {
  timeLimitMinutes: number;
  onTimeUp: () => void;
  isPaused?: boolean;
  className?: string;
}

export function QuizTimer({
  timeLimitMinutes,
  onTimeUp,
  isPaused = false,
  className = "",
}: QuizTimerProps) {
  // Total seconds remaining
  const [secondsRemaining, setSecondsRemaining] = useState<number>(timeLimitMinutes * 60);
  const onTimeUpRef = useRef(onTimeUp);
  onTimeUpRef.current = onTimeUp;

  useEffect(() => {
    setSecondsRemaining(timeLimitMinutes * 60);
  }, [timeLimitMinutes]);

  useEffect(() => {
    if (isPaused || secondsRemaining <= 0) return;

    const interval = setInterval(() => {
      setSecondsRemaining((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          onTimeUpRef.current();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [isPaused, secondsRemaining]);

  const minutes = Math.floor(secondsRemaining / 60);
  const seconds = secondsRemaining % 60;
  const formatted = `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;

  const isWarning = secondsRemaining <= 120 && secondsRemaining > 30;
  const isCritical = secondsRemaining <= 30;

  return (
    <div
      className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border font-mono text-sm font-semibold transition-colors ${
        isCritical
          ? "bg-rose-50 border-rose-300 text-rose-700 animate-pulse dark:bg-rose-950/40 dark:border-rose-800 dark:text-rose-300"
          : isWarning
          ? "bg-amber-50 border-amber-300 text-amber-800 dark:bg-amber-950/40 dark:border-amber-800 dark:text-amber-300"
          : "bg-slate-50 border-slate-200 text-slate-700 dark:bg-slate-900 dark:border-slate-800 dark:text-slate-200"
      } ${className}`}
    >
      {isCritical || isWarning ? (
        <AlertTriangle className="h-4 w-4 shrink-0 text-current" />
      ) : (
        <Clock className="h-4 w-4 shrink-0 text-slate-500 dark:text-slate-400" />
      )}
      <span>{formatted}</span>
      {isCritical && <span className="text-xs font-sans font-medium uppercase tracking-wide">Dernières secondes !</span>}
    </div>
  );
}
