"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Play,
  Pause,
  RotateCcw,
  Volume2,
  Sparkles,
  CheckCircle2,
  Mic,
  Clock,
  Radio,
  Share2,
  ChevronRight,
  BookOpen,
} from "lucide-react";
import { PodcastEpisodeItem, PodcastTurn } from "../../types/podcast";

interface PodcastPlayerProps {
  episode: PodcastEpisodeItem;
  onCitationClick?: (citationNum: number) => void;
}

export const PodcastPlayer: React.FC<PodcastPlayerProps> = ({
  episode,
  onCitationClick,
}) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [activeTurnIndex, setActiveTurnIndex] = useState(0);
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1);
  const turnRefs = useRef<(HTMLDivElement | null)[]>([]);

  const turns = episode.turns || [];

  // Speech simulation timer
  useEffect(() => {
    let timer: NodeJS.Timeout | null = null;
    if (isPlaying && turns.length > 0) {
      const currentTurn = turns[activeTurnIndex];
      // Estimate duration based on word count: ~130 words per minute
      const wordCount = currentTurn?.text.split(/\s+/).length || 20;
      const turnDurationMs = Math.max(3000, (wordCount / (130 * playbackSpeed)) * 60 * 1000);

      timer = setTimeout(() => {
        if (activeTurnIndex + 1 < turns.length) {
          setActiveTurnIndex((prev) => prev + 1);
        } else {
          setIsPlaying(false);
        }
      }, turnDurationMs);
    }

    return () => {
      if (timer) clearTimeout(timer);
    };
  }, [isPlaying, activeTurnIndex, turns, playbackSpeed]);

  // Auto-scroll active turn into view
  useEffect(() => {
    const el = turnRefs.current[activeTurnIndex];
    if (el && isPlaying) {
      el.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  }, [activeTurnIndex, isPlaying]);

  const handleTogglePlay = () => {
    if (activeTurnIndex >= turns.length - 1 && !isPlaying) {
      setActiveTurnIndex(0);
    }
    setIsPlaying((prev) => !prev);
  };

  const handleReset = () => {
    setIsPlaying(false);
    setActiveTurnIndex(0);
  };

  const renderTurnText = (text: string) => {
    // Highlight citations like [1], [2] as clickable pills
    const parts = text.split(/(\[\d+\])/g);
    return parts.map((part, i) => {
      const match = part.match(/\[(\d+)\]/);
      if (match) {
        const num = parseInt(match[1], 10);
        return (
          <button
            key={i}
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onCitationClick?.(num);
            }}
            className="inline-flex items-center px-1.5 py-0.5 mx-0.5 text-xs font-mono font-bold bg-indigo-500/20 hover:bg-indigo-500/40 text-indigo-300 rounded border border-indigo-500/40 transition-colors"
            title={`Voir la source originale [${num}]`}
          >
            [{num}]
          </button>
        );
      }
      return <span key={i}>{part}</span>;
    });
  };

  const progressPercent =
    turns.length > 0 ? Math.round(((activeTurnIndex + 1) / turns.length) * 100) : 0;

  return (
    <div className="space-y-6">
      {/* Studio Header Card */}
      <div className="relative overflow-hidden rounded-3xl border border-slate-800 bg-gradient-to-br from-slate-900 via-indigo-950/40 to-slate-900 p-6 sm:p-8 backdrop-blur-xl shadow-2xl">
        <div className="absolute top-0 right-0 -mt-12 -mr-12 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-3 max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
              <Radio className="w-3.5 h-3.5 animate-pulse text-indigo-400" />
              <span>Studio Podcast Pédagogique • 2 Voix</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              {episode.title}
            </h1>
            <p className="text-sm text-slate-300 leading-relaxed">
              {episode.description}
            </p>

            {/* Host badges */}
            <div className="flex flex-wrap items-center gap-3 pt-2">
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-300 text-xs font-medium">
                <span className="w-2 h-2 rounded-full bg-purple-400 animate-ping" />
                <span>Camille (Hôte • Cadrage & Relance)</span>
              </div>
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-300 text-xs font-medium">
                <span className="w-2 h-2 rounded-full bg-blue-400" />
                <span>Alex (Expert • Concepts & Sources)</span>
              </div>
            </div>
          </div>

          {/* Audio Controls Module */}
          <div className="flex flex-col items-center justify-center p-6 rounded-2xl bg-slate-950/60 border border-slate-800/80 min-w-[240px] shadow-inner">
            <div className="flex items-center gap-3 mb-4">
              <button
                type="button"
                onClick={handleReset}
                className="p-2.5 rounded-xl bg-slate-800/80 hover:bg-slate-700 text-slate-300 transition-colors"
                title="Recommencer"
              >
                <RotateCcw className="w-4 h-4" />
              </button>

              <button
                type="button"
                onClick={handleTogglePlay}
                className="p-4 rounded-2xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold shadow-lg shadow-indigo-600/30 transition-transform active:scale-95 flex items-center justify-center"
              >
                {isPlaying ? <Pause className="w-6 h-6" /> : <Play className="w-6 h-6 ml-0.5" />}
              </button>

              <button
                type="button"
                onClick={() => {
                  setPlaybackSpeed((prev) => (prev === 1 ? 1.25 : prev === 1.25 ? 1.5 : 1));
                }}
                className="px-2.5 py-1.5 rounded-xl bg-slate-800/80 hover:bg-slate-700 text-slate-200 text-xs font-mono font-semibold transition-colors"
                title="Vitesse de lecture"
              >
                {playbackSpeed}x
              </button>
            </div>

            {/* Sound Wave Animation */}
            <div className="flex items-center gap-1 h-6 mb-3">
              {[40, 75, 100, 60, 90, 45, 80, 65, 95, 50, 70].map((h, i) => (
                <span
                  key={i}
                  className={`w-1 rounded-full transition-all duration-300 ${
                    isPlaying
                      ? "bg-indigo-400 animate-pulse"
                      : "bg-slate-700"
                  }`}
                  style={{
                    height: isPlaying ? `${h}%` : "20%",
                    animationDelay: `${i * 100}ms`,
                  }}
                />
              ))}
            </div>

            {/* Turn Progress bar */}
            <div className="w-full space-y-1 text-center">
              <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
                <div
                  className="h-full bg-indigo-500 rounded-full transition-all duration-300"
                  style={{ width: `${progressPercent}%` }}
                />
              </div>
              <p className="text-[11px] font-mono text-slate-400">
                Réplique {activeTurnIndex + 1} / {turns.length} ({progressPercent}%)
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Key Takeaways Card */}
      {episode.key_takeaways && episode.key_takeaways.length > 0 && (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur-sm">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2 mb-3">
            <Sparkles className="w-4 h-4 text-amber-400" />
            Ce qu&apos;il faut retenir de l&apos;épisode
          </h3>
          <ul className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {episode.key_takeaways.map((point, idx) => (
              <li
                key={idx}
                className="flex items-start gap-2.5 p-3 rounded-xl bg-slate-950/40 border border-slate-800/60 text-xs text-slate-300 leading-relaxed"
              >
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                <span>{point}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Interactive Dialogue Transcript */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold text-white flex items-center gap-2">
            <Mic className="w-4 h-4 text-indigo-400" />
            Transcription Intégrale en Direct
          </h2>
          <span className="text-xs text-slate-500">
            Cliquez sur une réplique pour écouter à partir de ce passage
          </span>
        </div>

        <div className="space-y-3 max-h-[600px] overflow-y-auto pr-2 custom-scrollbar">
          {turns.map((turn, index) => {
            const isTurnActive = index === activeTurnIndex;
            const isHost = turn.role === "host" || turn.speaker.toLowerCase().includes("camille") || turn.speaker.toLowerCase().includes("layla") || turn.speaker.toLowerCase().includes("emma");

            return (
              <div
                key={index}
                ref={(el) => {
                  turnRefs.current[index] = el;
                }}
                onClick={() => {
                  setActiveTurnIndex(index);
                  setIsPlaying(true);
                }}
                className={`cursor-pointer rounded-2xl p-4 sm:p-5 transition-all duration-200 border ${
                  isTurnActive
                    ? isHost
                      ? "bg-purple-950/40 border-purple-500/50 shadow-lg shadow-purple-950/50 ring-1 ring-purple-500/30"
                      : "bg-indigo-950/40 border-indigo-500/50 shadow-lg shadow-indigo-950/50 ring-1 ring-indigo-500/30"
                    : "bg-slate-900/50 border-slate-800/80 hover:bg-slate-800/40"
                }`}
              >
                <div className="flex items-center justify-between gap-3 mb-2">
                  <div className="flex items-center gap-2.5">
                    <div
                      className={`w-7 h-7 rounded-xl flex items-center justify-center text-xs font-bold ${
                        isHost
                          ? "bg-purple-500/20 text-purple-300 border border-purple-500/30"
                          : "bg-indigo-500/20 text-indigo-300 border border-indigo-500/30"
                      }`}
                    >
                      {turn.speaker.slice(0, 1)}
                    </div>
                    <div>
                      <span className="text-xs font-bold text-white">
                        {turn.speaker}
                      </span>
                      <span className="text-[11px] text-slate-400 ml-2">
                        {isHost ? "• Hôte" : "• Expert Spécialiste"}
                      </span>
                    </div>
                  </div>

                  {isTurnActive && (
                    <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-indigo-500/20 border border-indigo-500/30 text-indigo-300 text-[10px] font-mono">
                      <Volume2 className="w-3 h-3 animate-pulse" />
                      <span>En cours</span>
                    </div>
                  )}
                </div>

                <div className="text-sm leading-relaxed text-slate-200 pl-9">
                  {renderTurnText(turn.text)}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
