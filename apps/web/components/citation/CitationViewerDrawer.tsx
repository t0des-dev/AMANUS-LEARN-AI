"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  X,
  BookOpen,
  FileText,
  Search,
  ExternalLink,
  ChevronRight,
  Sparkles,
  Layers,
  Loader2,
  AlertCircle,
} from "lucide-react";
import { documentService } from "../../services/documentService";
import { DocumentChunkItem } from "../../types/document";
import { useAuth } from "../auth/AuthProvider";
import { useTranslation } from "../../lib/i18n/LanguageContext";

interface CitationViewerDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  documentId: string;
  documentTitle?: string;
  highlightIndex?: number; // 0-indexed chunk to highlight
}

export const CitationViewerDrawer: React.FC<CitationViewerDrawerProps> = ({
  isOpen,
  onClose,
  documentId,
  documentTitle,
  highlightIndex,
}) => {
  const { token } = useAuth();
  const { t } = useTranslation();
  const [chunks, setChunks] = useState<DocumentChunkItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const chunkRefs = useRef<(HTMLDivElement | null)[]>([]);

  useEffect(() => {
    if (!isOpen || !token || !documentId) return;

    let isMounted = true;
    setIsLoading(true);
    setError(null);

    documentService
      .getChunks(token, documentId)
      .then((res) => {
        if (isMounted) {
          setChunks(res.results || []);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(
            err instanceof Error ? err.message : "Impossible de charger les segments sources."
          );
        }
      })
      .finally(() => {
        if (isMounted) setIsLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [isOpen, token, documentId]);

  // Scroll to highlighted citation index
  useEffect(() => {
    if (
      isOpen &&
      chunks.length > 0 &&
      highlightIndex !== undefined &&
      highlightIndex >= 0 &&
      highlightIndex < chunks.length
    ) {
      setTimeout(() => {
        chunkRefs.current[highlightIndex]?.scrollIntoView({
          behavior: "smooth",
          block: "center",
        });
      }, 200);
    }
  }, [isOpen, highlightIndex, chunks]);

  if (!isOpen) return null;

  const filteredChunks = chunks.filter((c) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      c.content.toLowerCase().includes(q) ||
      (c.metadata?.chapter && c.metadata.chapter.toLowerCase().includes(q)) ||
      (c.metadata?.section && c.metadata.section.toLowerCase().includes(q))
    );
  });

  return (
    <div className="fixed inset-0 z-50 flex justify-end overflow-hidden">
      {/* Dimmed Backdrop */}
      <div
        className="fixed inset-0 bg-slate-950/70 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      {/* Drawer Panel */}
      <div className="relative z-10 w-full max-w-xl bg-slate-900 border-l border-slate-800 shadow-2xl flex flex-col h-full animate-in slide-in-from-right duration-300">
        {/* Header */}
        <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-950/40">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-indigo-400" />
              <h2 className="text-sm font-bold text-white">
                {t("documents.citationsTitle", "Sources & Citations Documentaires")}
              </h2>
            </div>
            <p className="text-xs text-slate-400 truncate max-w-sm">
              {documentTitle || t("documents.citationsDesc", "Inspection des segments RAG indexés")}
            </p>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Search bar */}
        <div className="p-4 border-b border-slate-800/80 bg-slate-950/20">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 rtl:left-auto rtl:right-3" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={t("documents.searchChunks", "Rechercher dans les extraits du document...")}
              className="w-full pl-9 pr-4 rtl:pl-4 rtl:pr-9 py-2 bg-slate-950/60 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
            />
          </div>
        </div>

        {/* Content list */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3.5 custom-scrollbar">
          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-20 text-slate-400">
              <Loader2 className="w-8 h-8 animate-spin text-indigo-500 mb-3" />
              <p className="text-xs">{t("documents.loadingData", "Chargement des extraits authentifiés...")}</p>
            </div>
          ) : error ? (
            <div className="rounded-xl border border-rose-500/20 bg-rose-500/10 p-5 text-center">
              <AlertCircle className="w-6 h-6 text-rose-400 mx-auto mb-2" />
              <p className="text-xs text-rose-200">{error}</p>
            </div>
          ) : filteredChunks.length === 0 ? (
            <div className="text-center py-16 text-slate-500 text-xs">
              {t("documents.noChunksFound", "Aucun segment documentaire trouvé.")}
            </div>
          ) : (
            filteredChunks.map((chunk, idx) => {
              const isTarget = highlightIndex !== undefined && chunk.chunk_index === highlightIndex;

              return (
                <div
                  key={chunk.id || idx}
                  ref={(el) => {
                    chunkRefs.current[chunk.chunk_index] = el;
                  }}
                  className={`rounded-2xl p-4 border transition-all duration-300 ${
                    isTarget
                      ? "bg-indigo-950/40 border-indigo-500 shadow-lg shadow-indigo-950/80 ring-2 ring-indigo-500/40"
                      : "bg-slate-950/40 border-slate-800/80 hover:border-slate-700"
                  }`}
                >
                  <div className="flex items-center justify-between gap-2 mb-2.5">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded-md bg-indigo-500/20 border border-indigo-500/30 text-indigo-300 text-[11px] font-mono font-bold">
                        [{chunk.chunk_index + 1}]
                      </span>
                      {chunk.page_number && (
                        <span className="text-[11px] text-slate-400 font-mono">
                          {t("documents.pageNumber", "Page")} {chunk.page_number}
                        </span>
                      )}
                    </div>

                    {isTarget && (
                      <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                        <Sparkles className="w-3 h-3" />
                        Citation Active
                      </span>
                    )}
                  </div>

                  <p className="text-xs text-slate-200 leading-relaxed font-sans select-text whitespace-pre-wrap">
                    {chunk.content}
                  </p>

                  {(chunk.metadata?.chapter || chunk.metadata?.section) && (
                    <div className="mt-3 pt-2.5 border-t border-slate-800/60 flex items-center gap-2 text-[11px] text-slate-400">
                      <Layers className="w-3 h-3 text-slate-500 shrink-0" />
                      <span className="truncate">
                        {[chunk.metadata?.chapter, chunk.metadata?.section]
                          .filter(Boolean)
                          .join(" • ")}
                      </span>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>

        {/* Footer info */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/60 flex items-center justify-between text-xs text-slate-400">
          <span>{chunks.length} {t("documents.pagesIndexed", "segments indexés")}</span>
          <span className="font-mono text-emerald-400">RAG Grounded</span>
        </div>
      </div>
    </div>
  );
};
