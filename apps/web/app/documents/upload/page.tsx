"use client";

import React from "react";
import Link from "next/link";
import { ArrowLeft, UploadCloud } from "lucide-react";
import { ProtectedRoute } from "../../../components/auth/ProtectedRoute";
import { DocumentUploader } from "../../../features/document/DocumentUploader";

function DocumentUploadPageContent() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-6">
        <Link
          href="/documents"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-400 transition hover:text-white mb-4"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Retour aux documents</span>
        </Link>
      </div>

      <div className="flex justify-center">
        <DocumentUploader redirectOnSuccess={true} />
      </div>
    </div>
  );
}

export default function DocumentUploadPage() {
  return (
    <ProtectedRoute>
      <DocumentUploadPageContent />
    </ProtectedRoute>
  );
}
