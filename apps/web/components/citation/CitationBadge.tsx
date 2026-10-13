"use client";

import React from "react";

interface CitationBadgeProps {
  num: number;
  onClick?: (num: number) => void;
  className?: string;
}

export const CitationBadge: React.FC<CitationBadgeProps> = ({
  num,
  onClick,
  className = "",
}) => {
  return (
    <button
      type="button"
      onClick={(e) => {
        e.stopPropagation();
        onClick?.(num);
      }}
      className={`inline-flex items-center px-1.5 py-0.5 mx-0.5 text-xs font-mono font-bold bg-indigo-500/20 hover:bg-indigo-500/40 text-indigo-300 rounded border border-indigo-500/40 transition-colors active:scale-95 cursor-pointer ${className}`}
      title={`Inspecter la citation source [${num}]`}
    >
      [{num}]
    </button>
  );
};
