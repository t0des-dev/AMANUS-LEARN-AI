"use client";

import React from "react";
import {
  UploadCloud,
  Loader2,
  CheckCircle2,
  AlertTriangle,
  Archive,
  Scan,
  Layers,
  Scissors,
  FileText,
} from "lucide-react";
import {
  DocumentProcessingStage,
  DocumentStatus as StatusType,
} from "../../types/document";

interface DocumentStatusProps {
  status: StatusType | string;
  stage?: DocumentProcessingStage | string;
  size?: "sm" | "md" | "lg";
  showIcon?: boolean;
}

export function DocumentStatus({
  status,
  stage,
  size = "md",
  showIcon = true,
}: DocumentStatusProps) {
  // Determine display key
  const effectiveKey = (stage || status).toUpperCase();

  const config: Record<
    string,
    {
      label: string;
      icon: React.ElementType;
      bg: string;
      dot: string;
      animateIcon?: string;
    }
  > = {
    UPLOADING: {
      label: "Uploading",
      icon: UploadCloud,
      bg: "bg-indigo-500/10 text-indigo-400 border-indigo-500/20",
      dot: "bg-indigo-400",
      animateIcon: "animate-pulse",
    },
    UPLOADED: {
      label: "Uploadé",
      icon: UploadCloud,
      bg: "bg-indigo-500/10 text-indigo-400 border-indigo-500/20",
      dot: "bg-indigo-400",
    },
    EXTRACTING: {
      label: "Extracting",
      icon: FileText,
      bg: "bg-sky-500/10 text-sky-300 border-sky-500/20",
      dot: "bg-sky-400",
      animateIcon: "animate-spin",
    },
    OCR: {
      label: "OCR",
      icon: Scan,
      bg: "bg-violet-500/10 text-violet-300 border-violet-500/20",
      dot: "bg-violet-400",
      animateIcon: "animate-pulse",
    },
    STRUCTURING: {
      label: "Structuring",
      icon: Layers,
      bg: "bg-blue-500/10 text-blue-300 border-blue-500/20",
      dot: "bg-blue-400",
      animateIcon: "animate-pulse",
    },
    CHUNKING: {
      label: "Chunking",
      icon: Scissors,
      bg: "bg-amber-500/10 text-amber-300 border-amber-500/20",
      dot: "bg-amber-400",
      animateIcon: "animate-spin",
    },
    PROCESSING: {
      label: "En traitement",
      icon: Loader2,
      bg: "bg-amber-500/10 text-amber-300 border-amber-500/20",
      dot: "bg-amber-400",
      animateIcon: "animate-spin",
    },
    COMPLETED: {
      label: "Completed",
      icon: CheckCircle2,
      bg: "bg-emerald-500/10 text-emerald-300 border-emerald-500/20",
      dot: "bg-emerald-400",
    },
    READY: {
      label: "Completed",
      icon: CheckCircle2,
      bg: "bg-emerald-500/10 text-emerald-300 border-emerald-500/20",
      dot: "bg-emerald-400",
    },
    FAILED: {
      label: "Failed",
      icon: AlertTriangle,
      bg: "bg-rose-500/10 text-rose-400 border-rose-500/20",
      dot: "bg-rose-400",
    },
    ARCHIVED: {
      label: "Archivé",
      icon: Archive,
      bg: "bg-slate-700/20 text-slate-400 border-slate-700/40",
      dot: "bg-slate-400",
    },
  };

  const statusConfig = config[effectiveKey] || {
    label: stage || status,
    icon: UploadCloud,
    bg: "bg-slate-800 text-slate-300 border-slate-700",
    dot: "bg-slate-400",
  };

  const Icon = statusConfig.icon;

  const sizeClasses = {
    sm: "px-2 py-0.5 text-xs gap-1.5",
    md: "px-2.5 py-1 text-xs gap-2 font-medium",
    lg: "px-3.5 py-1.5 text-sm gap-2.5 font-medium",
  }[size];

  const iconSizes = {
    sm: "w-3 h-3",
    md: "w-3.5 h-3.5",
    lg: "w-4 h-4",
  }[size];

  return (
    <span
      className={`inline-flex items-center rounded-full border transition-colors ${statusConfig.bg} ${sizeClasses}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${statusConfig.dot}`} />
      {showIcon && (
        <Icon className={`${iconSizes} ${statusConfig.animateIcon || ""}`} />
      )}
      <span>{statusConfig.label}</span>
    </span>
  );
}
