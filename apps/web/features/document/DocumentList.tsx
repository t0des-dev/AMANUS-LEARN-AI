"use client";

import React, { useState, useMemo } from "react";
import Link from "next/link";
import {
  Search,
  Filter,
  PlusCircle,
  FileQuestion,
  Layers,
  LayoutGrid,
  List,
} from "lucide-react";
import { DocumentItem, DocumentStatus as StatusType } from "../../types/document";
import { DocumentCard } from "./DocumentCard";

interface DocumentListProps {
  documents: DocumentItem[];
  isLoading?: boolean;
  canManage?: boolean;
  onProcess?: (doc: DocumentItem) => void;
  onDelete?: (doc: DocumentItem) => void;
}

export function DocumentList({
  documents,
  isLoading = false,
  canManage = true,
  onProcess,
  onDelete,
}: DocumentListProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedFormat, setSelectedFormat] = useState<string>("ALL");
  const [selectedStatus, setSelectedStatus] = useState<string>("ALL");

  const filteredDocuments = useMemo(() => {
    return documents.filter((doc) => {
      // Search
      const matchesSearch =
        searchTerm === "" ||
        doc.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        doc.file_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        doc.description.toLowerCase().includes(searchTerm.toLowerCase());

      // Format
      const matchesFormat =
        selectedFormat === "ALL" ||
        doc.file_type.toLowerCase() === selectedFormat.toLowerCase();

      // Status
      const matchesStatus =
        selectedStatus === "ALL" || doc.status === selectedStatus;

      return matchesSearch && matchesFormat && matchesStatus;
    });
  }, [documents, searchTerm, selectedFormat, selectedStatus]);

  return (
    <div className="space-y-6">
      {/* Control Bar: Search & Filters */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 rounded-2xl border border-slate-800 bg-slate-950/60 p-4 backdrop-blur-md">
        {/* Search Input */}
        <div className="relative flex-1">
          <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Rechercher par titre, nom de fichier..."
            className="w-full rounded-xl border border-slate-800 bg-slate-900/80 pl-10 pr-4 py-2 text-xs text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
        </div>

        {/* Filter dropdowns */}
        <div className="flex items-center gap-3">
          {/* Format Selector */}
          <select
            value={selectedFormat}
            onChange={(e) => setSelectedFormat(e.target.value)}
            className="rounded-xl border border-slate-800 bg-slate-900 px-3 py-2 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
          >
            <option value="ALL">Tous les formats</option>
            <option value="pdf">PDF</option>
            <option value="docx">Word (.docx)</option>
            <option value="pptx">PowerPoint (.pptx)</option>
            <option value="txt">Texte (.txt)</option>
          </select>

          {/* Status Selector */}
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="rounded-xl border border-slate-800 bg-slate-900 px-3 py-2 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
          >
            <option value="ALL">Tous les statuts</option>
            <option value="UPLOADED">Uploadé</option>
            <option value="PROCESSING">En traitement</option>
            <option value="READY">Prêt</option>
            <option value="FAILED">Échoué</option>
            <option value="ARCHIVED">Archivé</option>
          </select>

          {/* Upload Button */}
          {canManage && (
            <Link
              href="/documents/upload"
              className="inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white shadow-lg shadow-indigo-600/30 transition hover:bg-indigo-500"
            >
              <PlusCircle className="h-4 w-4" />
              <span className="hidden sm:inline">Importer</span>
            </Link>
          )}
        </div>
      </div>

      {/* Content Rendering */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((idx) => (
            <div
              key={idx}
              className="h-56 rounded-2xl border border-slate-800 bg-slate-900/30 animate-pulse p-5"
            />
          ))}
        </div>
      ) : filteredDocuments.length === 0 ? (
        <div className="rounded-3xl border border-slate-800 bg-slate-950/60 p-12 text-center backdrop-blur-xl">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-600/10 text-indigo-400 border border-indigo-500/20 mb-4">
            <FileQuestion className="h-7 w-7" />
          </div>
          <h3 className="text-base font-semibold text-white">
            Aucun document trouvé
          </h3>
          <p className="mt-1 text-xs text-slate-400 max-w-sm mx-auto">
            {searchTerm || selectedFormat !== "ALL" || selectedStatus !== "ALL"
              ? "Aucun résultat ne correspond à vos filtres actuels."
              : "Importez vos cours, manuels ou présentations pour commencer la génération pédagogique."}
          </p>

          {canManage && (
            <div className="mt-6">
              <Link
                href="/documents/upload"
                className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-xs font-semibold text-white shadow-lg shadow-indigo-600/30 transition hover:bg-indigo-500"
              >
                <PlusCircle className="h-4 w-4" />
                <span>Importer un premier document</span>
              </Link>
            </div>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredDocuments.map((doc) => (
            <DocumentCard
              key={doc.id}
              document={doc}
              canManage={canManage}
              onProcess={onProcess}
              onDelete={onDelete}
            />
          ))}
        </div>
      )}
    </div>
  );
}
