"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  FileText,
  Presentation,
  FileCode,
  Download,
  Trash2,
  Play,
  RotateCw,
  Edit2,
  Check,
  X,
  Calendar,
  Layers,
  Globe,
  HardDrive,
  Shield,
  ArrowLeft,
  AlertTriangle,
  UploadCloud,
  Scan,
  Scissors,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { useAuth } from "../../components/auth/AuthProvider";
import { documentService } from "../../services/documentService";
import {
  DocumentItem,
  DocumentPageItem,
  DocumentProcessingStage,
} from "../../types/document";
import { DocumentStatus } from "./DocumentStatus";

interface DocumentDetailsProps {
  document: DocumentItem;
  canManage?: boolean;
  onRefresh?: () => void;
}

const PIPELINE_STEPS: { stage: DocumentProcessingStage; label: string; icon: React.ElementType }[] = [
  { stage: "Uploading", label: "Uploading", icon: UploadCloud },
  { stage: "Extracting", label: "Extracting", icon: FileText },
  { stage: "OCR", label: "OCR", icon: Scan },
  { stage: "Structuring", label: "Structuring", icon: Layers },
  { stage: "Chunking", label: "Chunking", icon: Scissors },
  { stage: "Completed", label: "Completed", icon: CheckCircle2 },
];

export function DocumentDetails({
  document: initialDoc,
  canManage = true,
  onRefresh,
}: DocumentDetailsProps) {
  const { token } = useAuth();
  const router = useRouter();

  const [doc, setDoc] = useState<DocumentItem>(initialDoc);
  const [currentStage, setCurrentStage] = useState<DocumentProcessingStage | "Failed">(
    (initialDoc.processing_metadata?.progress_stage as DocumentProcessingStage) ||
      (initialDoc.status === "READY" ? "Completed" : "Uploading")
  );
  const [isProcessing, setIsProcessing] = useState(false);
  const [isCheckingStatus, setIsCheckingStatus] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isEditing, setIsEditing] = useState(false);

  // Pages state
  const [pages, setPages] = useState<DocumentPageItem[]>([]);
  const [isLoadingPages, setIsLoadingPages] = useState(false);
  const [expandedPage, setExpandedPage] = useState<number | null>(1);

  // Edit fields
  const [title, setTitle] = useState(doc.title);
  const [description, setDescription] = useState(doc.description);
  const [language, setLanguage] = useState(doc.language);

  const [message, setMessage] = useState<{ text: string; type: "success" | "error" } | null>(
    null
  );

  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const fetchPages = useCallback(async () => {
    if (!token || !doc.id) return;
    setIsLoadingPages(true);
    try {
      const res = await documentService.getPages(token, doc.id);
      setPages(res.results || []);
    } catch {
      // Pages might not be extracted yet
    } finally {
      setIsLoadingPages(false);
    }
  }, [token, doc.id]);

  // Load pages if document is already ready/completed
  useEffect(() => {
    if (doc.status === "READY" || doc.status === "COMPLETED") {
      fetchPages();
    }
  }, [doc.status, fetchPages]);

  // Clean polling on unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, []);

  const startPolling = useCallback(() => {
    if (!token) return;
    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);

    pollIntervalRef.current = setInterval(async () => {
      try {
        const statusRes = await documentService.getProcessingStatus(token, doc.id);
        setCurrentStage(statusRes.progress_stage);
        setDoc((prev) => ({
          ...prev,
          status: statusRes.status,
          page_count: statusRes.pages_count || statusRes.page_count,
          error_message: statusRes.error_message,
        }));

        if (statusRes.progress_stage === "Completed" || statusRes.status === "READY") {
          if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
          setIsProcessing(false);
          fetchPages();
          if (onRefresh) onRefresh();
        } else if (statusRes.progress_stage === "Failed" || statusRes.status === "FAILED") {
          if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
          setIsProcessing(false);
          setMessage({
            text: statusRes.error_message || "Le traitement du document a échoué.",
            type: "error",
          });
        }
      } catch {
        if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
        setIsProcessing(false);
      }
    }, 1500);
  }, [token, doc.id, fetchPages, onRefresh]);

  const handleProcess = async () => {
    if (!token) return;
    setIsProcessing(true);
    setMessage(null);
    setCurrentStage("Extracting");
    try {
      const res = await documentService.process(token, doc.id);
      setDoc((prev) => ({ ...prev, status: res.status }));
      setMessage({
        text: res.message || "Pipeline d'ingestion initialisé avec succès.",
        type: "success",
      });
      startPolling();
    } catch (err: any) {
      setIsProcessing(false);
      setMessage({
        text: err.message || "Échec du déclenchement du traitement.",
        type: "error",
      });
    }
  };

  const handleCheckStatus = async () => {
    if (!token) return;
    setIsCheckingStatus(true);
    setMessage(null);
    try {
      const statusRes = await documentService.getProcessingStatus(token, doc.id);
      setCurrentStage(statusRes.progress_stage);
      setDoc((prev) => ({
        ...prev,
        status: statusRes.status,
        page_count: statusRes.pages_count || statusRes.page_count,
        error_message: statusRes.error_message,
      }));
      setMessage({
        text: `Statut actuel : ${statusRes.progress_stage} (${statusRes.pages_count} pages, ${statusRes.chunks_count} chunks)`,
        type: "success",
      });
      if (statusRes.progress_stage === "Completed") {
        fetchPages();
      }
    } catch (err: any) {
      setMessage({
        text: err.message || "Impossible de vérifier le statut.",
        type: "error",
      });
    } finally {
      setIsCheckingStatus(false);
    }
  };

  const handleUpdate = async () => {
    if (!token) return;
    setMessage(null);
    try {
      const updated = await documentService.update(token, doc.id, {
        title: title.trim(),
        description: description.trim(),
        language,
      });
      setDoc(updated);
      setIsEditing(false);
      setMessage({ text: "Métadonnées mises à jour avec succès.", type: "success" });
    } catch (err: any) {
      setMessage({ text: err.message || "Erreur de mise à jour.", type: "error" });
    }
  };

  const handleDelete = async () => {
    if (!token) return;
    if (!window.confirm("Êtes-vous sûr de vouloir supprimer définitivement ce document ?")) {
      return;
    }
    setIsDeleting(true);
    try {
      await documentService.delete(token, doc.id);
      router.push("/documents");
    } catch (err: any) {
      setMessage({
        text: err.message || "Impossible de supprimer le document.",
        type: "error",
      });
      setIsDeleting(false);
    }
  };

  const getFormatIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case "pdf":
        return <FileText className="h-6 w-6 text-rose-400" />;
      case "pptx":
        return <Presentation className="h-6 w-6 text-amber-400" />;
      case "docx":
        return <FileText className="h-6 w-6 text-sky-400" />;
      default:
        return <FileCode className="h-6 w-6 text-emerald-400" />;
    }
  };

  const getStepIndex = (stage: string) => {
    switch (stage) {
      case "Uploading":
        return 0;
      case "Extracting":
        return 1;
      case "OCR":
        return 2;
      case "Structuring":
        return 3;
      case "Chunking":
        return 4;
      case "Completed":
        return 5;
      default:
        return -1;
    }
  };

  const currentStepIdx = getStepIndex(currentStage);

  return (
    <div className="space-y-6">
      {/* Back button */}
      <div>
        <Link
          href="/documents"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-400 hover:text-white transition"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>Retour aux documents</span>
        </Link>
      </div>

      {/* Main Document Header Card */}
      <div className="rounded-3xl border border-slate-800 bg-slate-900/60 p-6 md:p-8 backdrop-blur-xl shadow-2xl">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
          <div className="flex items-start gap-4">
            <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl border border-slate-700/50 bg-slate-800/80 shadow-inner">
              {getFormatIcon(doc.file_type)}
            </div>

            <div className="space-y-2 flex-1">
              <div className="flex flex-wrap items-center gap-2">
                <DocumentStatus status={doc.status} stage={currentStage} size="sm" />
                <span className="rounded-lg bg-slate-800/80 px-2 py-0.5 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                  {doc.file_type}
                </span>
                <span className="text-[11px] text-slate-500 font-mono">
                  {doc.file_size_human}
                </span>
              </div>

              {isEditing ? (
                <div className="space-y-2 max-w-lg">
                  <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    className="w-full rounded-xl border border-slate-700 bg-slate-900 px-3 py-1.5 text-base font-bold text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                  <textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    rows={2}
                    className="w-full rounded-xl border border-slate-700 bg-slate-900 px-3 py-1 text-xs text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    placeholder="Description..."
                  />
                  <select
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    className="w-full rounded-xl border border-slate-700 bg-slate-900 px-3 py-1.5 text-xs text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  >
                    <option value="fr">Français (FR)</option>
                    <option value="ar">العربية - Arabe (AR)</option>
                    <option value="en">English - Anglais (EN)</option>
                    <option value="es">Español - Espagnol (ES)</option>
                    <option value="de">Deutsch - Allemand (DE)</option>
                  </select>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={handleUpdate}
                      className="inline-flex items-center gap-1 rounded-lg bg-indigo-600 px-3 py-1 text-xs font-semibold text-white hover:bg-indigo-500"
                    >
                      <Check className="h-3.5 w-3.5" /> Enregistrer
                    </button>
                    <button
                      type="button"
                      onClick={() => setIsEditing(false)}
                      className="inline-flex items-center gap-1 rounded-lg border border-slate-800 bg-slate-900 px-3 py-1 text-xs font-semibold text-slate-300 hover:bg-slate-800"
                    >
                      <X className="h-3.5 w-3.5" /> Annuler
                    </button>
                  </div>
                </div>
              ) : (
                <div>
                  <div className="flex items-center gap-2">
                    <h1 className="text-xl md:text-2xl font-bold tracking-tight text-white">
                      {doc.title}
                    </h1>
                    {canManage && (
                      <button
                        type="button"
                        onClick={() => setIsEditing(true)}
                        className="rounded-lg p-1 text-slate-500 transition hover:bg-slate-900 hover:text-white"
                        title="Modifier les informations"
                      >
                        <Edit2 className="h-3.5 w-3.5" />
                      </button>
                    )}
                  </div>
                  <p className="mt-1 text-xs text-slate-400">
                    {doc.description || "Aucune description fournie pour ce document."}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Action Bar */}
          <div className="flex flex-wrap items-center gap-2">
            {doc.download_url && (
              <a
                href={doc.download_url}
                target="_blank"
                rel="noreferrer"
                download
                className="inline-flex items-center gap-1.5 rounded-xl border border-slate-800 bg-slate-900 px-4 py-2 text-xs font-semibold text-slate-200 transition hover:border-slate-700 hover:bg-slate-800 hover:text-white"
              >
                <Download className="h-4 w-4" />
                <span>Télécharger</span>
              </a>
            )}

            {canManage && (
              <button
                type="button"
                onClick={handleProcess}
                disabled={isProcessing}
                className="inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white shadow-lg shadow-indigo-600/30 transition hover:bg-indigo-500 disabled:opacity-50"
              >
                <Play className="h-4 w-4" />
                <span>{isProcessing ? "Ingestion en cours..." : "Lancer l'Ingestion"}</span>
              </button>
            )}

            <button
              type="button"
              onClick={handleCheckStatus}
              disabled={isCheckingStatus}
              className="inline-flex items-center gap-1.5 rounded-xl border border-slate-800 bg-slate-900 px-3.5 py-2 text-xs font-semibold text-slate-300 transition hover:border-slate-700 hover:bg-slate-800 disabled:opacity-50"
              title="Vérifier le statut du pipeline"
            >
              <RotateCw className={`h-3.5 w-3.5 ${isCheckingStatus ? "animate-spin" : ""}`} />
              <span>Statut</span>
            </button>

            {canManage && (
              <button
                type="button"
                onClick={handleDelete}
                disabled={isDeleting}
                className="inline-flex items-center gap-1.5 rounded-xl border border-rose-900/40 bg-rose-500/10 px-4 py-2 text-xs font-semibold text-rose-400 transition hover:bg-rose-500/20 hover:text-rose-300 disabled:opacity-50"
              >
                <Trash2 className="h-4 w-4" />
                <span>{isDeleting ? "Suppression..." : "Supprimer"}</span>
              </button>
            )}
          </div>
        </div>

        {/* Pipeline Progression Stepper */}
        <div className="mt-8 rounded-2xl border border-slate-800/80 bg-slate-950/40 p-4 md:p-6">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">
              Pipeline d'Ingestion Documentaire
            </span>
            <span className="text-xs font-semibold text-indigo-400">
              {currentStage === "Failed" ? "Échec du pipeline" : currentStage}
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2">
            {PIPELINE_STEPS.map((step, idx) => {
              const isPast = currentStepIdx > idx;
              const isCurrent = currentStepIdx === idx && currentStage !== "Failed";
              const isFailed = currentStage === "Failed" && currentStepIdx === idx;
              const StepIcon = step.icon;

              let badgeStyle = "border-slate-800 bg-slate-900/40 text-slate-500";
              if (isPast) {
                badgeStyle = "border-emerald-500/30 bg-emerald-500/10 text-emerald-400 font-semibold";
              } else if (isCurrent) {
                badgeStyle = "border-indigo-500/50 bg-indigo-500/20 text-indigo-300 font-bold ring-1 ring-indigo-500/50 animate-pulse";
              } else if (isFailed) {
                badgeStyle = "border-rose-500/50 bg-rose-500/20 text-rose-400 font-bold";
              }

              return (
                <div
                  key={step.stage}
                  className={`flex flex-col items-center justify-center p-3 rounded-xl border text-center transition ${badgeStyle}`}
                >
                  <StepIcon className="h-4 w-4 mb-1.5" />
                  <span className="text-xs">{step.label}</span>
                </div>
              );
            })}
          </div>

          {currentStage === "Failed" && doc.error_message && (
            <div className="mt-4 flex items-start gap-2 rounded-xl border border-rose-500/30 bg-rose-500/10 p-3 text-xs text-rose-300">
              <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold">Erreur d'ingestion :</p>
                <p className="mt-0.5 text-rose-400/90">{doc.error_message}</p>
              </div>
            </div>
          )}
        </div>

        {/* Notifications / Alerts */}
        {message && (
          <div
            className={`mt-6 rounded-2xl border p-4 text-xs font-medium backdrop-blur-md ${
              message.type === "success"
                ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-300"
                : "border-rose-500/30 bg-rose-500/10 text-rose-300"
            }`}
          >
            {message.text}
          </div>
        )}

        {/* Metadata Grid */}
        <div className="mt-8 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="rounded-2xl border border-slate-850 bg-slate-900/40 p-4">
            <div className="flex items-center gap-2 text-slate-400 mb-1">
              <HardDrive className="h-4 w-4 text-indigo-400" />
              <span className="text-[11px] font-semibold uppercase tracking-wider">Fichier source</span>
            </div>
            <p className="text-sm font-semibold text-white truncate">{doc.file_name}</p>
            <p className="text-xs text-slate-400">{doc.file_size_human} • {doc.file_type.toUpperCase()}</p>
          </div>

          <div className="rounded-2xl border border-slate-850 bg-slate-900/40 p-4">
            <div className="flex items-center gap-2 text-slate-400 mb-1">
              <Layers className="h-4 w-4 text-violet-400" />
              <span className="text-[11px] font-semibold uppercase tracking-wider">Pages extraites</span>
            </div>
            <p className="text-sm font-semibold text-white">
              {doc.page_count > 0 ? `${doc.page_count} page(s)` : "En attente d'ingestion"}
            </p>
            <p className="text-xs text-slate-400">
              {pages.length > 0 ? `${pages.length} pages indexées` : "Prêt pour chunking"}
            </p>
          </div>

          <div className="rounded-2xl border border-slate-850 bg-slate-900/40 p-4">
            <div className="flex items-center gap-2 text-slate-400 mb-1">
              <Globe className="h-4 w-4 text-emerald-400" />
              <span className="text-[11px] font-semibold uppercase tracking-wider">Langue du contenu</span>
            </div>
            <p className="text-sm font-semibold text-white">
              {doc.language === "ar"
                ? "العربية - Arabe (AR)"
                : doc.language === "fr"
                ? "Français (FR)"
                : doc.language === "en"
                ? "English (EN)"
                : doc.language === "es"
                ? "Español (ES)"
                : doc.language === "de"
                ? "Deutsch (DE)"
                : doc.language.toUpperCase()}
            </p>
            <p className="text-xs text-slate-400">Langue principale détectée</p>
          </div>

          <div className="rounded-2xl border border-slate-850 bg-slate-900/40 p-4">
            <div className="flex items-center gap-2 text-slate-400 mb-1">
              <Calendar className="h-4 w-4 text-amber-400" />
              <span className="text-[11px] font-semibold uppercase tracking-wider">Date d'importation</span>
            </div>
            <p className="text-sm font-semibold text-white">
              {new Date(doc.created_at).toLocaleDateString("fr-FR", {
                day: "numeric",
                month: "short",
                year: "numeric",
              })}
            </p>
            <p className="text-xs text-slate-400">
              {new Date(doc.created_at).toLocaleTimeString("fr-FR", {
                hour: "2-digit",
                minute: "2-digit",
              })}
            </p>
          </div>
        </div>

        {/* Extracted Document Pages Section */}
        {pages.length > 0 && (
          <div className="mt-8 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FileText className="h-4 w-4 text-indigo-400" />
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                  Pages Extraites & Structure ({pages.length})
                </h3>
              </div>
              <span className="text-xs text-slate-400">Structure hiérarchique préservée</span>
            </div>

            <div className="space-y-3">
              {pages.map((p) => {
                const isExpanded = expandedPage === p.page_number;
                return (
                  <div
                    key={p.id}
                    className="rounded-2xl border border-slate-800 bg-slate-900/40 p-4 transition hover:border-slate-700"
                  >
                    <div
                      className="flex items-center justify-between cursor-pointer"
                      onClick={() => setExpandedPage(isExpanded ? null : p.page_number)}
                    >
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="rounded-lg bg-indigo-500/10 px-2.5 py-1 text-xs font-bold text-indigo-300 border border-indigo-500/20">
                          Page {p.page_number}
                        </span>
                        {p.ocr_used && (
                          <span className="rounded-lg bg-violet-500/10 px-2 py-0.5 text-[11px] font-semibold text-violet-300 border border-violet-500/20">
                            OCR
                          </span>
                        )}
                        {p.metadata?.chapter && (
                          <span className="text-xs font-medium text-slate-300">
                            {p.metadata.chapter}
                          </span>
                        )}
                        {p.metadata?.section && (
                          <span className="text-xs text-slate-400">
                            › {p.metadata.section}
                          </span>
                        )}
                      </div>

                      <button
                        type="button"
                        className="rounded-lg p-1 text-slate-400 hover:text-white"
                      >
                        {isExpanded ? (
                          <ChevronUp className="h-4 w-4" />
                        ) : (
                          <ChevronDown className="h-4 w-4" />
                        )}
                      </button>
                    </div>

                    {isExpanded && (
                      <div className="mt-3 pt-3 border-t border-slate-800/80 space-y-2">
                        {p.metadata?.subsection && (
                          <p className="text-xs text-indigo-400 font-medium">
                            Sous-section : {p.metadata.subsection}
                          </p>
                        )}
                        <pre className="max-h-48 overflow-y-auto whitespace-pre-wrap font-sans text-xs text-slate-300 bg-slate-950/50 p-3 rounded-xl border border-slate-850">
                          {p.text || "Aucun contenu textuel extrait sur cette page."}
                        </pre>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Technical Storage & Multi-Tenant Info */}
        <div className="mt-8 rounded-2xl border border-slate-800 bg-slate-900/20 p-4">
          <div className="flex items-center gap-2 text-slate-400 mb-2">
            <Shield className="h-4 w-4 text-indigo-400" />
            <span className="text-xs font-semibold text-slate-300">
              Sécurité & Isolation Multi-Tenant
            </span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
            <div className="truncate">
              <span className="text-slate-500">ID Unique :</span>{" "}
              <span className="font-mono text-slate-300">{doc.id}</span>
            </div>
            <div className="truncate">
              <span className="text-slate-500">Organisation :</span>{" "}
              <span className="font-mono text-slate-300">{doc.organization}</span>
            </div>
            {doc.storage_key && (
              <div className="md:col-span-2 truncate">
                <span className="text-slate-500">Clé de stockage (S3/MinIO) :</span>{" "}
                <span className="font-mono text-slate-400">{doc.storage_key}</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
