"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  FileText,
  PlusCircle,
  FolderOpen,
  Building2,
  ShieldCheck,
  AlertCircle,
} from "lucide-react";
import { ProtectedRoute } from "../../components/auth/ProtectedRoute";
import { useAuth } from "../../components/auth/AuthProvider";
import { useOrganization } from "../../components/organization/OrganizationContext";
import { documentService } from "../../services/documentService";
import { DocumentItem } from "../../types/document";
import { DocumentList } from "../../features/document/DocumentList";

function DocumentsPageContent() {
  const { token } = useAuth();
  const { currentOrg, organizations, isLoading: isOrgLoading } = useOrganization();

  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDocuments = useCallback(async () => {
    if (!token) return;
    setIsLoading(true);
    setError(null);

    try {
      // Strictly fetch documents isolated for currentOrg if selected
      const docs = await documentService.list(token, {
        organization_id: currentOrg?.id || undefined,
      });
      setDocuments(docs);
    } catch (err: any) {
      setError(err.message || "Impossible de charger les documents.");
    } finally {
      setIsLoading(false);
    }
  }, [token, currentOrg]);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const handleProcess = async (doc: DocumentItem) => {
    if (!token) return;
    try {
      const res = await documentService.process(token, doc.id);
      setDocuments((prev) =>
        prev.map((d) => (d.id === doc.id ? { ...d, status: res.status } : d))
      );
    } catch (err: any) {
      alert(err.message || "Erreur lors du traitement.");
    }
  };

  const handleDelete = async (doc: DocumentItem) => {
    if (!token) return;
    if (!window.confirm(`Supprimer le document "${doc.title}" ?`)) return;

    try {
      await documentService.delete(token, doc.id);
      setDocuments((prev) => prev.filter((d) => d.id !== doc.id));
    } catch (err: any) {
      alert(err.message || "Erreur lors de la suppression.");
    }
  };

  const canManage =
    !currentOrg?.user_role ||
    ["OWNER", "ADMIN", "TEACHER"].includes(currentOrg.user_role);

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-8 border-b border-slate-800 mb-8">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600/10 text-indigo-400 border border-indigo-500/20 shadow-md">
              <FolderOpen className="h-5 w-5" />
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-white">
              Gestionnaire de Documents
            </h1>
          </div>
          <p className="text-xs text-slate-400">
            Importez et organisez les supports pédagogiques (PDF, Word, PPTX, TXT) pour
            générer des contenus d&apos;apprentissage interactifs.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {currentOrg && (
            <div className="flex items-center gap-2 rounded-xl border border-slate-800 bg-slate-900/60 px-3 py-1.5 text-xs text-slate-300">
              <Building2 className="h-3.5 w-3.5 text-indigo-400" />
              <span className="font-semibold text-white">{currentOrg.name}</span>
            </div>
          )}

          {canManage && (
            <Link
              href="/documents/upload"
              className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white shadow-lg shadow-indigo-600/30 transition hover:bg-indigo-500"
            >
              <PlusCircle className="h-4 w-4" />
              <span>Importer un document</span>
            </Link>
          )}
        </div>
      </div>

      {error && (
        <div className="mb-6 rounded-2xl border border-rose-500/20 bg-rose-500/10 p-4 text-xs text-rose-400 flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Document List */}
      <DocumentList
        documents={documents}
        isLoading={isLoading || isOrgLoading}
        canManage={canManage}
        onProcess={handleProcess}
        onDelete={handleDelete}
      />
    </div>
  );
}

export default function DocumentsPage() {
  return (
    <ProtectedRoute>
      <DocumentsPageContent />
    </ProtectedRoute>
  );
}
