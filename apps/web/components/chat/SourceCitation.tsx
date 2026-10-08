"use client";

import React, { useState } from "react";
import {
  FileText,
  ChevronDown,
  ChevronUp,
  Bookmark,
  ExternalLink,
  Layers,
  Sparkles,
} from "lucide-react";
import { SourceCitation as SourceCitationType } from "../../types/chat";

interface SourceCitationProps {
  sources: SourceCitationType[];
  activeCitationId?: number | null;
  onSelectCitation?: (citationId: number) => void;
  className?: string;
}

export function SourceCitation({
  sources,
  activeCitationId,
  onSelectCitation,
  className = "",
}: SourceCitationProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [expandedCardId, setExpandedCardId] = useState<number | null>(null);

  if (!sources || sources.length === 0) {
    return null;
  }

  const toggleCard = (id: number) => {
    setExpandedCardId((prev) => (prev === id ? null : id));
  };

  return (
    <div
      className={`mt-3 rounded-xl border border-indigo-500/20 bg-slate-900/60 p-3 shadow-inner backdrop-blur-sm ${className}`}
    >
      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center gap-2 text-xs font-semibold text-indigo-300 hover:text-indigo-200 transition"
        >
          <Sparkles className="h-3.5 w-3.5 text-indigo-400" />
          <span>
            {sources.length} source{sources.length > 1 ? "s" : ""} documentaire
            {sources.length > 1 ? "s" : ""} citée{sources.length > 1 ? "s" : ""}
          </span>
          {isExpanded ? (
            <ChevronUp className="h-3.5 w-3.5 text-slate-400" />
          ) : (
            <ChevronDown className="h-3.5 w-3.5 text-slate-400" />
          )}
        </button>

        {/* Quick pill numbers */}
        <div className="flex items-center gap-1">
          {sources.map((src) => {
            const isActive = activeCitationId === src.citation_id;
            return (
              <button
                key={src.citation_id}
                type="button"
                onClick={() => {
                  setIsExpanded(true);
                  setExpandedCardId(src.citation_id);
                  if (onSelectCitation) onSelectCitation(src.citation_id);
                }}
                className={`flex h-5 min-w-5 items-center justify-center rounded-full px-1.5 text-[10px] font-bold transition ${
                  isActive
                    ? "bg-indigo-500 text-white shadow-md shadow-indigo-500/30 ring-2 ring-indigo-300"
                    : "bg-slate-800 text-indigo-300 hover:bg-slate-700"
                }`}
                title={`${src.document_title}${src.page ? ` (p. ${src.page})` : ""}`}
              >
                [{src.citation_id}]
              </button>
            );
          })}
        </div>
      </div>

      {isExpanded && (
        <div className="mt-3 space-y-2.5 border-t border-slate-800/80 pt-2.5">
          {sources.map((source) => {
            const isCardOpen =
              expandedCardId === source.citation_id ||
              activeCitationId === source.citation_id;
            const scorePercent =
              source.score != null
                ? Math.round(Number(source.score) * 100)
                : null;

            return (
              <div
                key={source.citation_id}
                className={`rounded-lg border transition-all ${
                  activeCitationId === source.citation_id
                    ? "border-indigo-500 bg-indigo-950/30 shadow-md shadow-indigo-950/50"
                    : "border-slate-800 bg-slate-950/50 hover:border-slate-700"
                }`}
              >
                <button
                  type="button"
                  onClick={() => toggleCard(source.citation_id)}
                  className="flex w-full items-center justify-between p-2.5 text-left text-xs"
                >
                  <div className="flex items-center gap-2 overflow-hidden pr-2">
                    <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded bg-indigo-600/30 text-[10px] font-bold text-indigo-300">
                      [{source.citation_id}]
                    </span>
                    <FileText className="h-3.5 w-3.5 shrink-0 text-slate-400" />
                    <span className="truncate font-medium text-slate-200">
                      {source.document_title}
                    </span>
                  </div>

                  <div className="flex shrink-0 items-center gap-2">
                    {source.page && (
                      <span className="rounded bg-slate-800 px-1.5 py-0.5 text-[10px] text-slate-300">
                        Page {source.page}
                      </span>
                    )}
                    {scorePercent != null && (
                      <span className="rounded bg-emerald-950/60 border border-emerald-800/50 px-1.5 py-0.5 text-[10px] font-semibold text-emerald-400">
                        {scorePercent}%
                      </span>
                    )}
                    {isCardOpen ? (
                      <ChevronUp className="h-3 w-3 text-slate-400" />
                    ) : (
                      <ChevronDown className="h-3 w-3 text-slate-400" />
                    )}
                  </div>
                </button>

                {isCardOpen && (
                  <div className="border-t border-slate-800/80 p-2.5 text-xs">
                    {(source.chapter || source.section) && (
                      <div className="mb-1.5 flex items-center gap-1.5 text-[11px] text-indigo-300/80">
                        <Bookmark className="h-3 w-3 text-indigo-400" />
                        <span>
                          {[source.chapter, source.section]
                            .filter(Boolean)
                            .join(" • ")}
                        </span>
                      </div>
                    )}

                    <blockquote className="rounded bg-slate-900/90 p-2 italic text-slate-300 border-l-2 border-indigo-500">
                      « {source.snippet} »
                    </blockquote>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
