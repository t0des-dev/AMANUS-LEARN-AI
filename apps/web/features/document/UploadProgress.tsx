"use client";

import React from "react";
import { FileUp, CheckCircle, AlertCircle } from "lucide-react";

interface UploadProgressProps {
  fileName: string;
  fileSizeHuman?: string;
  progress: number; // 0 to 100
  isError?: boolean;
  errorMessage?: string;
}

export function UploadProgress({
  fileName,
  fileSizeHuman,
  progress,
  isError = false,
  errorMessage,
}: UploadProgressProps) {
  const isComplete = progress >= 100 && !isError;

  return (
    <div className="w-full rounded-2xl border border-slate-800 bg-slate-900/80 p-4 shadow-xl backdrop-blur-xl">
      <div className="flex items-center justify-between gap-3 mb-2">
        <div className="flex items-center gap-2.5 truncate">
          <div
            className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl ${
              isError
                ? "bg-rose-500/10 text-rose-400"
                : isComplete
                ? "bg-emerald-500/10 text-emerald-400"
                : "bg-indigo-500/10 text-indigo-400 animate-pulse"
            }`}
          >
            {isError ? (
              <AlertCircle className="h-4 w-4" />
            ) : isComplete ? (
              <CheckCircle className="h-4 w-4" />
            ) : (
              <FileUp className="h-4 w-4" />
            )}
          </div>
          <div className="truncate">
            <p className="truncate text-xs font-semibold text-white">
              {fileName}
            </p>
            <p className="text-[11px] text-slate-400">
              {fileSizeHuman || "Téléversement en cours..."}
            </p>
          </div>
        </div>

        <span
          className={`text-xs font-bold ${
            isError
              ? "text-rose-400"
              : isComplete
              ? "text-emerald-400"
              : "text-indigo-400"
          }`}
        >
          {isError ? "Échec" : `${progress}%`}
        </span>
      </div>

      {/* Progress Track */}
      <div className="relative h-2 w-full overflow-hidden rounded-full bg-slate-800">
        <div
          className={`h-full rounded-full transition-all duration-300 ease-out ${
            isError
              ? "bg-rose-500"
              : isComplete
              ? "bg-gradient-to-r from-emerald-500 to-teal-400"
              : "bg-gradient-to-r from-indigo-500 to-violet-500"
          }`}
          style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
        />
      </div>

      {errorMessage && (
        <p className="mt-2 text-xs text-rose-400 flex items-center gap-1.5">
          <AlertCircle className="h-3.5 w-3.5 shrink-0" />
          <span>{errorMessage}</span>
        </p>
      )}

      {isComplete && !errorMessage && (
        <p className="mt-2 text-[11px] text-emerald-400 font-medium">
          Fichier transféré avec succès dans le coffre-fort de l'organisation.
        </p>
      )}
    </div>
  );
}
