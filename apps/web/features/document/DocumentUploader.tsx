"use client";

import React, { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  UploadCloud,
  File,
  X,
  AlertCircle,
  CheckCircle,
  FileText,
  Presentation,
  FileCode,
  ShieldCheck,
} from "lucide-react";
import { useAuth } from "../../components/auth/AuthProvider";
import { useOrganization } from "../../components/organization/OrganizationContext";
import { documentService } from "../../services/documentService";
import { DocumentItem } from "../../types/document";
import { UploadProgress } from "./UploadProgress";

const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB
const ACCEPTED_EXTENSIONS = [".pdf", ".docx", ".pptx", ".txt"];

interface DocumentUploaderProps {
  onSuccess?: (newDoc: DocumentItem) => void;
  redirectOnSuccess?: boolean;
}

export function DocumentUploader({
  onSuccess,
  redirectOnSuccess = true,
}: DocumentUploaderProps) {
  const { token } = useAuth();
  const { currentOrg, organizations } = useOrganization();
  const router = useRouter();

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedOrgId, setSelectedOrgId] = useState<string>(
    currentOrg?.id || (organizations[0]?.id ?? "")
  );
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [language, setLanguage] = useState("fr");

  const [isDragging, setIsDragging] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [isUploading, setIsUploading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isComplete, setIsComplete] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateAndSetFile = (file: File) => {
    setErrorMessage(null);
    const extension = "." + file.name.split(".").pop()?.toLowerCase();

    if (!ACCEPTED_EXTENSIONS.includes(extension)) {
      setErrorMessage(
        `Format '${extension}' non supporté. Veuillez sélectionner un fichier ${ACCEPTED_EXTENSIONS.join(
          ", "
        )}.`
      );
      return false;
    }

    if (file.size > MAX_FILE_SIZE) {
      setErrorMessage(
        `Le fichier dépasse la taille maximale autorisée de 50 Mo (${(
          file.size /
          (1024 * 1024)
        ).toFixed(1)} Mo).`
      );
      return false;
    }

    setSelectedFile(file);
    if (!title) {
      // Suggest clean title
      const cleanStem = file.name
        .substring(0, file.name.lastIndexOf("."))
        .replace(/[_-]/g, " ");
      setTitle(cleanStem.charAt(0).toUpperCase() + cleanStem.slice(1));
    }
    return true;
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setErrorMessage("Veuillez sélectionner un document.");
      return;
    }
    if (!selectedOrgId) {
      setErrorMessage("Veuillez sélectionner une organisation pour ce document.");
      return;
    }
    if (!token) {
      setErrorMessage("Session expirée. Veuillez vous reconnecter.");
      return;
    }

    setIsUploading(true);
    setUploadProgress(10);
    setErrorMessage(null);

    try {
      const createdDoc = await documentService.upload(
        token,
        {
          file: selectedFile,
          organization_id: selectedOrgId,
          title: title.trim() || undefined,
          description: description.trim() || undefined,
          language,
        },
        (percent) => {
          setUploadProgress(percent);
        }
      );

      setUploadProgress(100);
      setIsComplete(true);

      if (onSuccess) {
        onSuccess(createdDoc);
      }

      if (redirectOnSuccess) {
        setTimeout(() => {
          router.push(`/documents/${createdDoc.id}`);
        }, 800);
      }
    } catch (err: any) {
      setErrorMessage(err.message || "Échec du téléversement du document.");
      setIsUploading(false);
    }
  };

  const clearSelectedFile = () => {
    setSelectedFile(null);
    setErrorMessage(null);
    setUploadProgress(0);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <div className="w-full max-w-2xl rounded-3xl border border-slate-800 bg-slate-950/80 p-6 md:p-8 shadow-2xl backdrop-blur-xl">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white">
            Importer un document
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Formats acceptés : PDF, DOCX, PPTX et TXT (jusqu'à 50 Mo).
          </p>
        </div>
        <div className="flex items-center gap-1.5 rounded-full border border-indigo-500/20 bg-indigo-500/10 px-3 py-1 text-xs text-indigo-300">
          <ShieldCheck className="h-3.5 w-3.5 text-indigo-400" />
          <span>Isolé par organisation</span>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Organization Select */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
            Organisation de destination *
          </label>
          <select
            value={selectedOrgId}
            onChange={(e) => setSelectedOrgId(e.target.value)}
            disabled={isUploading}
            className="w-full rounded-xl border border-slate-800 bg-slate-900 px-4 py-2.5 text-sm text-white transition focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:opacity-50"
          >
            {organizations.length === 0 ? (
              <option value="">Aucune organisation disponible</option>
            ) : (
              organizations.map((org) => (
                <option key={org.id} value={org.id}>
                  {org.name} ({org.user_role || "MEMBRE"})
                </option>
              ))
            )}
          </select>
        </div>

        {/* Drag and Drop Box */}
        {!selectedFile ? (
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`cursor-pointer rounded-2xl border-2 border-dashed p-8 text-center transition-all duration-300 ${
              isDragging
                ? "border-indigo-500 bg-indigo-500/10 scale-[1.01]"
                : "border-slate-800 bg-slate-900/40 hover:border-slate-700 hover:bg-slate-900/70"
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx,.pptx,.txt"
              onChange={handleFileChange}
              className="hidden"
            />
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-600/10 text-indigo-400 border border-indigo-500/20 shadow-lg mb-4">
              <UploadCloud className="h-7 w-7" />
            </div>

            <p className="text-sm font-semibold text-white">
              Glissez et déposez votre fichier ici, ou{" "}
              <span className="text-indigo-400 hover:underline">parcourez</span>
            </p>
            <p className="mt-1 text-xs text-slate-500">
              PDF, Word (.docx), PowerPoint (.pptx) ou Texte brut (.txt)
            </p>

            <div className="mt-4 flex items-center justify-center gap-4 text-[11px] text-slate-400">
              <span className="flex items-center gap-1">
                <FileText className="h-3.5 w-3.5 text-rose-400" /> PDF
              </span>
              <span className="flex items-center gap-1">
                <FileText className="h-3.5 w-3.5 text-blue-400" /> DOCX
              </span>
              <span className="flex items-center gap-1">
                <Presentation className="h-3.5 w-3.5 text-amber-400" /> PPTX
              </span>
              <span className="flex items-center gap-1">
                <FileCode className="h-3.5 w-3.5 text-emerald-400" /> TXT
              </span>
            </div>
          </div>
        ) : (
          <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3 truncate">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-indigo-600/20 text-indigo-400">
                  <File className="h-5 w-5" />
                </div>
                <div className="truncate">
                  <p className="truncate text-sm font-medium text-white">
                    {selectedFile.name}
                  </p>
                  <p className="text-xs text-slate-400">
                    {(selectedFile.size / (1024 * 1024)).toFixed(2)} Mo
                  </p>
                </div>
              </div>

              {!isUploading && (
                <button
                  type="button"
                  onClick={clearSelectedFile}
                  className="rounded-lg p-1.5 text-slate-400 transition hover:bg-slate-800 hover:text-white"
                  title="Changer de fichier"
                >
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>

            {isUploading && (
              <div className="mt-4">
                <UploadProgress
                  fileName={selectedFile.name}
                  fileSizeHuman={`${(selectedFile.size / (1024 * 1024)).toFixed(
                    2
                  )} Mo`}
                  progress={uploadProgress}
                  isError={!!errorMessage}
                  errorMessage={errorMessage || undefined}
                />
              </div>
            )}
          </div>
        )}

        {/* Metadata Inputs */}
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Titre du document
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Ex: Manuel de Data Science - Chapitre 1"
              disabled={isUploading}
              className="w-full rounded-xl border border-slate-800 bg-slate-900 px-4 py-2.5 text-sm text-white placeholder-slate-500 transition focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:opacity-50"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Description (optionnelle)
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
              placeholder="Brève description ou objectifs pédagogiques..."
              disabled={isUploading}
              className="w-full rounded-xl border border-slate-800 bg-slate-900 px-4 py-2 text-sm text-white placeholder-slate-500 transition focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:opacity-50"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Langue principale
            </label>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              disabled={isUploading}
              className="w-full rounded-xl border border-slate-800 bg-slate-900 px-4 py-2 text-sm text-white transition focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:opacity-50"
            >
              <option value="fr">Français (FR)</option>
              <option value="ar">العربية - Arabe (AR)</option>
              <option value="en">English - Anglais (EN)</option>
              <option value="es">Español - Espagnol (ES)</option>
              <option value="de">Deutsch - Allemand (DE)</option>
            </select>
          </div>
        </div>

        {errorMessage && !isUploading && (
          <div className="rounded-xl border border-rose-500/20 bg-rose-500/10 p-3 text-xs text-rose-400 flex items-center gap-2">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          disabled={!selectedFile || isUploading || !selectedOrgId}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-600/30 transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isUploading ? (
            <span>Téléversement ({uploadProgress}%)...</span>
          ) : isComplete ? (
            <span className="flex items-center gap-1.5 text-emerald-300">
              <CheckCircle className="h-4 w-4" /> Importé avec succès
            </span>
          ) : (
            <span className="flex items-center gap-1.5">
              <UploadCloud className="h-4 w-4" /> Importer le document
            </span>
          )}
        </button>
      </form>
    </div>
  );
}
