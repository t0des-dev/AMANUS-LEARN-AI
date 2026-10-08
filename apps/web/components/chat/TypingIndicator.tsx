"use client";

import React from "react";
import { Sparkles } from "lucide-react";

interface TypingIndicatorProps {
  label?: string;
  className?: string;
}

export function TypingIndicator({
  label = "L'assistant pédagogique réfléchit...",
  className = "",
}: TypingIndicatorProps) {
  return (
    <div
      className={`inline-flex items-center gap-3 rounded-2xl border border-indigo-500/30 bg-slate-900/80 px-4 py-2.5 text-xs text-indigo-300 shadow-lg shadow-indigo-950/40 backdrop-blur-md ${className}`}
    >
      <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-gradient-to-tr from-indigo-600 to-violet-500 text-white shadow-md shadow-indigo-500/20">
        <Sparkles className="h-3.5 w-3.5 animate-pulse" />
      </div>

      <span className="font-medium text-slate-300">{label}</span>

      <div className="flex items-center gap-1 pl-1">
        <span
          className="h-1.5 w-1.5 rounded-full bg-indigo-400 animate-bounce"
          style={{ animationDelay: "0ms" }}
        />
        <span
          className="h-1.5 w-1.5 rounded-full bg-indigo-400 animate-bounce"
          style={{ animationDelay: "150ms" }}
        />
        <span
          className="h-1.5 w-1.5 rounded-full bg-indigo-400 animate-bounce"
          style={{ animationDelay: "300ms" }}
        />
      </div>
    </div>
  );
}
