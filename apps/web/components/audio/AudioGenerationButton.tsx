"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";
import {
  Headphones,
  Sparkles,
  Loader2,
  X,
  Play,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
} from "lucide-react";
import { AudioContent } from "../../types/audio";
import { audioService } from "../../services/audioService";
import { useAuth } from "../auth/AuthProvider";
import { VoiceSelector } from "./VoiceSelector";
import { AudioPlayer } from "./AudioPlayer";

interface AudioGenerationButtonProps {
  sectionId: string;
  sectionTitle?: string;
  onAudioGenerated?: (audio: AudioContent) => void;
  className?: string;
}

export function AudioGenerationButton({
  sectionId,
  sectionTitle,
  onAudioGenerated,
  className = "",
}: AudioGenerationButtonProps) {
  const { token } = useAuth();

  const [audio, setAudio] = useState<AudioContent | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showVoiceModal, setShowVoiceModal] = useState(false);
  const [showPlayerModal, setShowPlayerModal] = useState(false);

  // Selected voice state
  const [selectedVoiceId, setSelectedVoiceId] = useState("pierre");
  const [selectedProvider, setSelectedProvider] = useState("mock");
  const [selectedLanguage, setSelectedLanguage] = useState("fr");

  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const fetchAudioStatus = useCallback(async () => {
    if (!token || !sectionId) return;
    try {
      const data = await audioService.getSectionAudio(token, sectionId);
      setAudio(data);
      if (data && onAudioGenerated) {
        onAudioGenerated(data);
      }
      return data;
    } catch {
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [token, sectionId, onAudioGenerated]);

  useEffect(() => {
    fetchAudioStatus();
  }, [fetchAudioStatus]);

  // Polling when PENDING or PROCESSING
  useEffect(() => {
    if (audio?.status === "PENDING" || audio?.status === "PROCESSING") {
      pollIntervalRef.current = setInterval(async () => {
        const updated = await fetchAudioStatus();
        if (updated?.status === "COMPLETED" || updated?.status === "FAILED") {
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
          }
        }
      }, 2500);
    } else {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    }

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, [audio?.status, fetchAudioStatus]);

  const handleStartGeneration = async () => {
    if (!token || isSubmitting) return;
    setIsSubmitting(true);

    try {
      const created = await audioService.requestSectionAudio(token, sectionId, {
        voice_id: selectedVoiceId,
        voice_provider: selectedProvider,
        language: selectedLanguage,
      });

      setAudio(created);
      setShowVoiceModal(false);
      if (onAudioGenerated) {
        onAudioGenerated(created);
      }
    } catch (err: any) {
      alert(err.message || "Erreur lors de la demande de génération audio.");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center gap-1.5 text-xs text-slate-500 py-1">
        <Loader2 className="h-3.5 w-3.5 animate-spin" />
        <span>Vérification audio...</span>
      </div>
    );
  }

  // State: COMPLETED
  if (audio && audio.status === "COMPLETED") {
    const mins = Math.floor(audio.duration / 60);
    const secs = Math.floor(audio.duration % 60);
    const formattedDuration = `${mins}:${secs.toString().padStart(2, "0")}`;

    return (
      <div className={`flex flex-col gap-3 ${className}`}>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setShowPlayerModal(!showPlayerModal)}
            className="group flex items-center gap-2 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 px-3.5 py-1.5 text-xs font-semibold text-white shadow-md shadow-indigo-600/20 transition hover:from-indigo-500 hover:to-violet-500"
          >
            <Headphones className="h-4 w-4" />
            <span>{showPlayerModal ? "Masquer le lecteur" : "Écouter la leçon"}</span>
            <span className="rounded bg-indigo-950/70 border border-indigo-400/30 px-1.5 py-0.5 text-[10px] text-indigo-200">
              {formattedDuration}
            </span>
          </button>

          <button
            type="button"
            onClick={() => setShowVoiceModal(true)}
            className="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-800 bg-slate-900 text-slate-400 hover:text-white transition"
            title="Régénérer avec une autre voix"
          >
            <RefreshCw className="h-3.5 w-3.5" />
          </button>
        </div>

        {/* Inline player view if toggled */}
        {showPlayerModal && (
          <AudioPlayer
            audio={audio}
            title={sectionTitle}
            autoPlay={true}
            className="mt-2"
          />
        )}

        {/* Regenerate modal */}
        {showVoiceModal && renderVoiceModal()}
      </div>
    );
  }

  // State: PROCESSING / PENDING
  if (audio && (audio.status === "PENDING" || audio.status === "PROCESSING")) {
    return (
      <div
        className={`flex items-center gap-2 rounded-xl border border-indigo-500/30 bg-indigo-950/30 px-3.5 py-1.5 text-xs text-indigo-300 shadow-sm ${className}`}
      >
        <Loader2 className="h-4 w-4 animate-spin text-indigo-400" />
        <span className="font-medium">
          {audio.status === "PROCESSING"
            ? "Génération audio en cours..."
            : "En attente du worker Celery..."}
        </span>
      </div>
    );
  }

  // State: FAILED or NOT GENERATED YET
  return (
    <>
      <div className={`flex items-center gap-2 ${className}`}>
        <button
          type="button"
          onClick={() => setShowVoiceModal(true)}
          className="group flex items-center gap-2 rounded-xl border border-indigo-500/40 bg-slate-900/90 px-3.5 py-1.5 text-xs font-semibold text-indigo-300 shadow-sm transition hover:border-indigo-400 hover:bg-indigo-950/40 hover:text-white"
        >
          <Sparkles className="h-3.5 w-3.5 text-indigo-400 transition group-hover:scale-110" />
          <span>
            {audio?.status === "FAILED"
              ? "Échec de génération (Réessayer)"
              : "Générer la version audio"}
          </span>
        </button>

        {audio?.status === "FAILED" && audio.error_message && (
          <span
            className="text-[11px] text-red-400 flex items-center gap-1"
            title={audio.error_message}
          >
            <AlertCircle className="h-3.5 w-3.5 shrink-0" />
            <span className="max-w-[180px] truncate">{audio.error_message}</span>
          </span>
        )}
      </div>

      {showVoiceModal && renderVoiceModal()}
    </>
  );

  function renderVoiceModal() {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-sm">
        <div className="relative w-full max-w-lg rounded-2xl border border-slate-800 bg-slate-900 p-5 shadow-2xl">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 text-white shadow-md shadow-indigo-500/20">
                <Headphones className="h-4 w-4" />
              </div>
              <span className="font-bold text-sm text-white">
                Générer la version audio TTS
              </span>
            </div>

            <button
              type="button"
              onClick={() => setShowVoiceModal(false)}
              className="text-slate-400 hover:text-white p-1 rounded-lg"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <VoiceSelector
            selectedVoiceId={selectedVoiceId}
            selectedProvider={selectedProvider}
            onSelectVoice={(vId, prov) => {
              setSelectedVoiceId(vId);
              setSelectedProvider(prov);
            }}
          />

          <div className="mt-5 border-t border-slate-800 pt-3 flex items-center justify-between">
            <span className="text-[11px] text-slate-400">
              Traitement asynchrone sécurisé avec Celery.
            </span>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setShowVoiceModal(false)}
                className="rounded-xl border border-slate-800 px-3 py-1.5 text-xs font-semibold text-slate-300 hover:bg-slate-800"
              >
                Annuler
              </button>
              <button
                type="button"
                onClick={handleStartGeneration}
                disabled={isSubmitting}
                className="inline-flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 px-4 py-1.5 text-xs font-semibold text-white shadow-md shadow-indigo-500/20 transition hover:from-indigo-500 hover:to-violet-500 disabled:opacity-50"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    <span>Lancement...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="h-3.5 w-3.5" />
                    <span>Lancer la synthèse</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }
}
