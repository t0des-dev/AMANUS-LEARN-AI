"use client";

import React from "react";
import { Check, X } from "lucide-react";

interface AnswerOptionProps {
  label: string; // e.g. "A", "B", "C", "D"
  text: string;
  selected: boolean;
  disabled?: boolean;
  onClick: () => void;
  showValidation?: boolean;
  isCorrect?: boolean | null;
  className?: string;
}

export function AnswerOption({
  label,
  text,
  selected,
  disabled = false,
  onClick,
  showValidation = false,
  isCorrect = null,
  className = "",
}: AnswerOptionProps) {
  // Determine color scheme based on validation / selection state
  let containerStyle =
    "border-slate-200 hover:border-indigo-300 hover:bg-indigo-50/40 bg-white dark:bg-slate-900 dark:border-slate-800 dark:hover:border-indigo-800 text-slate-800 dark:text-slate-200";
  let badgeStyle =
    "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300 border-slate-200 dark:border-slate-700";

  if (showValidation) {
    if (isCorrect) {
      containerStyle =
        "border-emerald-500 bg-emerald-50/70 dark:bg-emerald-950/40 dark:border-emerald-700 text-emerald-900 dark:text-emerald-200 ring-1 ring-emerald-500";
      badgeStyle = "bg-emerald-600 text-white border-emerald-600";
    } else if (selected && !isCorrect) {
      containerStyle =
        "border-rose-500 bg-rose-50/70 dark:bg-rose-950/40 dark:border-rose-700 text-rose-900 dark:text-rose-200 ring-1 ring-rose-500";
      badgeStyle = "bg-rose-600 text-white border-rose-600";
    } else {
      containerStyle =
        "border-slate-200 bg-slate-50/50 dark:bg-slate-900/50 dark:border-slate-800 text-slate-400 dark:text-slate-500 opacity-70";
      badgeStyle = "bg-slate-200 text-slate-500 dark:bg-slate-800 dark:text-slate-400 border-transparent";
    }
  } else if (selected) {
    containerStyle =
      "border-indigo-600 bg-indigo-50/60 dark:bg-indigo-950/50 dark:border-indigo-500 text-indigo-950 dark:text-indigo-100 ring-2 ring-indigo-500 shadow-sm";
    badgeStyle = "bg-indigo-600 text-white border-indigo-600";
  }

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={`group relative flex items-start w-full text-left p-4 rounded-xl border transition-all duration-150 ${containerStyle} ${
        disabled ? "cursor-default" : "cursor-pointer"
      } ${className}`}
    >
      {/* Letter badge / icon */}
      <div
        className={`flex items-center justify-center w-8 h-8 rounded-lg font-bold text-sm shrink-0 mr-3 border transition-colors ${badgeStyle}`}
      >
        {showValidation && isCorrect ? (
          <Check className="h-4 w-4" />
        ) : showValidation && selected && !isCorrect ? (
          <X className="h-4 w-4" />
        ) : (
          label
        )}
      </div>

      {/* Answer content */}
      <div className="flex-1 pt-1 text-sm sm:text-base font-normal leading-relaxed">
        {text}
      </div>
    </button>
  );
}
