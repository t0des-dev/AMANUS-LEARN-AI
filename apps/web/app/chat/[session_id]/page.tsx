"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, AlertCircle } from "lucide-react";
import { ProtectedRoute } from "../../../components/auth/ProtectedRoute";
import { useAuth } from "../../../components/auth/AuthProvider";
import { chatService } from "../../../services/chatService";
import { ChatSession } from "../../../types/chat";
import { ChatWindow } from "../../../components/chat/ChatWindow";

function ChatSessionPageContent() {
  const params = useParams();
  const router = useRouter();
  const { token } = useAuth();
  const sessionId = Array.isArray(params.session_id)
    ? params.session_id[0]
    : (params.session_id as string);

  const [session, setSession] = useState<ChatSession | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSession = useCallback(async () => {
    if (!token || !sessionId) return;
    setIsLoading(true);
    setError(null);

    try {
      const data = await chatService.getSession(token, sessionId);
      setSession(data);
    } catch (err: any) {
      setError(
        err.message || "Impossible de charger la conversation demandée."
      );
    } finally {
      setIsLoading(false);
    }
  }, [token, sessionId]);

  useEffect(() => {
    fetchSession();
  }, [fetchSession]);

  return (
    <div className="mx-auto max-w-6xl px-4 py-4 sm:px-6 lg:px-8 h-[calc(100vh-5rem)] flex flex-col">
      {isLoading ? (
        <div className="flex h-full items-center justify-center">
          <div className="flex flex-col items-center gap-3 text-slate-400 text-sm">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
            <span>Chargement de la session pédagogique...</span>
          </div>
        </div>
      ) : error || !session ? (
        <div className="flex h-full flex-col items-center justify-center text-center p-6">
          <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-red-950/40 border border-red-500/30 text-red-400">
            <AlertCircle className="h-6 w-6" />
          </div>
          <h2 className="text-lg font-bold text-slate-100">Session introuvable</h2>
          <p className="mt-1 max-w-md text-xs sm:text-sm text-slate-400">
            {error || "Cette session n'existe pas ou vous n'y avez pas accès."}
          </p>
          <Link
            href="/chat"
            className="mt-6 inline-flex items-center gap-2 rounded-xl bg-slate-800 px-4 py-2 text-xs font-semibold text-white transition hover:bg-slate-700"
          >
            <ArrowLeft className="h-4 w-4" />
            <span>Retour aux conversations</span>
          </Link>
        </div>
      ) : (
        <ChatWindow
          session={session}
          token={token!}
          onSessionUpdated={(updated) => setSession(updated)}
          className="flex-1"
        />
      )}
    </div>
  );
}

export default function ChatSessionPage() {
  return (
    <ProtectedRoute>
      <ChatSessionPageContent />
    </ProtectedRoute>
  );
}
