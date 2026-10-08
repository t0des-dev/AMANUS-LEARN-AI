"use client";

import React from "react";
import Link from "next/link";
import {
  FileText,
  Presentation,
  FileCode,
  Calendar,
  Layers,
  Download,
  Trash2,
  Play,
  ArrowRight,
} from "lucide-react";
import { DocumentItem } from "../../types/document";
import { DocumentStatus } from "./DocumentStatus";

interface DocumentCardProps {
  document: DocumentItem;
  canManage?: boolean;
  onProcess?: (doc: DocumentItem) => void;
  onDelete?: (doc: DocumentItem) => void;
}

export function DocumentCard({
  document,
  canManage = true,
  onProcess,
  onDelete,
}: DocumentCardProps) {
  const getFormatIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case "pdf":
        return {
          icon: FileText,
          color: "text-rose-400 bg-rose-500/10 border-rose-500/20",
          tag: "PDF",
        };
      case "docx":
      case "doc":
        return {
          icon: FileText,
          color: "text-blue-400 bg-blue-500/10 border-blue-500/20",
          tag: "DOCX",
        };
      case "pptx":
      case "ppt":
        return {
          icon: Presentation,
          color: "text-amber-400 bg-amber-500/10 border-amber-500/20",
          tag: "PPTX",
        };
      case "txt":
      default:
        return {
          icon: FileCode,
          color: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
          tag: "TXT",
        };
    }
  };

  const formatMeta = getFormatIcon(document.file_type);
  const Icon = formatMeta.icon;

  const formattedDate = new Date(document.created_at).toLocaleDateString("fr-FR", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });

  return (
    <div className="group relative flex flex-col justify-between overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/50 p-5 shadow-lg backdrop-blur-md transition-all duration-300 hover:-translate-y-1 hover:border-slate-700 hover:bg-slate-900/80 hover:shadow-2xl hover:shadow-indigo-500/10">
      {/* Top Section */}
      <div>
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="flex items-center gap-3">
            <div
              className={`flex h-11 w-11 items-center justify-center rounded-xl border shadow-inner ${formatMeta.color}`}
            >
              <Icon className="h-5 w-5" />
            </div>
            <div>
              <span className="inline-block rounded-md bg-slate-800 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-slate-300">
                {formatMeta.tag}
              </span>
              <p className="text-[11px] text-slate-400">
                {document.file_size_human}
              </p>
            </div>
          </div>

          <DocumentStatus status={document.status} size="sm" />
        </div>

        <Link
          href={`/documents/${document.id}`}
          className="group-hover:text-indigo-400 transition"
        >
          <h3 className="line-clamp-1 text-base font-semibold text-white">
            {document.title}
          </h3>
        </Link>

        {document.description ? (
          <p className="mt-1 line-clamp-2 text-xs text-slate-400 leading-relaxed">
            {document.description}
          </p>
        ) : (
          <p className="mt-1 text-xs italic text-slate-500">
            {document.file_name}
          </p>
        )}
      </div>

      {/* Meta Bar */}
      <div className="mt-5 border-t border-slate-800/80 pt-4">
        <div className="flex items-center justify-between text-[11px] text-slate-400 mb-3">
          <div className="flex items-center gap-1.5">
            <Calendar className="h-3.5 w-3.5 text-slate-500" />
            <span>{formattedDate}</span>
          </div>

          {document.page_count > 0 && (
            <div className="flex items-center gap-1">
              <Layers className="h-3.5 w-3.5 text-slate-500" />
              <span>{document.page_count} pages estimées</span>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-between gap-2">
          <Link
            href={`/documents/${document.id}`}
            className="flex items-center gap-1 text-xs font-semibold text-indigo-400 transition hover:text-indigo-300"
          >
            <span>Détails</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>

          <div className="flex items-center gap-1.5">
            {document.download_url && (
              <a
                href={document.download_url}
                target="_blank"
                rel="noreferrer"
                download
                className="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-800 bg-slate-850 text-slate-400 transition hover:border-slate-700 hover:text-white"
                title="Télécharger le fichier"
              >
                <Download className="h-3.5 w-3.5" />
              </a>
            )}

            {canManage && onProcess && document.status === "UPLOADED" && (
              <button
                type="button"
                onClick={() => onProcess(document)}
                className="flex items-center gap-1 rounded-lg border border-indigo-500/30 bg-indigo-500/10 px-2.5 py-1.5 text-xs font-medium text-indigo-300 transition hover:bg-indigo-600 hover:text-white"
                title="Préparer le pipeline de traitement"
              >
                <Play className="h-3 w-3" />
                <span>Traiter</span>
              </button>
            )}

            {canManage && onDelete && (
              <button
                type="button"
                onClick={() => onDelete(document)}
                className="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-800 bg-slate-850 text-slate-400 transition hover:border-rose-900/50 hover:bg-rose-500/10 hover:text-rose-400"
                title="Supprimer le document"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
