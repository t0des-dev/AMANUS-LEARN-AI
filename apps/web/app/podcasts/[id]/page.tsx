"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  Radio,
  Sparkles,
  AlertCircle,
  Loader2,
  FileText,
  BookOpen,
} from "lucide-react";
import { ProtectedRoute } from "../../../components/auth/ProtectedRoute";
import { useAuth } from "../../../components/auth/AuthProvider";
import { podcastService } from "../../../services/podcastService";
import { PodcastEpisodeItem } from "../../../types/podcast";
import { PodcastPlayer } from "../../../features/podcast/PodcastPlayer";
import { CitationViewerDrawer } from "../../../components/citation/CitationViewerDrawer";

function PodcastEpisodeDetailPage() {
  const params = useParams();
  const podcastId = params?.id as string;
  const router = useRouter();
  const { token } = useAuth();

  const [episode, setEpisode] = useState<PodcastEpisodeItem | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Selected citation for interactive viewer drawer
  const [selectedCitation, setSelectedCitation] = useState<number | null>(null);
  const [isCitationDrawerOpen, setIsCitationDrawerOpen] = useState(false);

  const fetchPodcast = useCallback(async () => {
    if (!token || !podcastId) return;
    setIsLoading(true);
    setError(null);
    try {
      const data = await podcastService.getPodcast(token, podcastId);
      setEpisode(data);
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Impossible de charger l'épisode de podcast."
      );
    } finally {
      setIsLoading(false);
    }
  }, [token, podcastId]);

  useEffect(() => {
    fetchPodcast();
  }, [fetchPodcast]);

  const handleCitationClick = (num: number) => {
    setSelectedCitation(num);
    setIsCitationDrawerOpen(true);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 pb-16">
      {/* Top Navbar */}
      <div className="border-b border-slate-800 bg-slate-900/60 backdrop-blur-md sticky top-0 z-30">
        <div className="mx-auto max-w-5xl px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => router.back()}
              className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-400 hover:text-white transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              Retour
            </button>
            <div className="h-4 w-px bg-slate-800" />
            <div className="flex items-center gap-2">
              <Radio className="w-4 h-4 text-indigo-400" />
              <span className="text-sm font-semibold text-white truncate max-w-xs sm:max-w-md">
                {episode?.title || "Épisode Podcast"}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {episode?.course_id && (
              <Link
                href={`/courses/${episode.course_id}`}
                className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
              >
                <BookOpen className="w-3.5 h-3.5" />
                Voir le cours
              </Link>
            )}
            {episode?.document_id && (
              <Link
                href={`/documents/${episode.document_id}`}
                className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1"
              >
                <FileText className="w-3.5 h-3.5" />
                Document source
              </Link>
            )}
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-5xl px-4 py-8">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-24 text-slate-400">
            <Loader2 className="w-8 h-8 animate-spin text-indigo-500 mb-3" />
            <p className="text-sm">Chargement du podcast pédagogique...</p>
          </div>
        ) : error ? (
          <div className="rounded-2xl border border-rose-500/20 bg-rose-500/10 p-6 text-center max-w-md mx-auto">
            <AlertCircle className="w-8 h-8 text-rose-400 mx-auto mb-2" />
            <h3 className="text-sm font-semibold text-white">Erreur de chargement</h3>
            <p className="text-xs text-rose-200 mt-1">{error}</p>
            <button
              onClick={() => fetchPodcast()}
              className="mt-4 px-4 py-2 bg-rose-500/20 hover:bg-rose-500/30 text-rose-200 text-xs font-medium rounded-lg transition-colors"
            >
              Réessayer
            </button>
          </div>
        ) : episode ? (
          <>
            <PodcastPlayer
              episode={episode}
              onCitationClick={handleCitationClick}
            />

            {/* Citation Viewer Drawer (Phase 6) */}
            {episode.document_id && (
              <CitationViewerDrawer
                isOpen={isCitationDrawerOpen}
                onClose={() => setIsCitationDrawerOpen(false)}
                documentId={episode.document_id}
                highlightIndex={selectedCitation !== null ? selectedCitation - 1 : undefined}
              />
            )}
          </>
        ) : null}
      </div>
    </div>
  );
}

export default function PodcastPage() {
  return (
    <ProtectedRoute>
      <PodcastEpisodeDetailPage />
    </ProtectedRoute>
  );
}
