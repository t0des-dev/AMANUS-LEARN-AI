"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { AlertCircle, ArrowLeft, Loader2 } from "lucide-react";
import { ProtectedRoute } from "../../../components/auth/ProtectedRoute";
import { useAuth } from "../../../components/auth/AuthProvider";
import { useOrganization } from "../../../components/organization/OrganizationContext";
import { documentService } from "../../../services/documentService";
import { DocumentItem } from "../../../types/document";
import { DocumentDetails } from "../../../features/document/DocumentDetails";

function DocumentDetailPageContent() {
  const params = useParams();
  const id = params?.id as string;
  const { token } = useAuth();
  const { currentOrg } = useOrganization();
  const router = useRouter();

  const [document, setDocument] = useState<DocumentItem | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDocument = useCallback(async () => {
    if (!token || !id) return;
    setIsLoading(true);
    setError(null);

    try {
      const data = await documentService.get(token, id);
      setDocument(data);
    } catch (err: any) {
      setError(
        err.message ||
          "Document introuvable ou vous n'avez pas les autorisations nécessaires pour y accéder."
      );
    } finally {
      setIsLoading(false);
    }
  }, [token, id]);

  useEffect(() => {
    fetchDocument();
  }, [fetchDocument]);

  const canManage =
    !currentOrg?.user_role ||
    ["OWNER", "ADMIN", "TEACHER"].includes(currentOrg.user_role) ||
    document?.owner?.email === undefined; // Or owner check

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
      {isLoading ? (
        <div className="flex flex-col items-center justify-center py-24 text-slate-400">
          <Loader2 className="h-8 w-8 animate-spin text-indigo-500 mb-3" />
          <p className="text-xs">Chargement des données du document...</p>
        </div>
      ) : error || !document ? (
        <div className="rounded-3xl border border-rose-500/20 bg-rose-500/10 p-8 text-center backdrop-blur-xl">
          <AlertCircle className="mx-auto h-10 w-10 text-rose-400 mb-3" />
          <h2 className="text-base font-semibold text-white">
            Accès au document impossible
          </h2>
          <p className="mt-1 text-xs text-rose-300 max-w-md mx-auto">
            {error || "Ce document est introuvable ou appartient à une autre organisation."}
          </p>
          <div className="mt-6">
            <Link
              href="/documents"
              className="inline-flex items-center gap-1.5 rounded-xl bg-slate-900 border border-slate-800 px-4 py-2 text-xs font-semibold text-slate-300 hover:text-white"
            >
              <ArrowLeft className="h-4 w-4" />
              <span>Retour à la liste des documents</span>
            </Link>
          </div>
        </div>
      ) : (
        <DocumentDetails
          document={document}
          canManage={canManage}
          onRefresh={fetchDocument}
        />
      )}
    </div>
  );
}

export default function DocumentDetailPage() {
  return (
    <ProtectedRoute>
      <DocumentDetailPageContent />
    </ProtectedRoute>
  );
}
