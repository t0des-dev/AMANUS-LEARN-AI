"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  GraduationCap,
  PlusCircle,
  MessageSquare,
  Sparkles,
  FileText,
  Search,
  Trash2,
  Clock,
  ChevronRight,
  BookOpen,
} from "lucide-react";
import { ProtectedRoute } from "../../components/auth/ProtectedRoute";
import { useAuth } from "../../components/auth/AuthProvider";
import { useOrganization } from "../../components/organization/OrganizationContext";
import { useTranslation } from "../../lib/i18n/LanguageContext";
import { chatService } from "../../services/chatService";
import { documentService } from "../../services/documentService";
import { ChatSession, PedagogicalCommandCode } from "../../types/chat";
import { DocumentItem } from "../../types/document";
import { SuggestedPrompt } from "../../components/chat/SuggestedPrompt";

function ChatHubContent() {
  const router = useRouter();
  const { token } = useAuth();
  const { currentOrg } = useOrganization();
  const { t } = useTranslation();

  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);

  const fetchSessions = useCallback(async () => {
    if (!token) return;
    try {
      const data = await chatService.listSessions(token, {
        organization_id: currentOrg?.id || undefined,
      });
      setSessions(data);
    } catch {
      // Handled
    } finally {
      setIsLoading(false);
    }
  }, [token, currentOrg]);

  const fetchDocuments = useCallback(async () => {
    if (!token) return;
    try {
      const data = await documentService.list(token, {
        organization_id: currentOrg?.id || undefined,
      });
      setDocuments(data.filter((d) => d.status === "READY" || d.status === "COMPLETED"));
    } catch {
      // Handled
    }
  }, [token, currentOrg]);

  useEffect(() => {
    fetchSessions();
    fetchDocuments();
  }, [fetchSessions, fetchDocuments]);

  const handleCreateSession = async (
    initialPrompt?: string,
    command?: PedagogicalCommandCode
  ) => {
    if (!token || isCreating) return;
    setIsCreating(true);

    try {
      const newSession = await chatService.createSession(token, {
        organization_id: currentOrg?.id,
        document_id: selectedDocId || undefined,
        title: initialPrompt ? initialPrompt.slice(0, 40) : "Nouvelle session pédagogique",
        initial_message: initialPrompt,
      });

      router.push(`/chat/${newSession.id}`);
    } catch (err: any) {
      alert(err.message || "Impossible de démarrer la session.");
      setIsCreating(false);
    }
  };

  const handleDeleteSession = async (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    e.preventDefault();
    if (!token) return;
    if (!confirm("Voulez-vous vraiment supprimer cette conversation ?")) return;

    try {
      await chatService.deleteSession(token, sessionId);
      setSessions((prev) => prev.filter((s) => s.id !== sessionId));
    } catch (err: any) {
      alert(err.message || "Erreur de suppression.");
    }
  };

  const filteredSessions = sessions.filter((s) =>
    s.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
      {/* Top Banner */}
      <div className="mb-6 flex flex-col md:flex-row md:items-center justify-between gap-4 rounded-2xl border border-indigo-500/20 bg-gradient-to-r from-indigo-950/40 via-slate-900 to-slate-950 p-6 shadow-xl">
        <div className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-tr from-indigo-600 to-violet-500 text-white shadow-lg shadow-indigo-500/30">
            <GraduationCap className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              {t("chat.title")}
            </h1>
            <p className="text-xs sm:text-sm text-slate-400">
              {t("chat.subtitle")}
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={() => handleCreateSession()}
          disabled={isCreating}
          className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-600/20 transition hover:from-indigo-500 hover:to-violet-500 disabled:opacity-50"
        >
          <PlusCircle className="h-4 w-4" />
          <span>{t("chat.newChat")}</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Sidebar: Session List */}
        <div className="lg:col-span-4 flex flex-col rounded-2xl border border-slate-800 bg-slate-950/60 p-4 shadow-md backdrop-blur-md">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-bold text-slate-200 flex items-center gap-2">
              <MessageSquare className="h-4 w-4 text-indigo-400" />
              <span>Vos conversations ({sessions.length})</span>
            </h2>
          </div>

          {/* Search */}
          <div className="relative mb-3">
            <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-slate-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Rechercher une session..."
              className="w-full rounded-xl border border-slate-800 bg-slate-900/90 py-2 pl-9 pr-3 text-xs text-slate-200 placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
            />
          </div>

          {/* Document filter picker */}
          <div className="mb-4">
            <label className="text-[11px] font-medium text-slate-400 block mb-1">
              Document d&apos;ancrage pour nouvelle session :
            </label>
            <select
              value={selectedDocId}
              onChange={(e) => setSelectedDocId(e.target.value)}
              className="w-full rounded-xl border border-slate-800 bg-slate-900 py-1.5 px-2.5 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
            >
              <option value="">Tous les documents de l&apos;organisation</option>
              {documents.map((doc) => (
                <option key={doc.id} value={doc.id}>
                  {doc.title}
                </option>
              ))}
            </select>
          </div>

          {/* Session Cards list */}
          <div className="space-y-2 overflow-y-auto max-h-[500px] pr-1">
            {isLoading ? (
              <div className="p-4 text-center text-xs text-slate-500">
                Chargement des conversations...
              </div>
            ) : filteredSessions.length === 0 ? (
              <div className="p-6 text-center text-xs text-slate-500 border border-dashed border-slate-800 rounded-xl">
                Aucune conversation trouvée.
              </div>
            ) : (
              filteredSessions.map((s) => (
                <Link
                  key={s.id}
                  href={`/chat/${s.id}`}
                  className="group relative flex flex-col rounded-xl border border-slate-800/80 bg-slate-900/40 p-3 transition hover:border-indigo-500/40 hover:bg-slate-900/90"
                >
                  <div className="flex items-start justify-between gap-2">
                    <span className="font-semibold text-xs text-slate-200 group-hover:text-indigo-300 transition line-clamp-1">
                      {s.title}
                    </span>
                    <button
                      type="button"
                      onClick={(e) => handleDeleteSession(e, s.id)}
                      className="opacity-0 group-hover:opacity-100 text-slate-500 hover:text-red-400 p-1 transition"
                      title="Supprimer"
                    >
                      <Trash2 className="h-3 w-3" />
                    </button>
                  </div>

                  {s.last_message && (
                    <p className="mt-1 text-[11px] text-slate-400 line-clamp-1">
                      {s.last_message.content}
                    </p>
                  )}

                  <div className="mt-2 flex items-center justify-between text-[10px] text-slate-500">
                    <span className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {new Date(s.updated_at).toLocaleDateString([], {
                        day: "2-digit",
                        month: "short",
                      })}
                    </span>
                    {s.document && (
                      <span className="rounded bg-indigo-950/60 border border-indigo-800/40 px-1.5 py-0.5 text-indigo-300 truncate max-w-[120px]">
                        {s.document.title}
                      </span>
                    )}
                  </div>
                </Link>
              ))
            )}
          </div>
        </div>

        {/* Right Main Area: Suggested prompts and Welcome */}
        <div className="lg:col-span-8 flex flex-col justify-between rounded-2xl border border-slate-800 bg-slate-950/60 p-6 shadow-md backdrop-blur-md">
          <div>
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-indigo-500/30 bg-indigo-950/30 px-3 py-1 text-xs text-indigo-300">
              <Sparkles className="h-3.5 w-3.5 text-indigo-400" />
              <span>Pédagogie active & RAG certifié sans hallucination</span>
            </div>

            <h2 className="text-xl sm:text-2xl font-bold text-white">
              Prêt à progresser avec votre Tuteur IA ?
            </h2>
            <p className="mt-2 text-sm text-slate-400 leading-relaxed max-w-2xl">
              Choisissez une commande pédagogique pour démarrer immédiatement une session d&apos;apprentissage ciblée.
              Chaque réponse est étayée par les sources précises de vos documents pédagogiques.
            </p>

            <div className="mt-8">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">
                Commandes Pédagogiques Clés en Main
              </h3>
              <SuggestedPrompt
                layout="grid"
                onSelectPrompt={(prompt, cmd) => handleCreateSession(prompt, cmd)}
              />
            </div>
          </div>

          <div className="mt-8 pt-6 border-t border-slate-800/80 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-400 gap-3">
            <div className="flex items-center gap-2">
              <BookOpen className="h-4 w-4 text-indigo-400" />
              <span>Isolation stricte : seules vos ressources documentaires sont exploitées.</span>
            </div>
            <button
              type="button"
              onClick={() => handleCreateSession()}
              className="text-indigo-400 hover:text-indigo-300 font-semibold flex items-center gap-1"
            >
              Démarrer sans prompt initial <ChevronRight className="h-3 w-3" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ChatPage() {
  return (
    <ProtectedRoute>
      <ChatHubContent />
    </ProtectedRoute>
  );
}
