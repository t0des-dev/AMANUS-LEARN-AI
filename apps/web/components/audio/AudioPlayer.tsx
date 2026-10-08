"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  Play,
  Pause,
  RotateCcw,
  RotateCw,
  Volume2,
  VolumeX,
  FileText,
  ChevronDown,
  ChevronUp,
  Headphones,
  Sparkles,
} from "lucide-react";
import { AudioContent } from "../../types/audio";
import { AudioProgress } from "./AudioProgress";

interface AudioPlayerProps {
  audio: AudioContent;
  title?: string;
  autoPlay?: boolean;
  className?: string;
}

export function AudioPlayer({
  audio,
  title,
  autoPlay = false,
  className = "",
}: AudioPlayerProps) {
  const audioRef = useRef<HTMLAudioElement>(null);

  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(audio.duration || 0);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [showScript, setShowScript] = useState(false);
  const [bufferedPercent, setBufferedPercent] = useState(0);

  // Fallback direct URL if relative media path
  const audioSrc = audio.audio_url || "";

  useEffect(() => {
    const el = audioRef.current;
    if (!el) return;

    const handleTimeUpdate = () => {
      setCurrentTime(el.currentTime);
      if (el.buffered.length > 0 && el.duration > 0) {
        const bufferedEnd = el.buffered.end(el.buffered.length - 1);
        setBufferedPercent((bufferedEnd / el.duration) * 100);
      }
    };

    const handleLoadedMetadata = () => {
      if (el.duration && !isNaN(el.duration) && el.duration !== Infinity) {
        setDuration(el.duration);
      } else if (audio.duration) {
        setDuration(audio.duration);
      }
    };

    const handleEnded = () => {
      setIsPlaying(false);
      setCurrentTime(0);
    };

    el.addEventListener("timeupdate", handleTimeUpdate);
    el.addEventListener("loadedmetadata", handleLoadedMetadata);
    el.addEventListener("ended", handleEnded);

    return () => {
      el.removeEventListener("timeupdate", handleTimeUpdate);
      el.removeEventListener("loadedmetadata", handleLoadedMetadata);
      el.removeEventListener("ended", handleEnded);
    };
  }, [audio.duration]);

  // Support Play / Pause (Resume / Pause)
  const togglePlay = () => {
    const el = audioRef.current;
    if (!el) return;

    if (isPlaying) {
      el.pause();
      setIsPlaying(false);
    } else {
      el.play()
        .then(() => setIsPlaying(true))
        .catch(() => setIsPlaying(false));
    }
  };

  const handleSeek = (newTime: number) => {
    const el = audioRef.current;
    if (!el) return;
    el.currentTime = newTime;
    setCurrentTime(newTime);
  };

  const handleSkip = (seconds: number) => {
    const el = audioRef.current;
    if (!el) return;
    const target = Math.max(0, Math.min(duration, el.currentTime + seconds));
    el.currentTime = target;
    setCurrentTime(target);
  };

  const handleRateChange = () => {
    const rates = [1, 1.25, 1.5, 0.75];
    const nextRate = rates[(rates.indexOf(playbackRate) + 1) % rates.length];
    setPlaybackRate(nextRate);
    if (audioRef.current) {
      audioRef.current.playbackRate = nextRate;
    }
  };

  const toggleMute = () => {
    const el = audioRef.current;
    if (!el) return;
    el.muted = !isMuted;
    setIsMuted(!isMuted);
  };

  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newVol = parseFloat(e.target.value);
    setVolume(newVol);
    setIsMuted(newVol === 0);
    if (audioRef.current) {
      audioRef.current.volume = newVol;
      audioRef.current.muted = newVol === 0;
    }
  };

  return (
    <div
      className={`rounded-2xl border border-indigo-500/30 bg-slate-950/90 p-4 sm:p-5 shadow-2xl backdrop-blur-xl ${className}`}
    >
      <audio
        ref={audioRef}
        src={audioSrc}
        autoPlay={autoPlay}
        preload="metadata"
      />

      {/* Header Info */}
      <div className="flex items-center justify-between mb-3 border-b border-slate-800/80 pb-3">
        <div className="flex items-center gap-2.5 overflow-hidden">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 text-white shadow-md shadow-indigo-500/25">
            <Headphones className="h-4 w-4" />
          </div>

          <div className="overflow-hidden">
            <div className="flex items-center gap-2">
              <span className="truncate text-xs sm:text-sm font-bold text-white">
                {title || audio.section_title || "Leçon Audio"}
              </span>
              <span className="rounded-full bg-indigo-950/80 border border-indigo-800/60 px-2 py-0.5 text-[10px] font-semibold text-indigo-300 shrink-0">
                Voix : {audio.voice_id}
              </span>
            </div>
            <p className="text-[11px] text-slate-400 truncate">
              Synthèse vocale pédagogique • {audio.language.toUpperCase()}
            </p>
          </div>
        </div>

        {/* Script toggle button */}
        {audio.script && (
          <button
            type="button"
            onClick={() => setShowScript(!showScript)}
            className="flex items-center gap-1 rounded-lg border border-slate-800 bg-slate-900/80 px-2.5 py-1 text-xs font-medium text-slate-300 transition hover:bg-slate-800 hover:text-white"
          >
            <FileText className="h-3.5 w-3.5 text-indigo-400" />
            <span className="hidden sm:inline">Transcription</span>
            {showScript ? (
              <ChevronUp className="h-3.5 w-3.5 text-slate-400" />
            ) : (
              <ChevronDown className="h-3.5 w-3.5 text-slate-400" />
            )}
          </button>
        )}
      </div>

      {/* Progress & Duration Bar */}
      <AudioProgress
        currentTime={currentTime}
        duration={duration}
        onSeek={handleSeek}
        bufferedPercent={bufferedPercent}
        className="mb-4"
      />

      {/* Main Controls */}
      <div className="flex items-center justify-between gap-2">
        {/* Playback speed */}
        <button
          type="button"
          onClick={handleRateChange}
          className="flex h-8 min-w-10 items-center justify-center rounded-lg border border-slate-800 bg-slate-900/80 px-2 text-xs font-mono font-bold text-indigo-300 transition hover:bg-slate-800 hover:text-white"
          title="Vitesse de lecture"
        >
          {playbackRate}x
        </button>

        {/* Primary Buttons: -10s, Play/Pause, +10s */}
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => handleSkip(-10)}
            className="flex h-9 w-9 items-center justify-center rounded-full text-slate-400 hover:bg-slate-900 hover:text-white transition"
            title="Reculer de 10s"
          >
            <RotateCcw className="h-4 w-4" />
          </button>

          <button
            type="button"
            onClick={togglePlay}
            className="flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-tr from-indigo-600 to-violet-500 text-white shadow-lg shadow-indigo-500/30 transition hover:scale-105 active:scale-95"
            title={isPlaying ? "Pause" : "Lecture (Reprendre)"}
          >
            {isPlaying ? (
              <Pause className="h-5 w-5 fill-current" />
            ) : (
              <Play className="h-5 w-5 fill-current ml-0.5" />
            )}
          </button>

          <button
            type="button"
            onClick={() => handleSkip(10)}
            className="flex h-9 w-9 items-center justify-center rounded-full text-slate-400 hover:bg-slate-900 hover:text-white transition"
            title="Avancer de 10s"
          >
            <RotateCw className="h-4 w-4" />
          </button>
        </div>

        {/* Volume controls */}
        <div className="flex items-center gap-1.5">
          <button
            type="button"
            onClick={toggleMute}
            className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 hover:text-white transition"
            title={isMuted ? "Activer le son" : "Couper le son"}
          >
            {isMuted || volume === 0 ? (
              <VolumeX className="h-4 w-4 text-red-400" />
            ) : (
              <Volume2 className="h-4 w-4" />
            )}
          </button>

          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={isMuted ? 0 : volume}
            onChange={handleVolumeChange}
            className="h-1.5 w-16 sm:w-20 cursor-pointer accent-indigo-500 rounded-full bg-slate-800"
            title={`Volume : ${Math.round((isMuted ? 0 : volume) * 100)}%`}
          />
        </div>
      </div>

      {/* Pedagogical Transcript / Script Dropdown */}
      {showScript && audio.script && (
        <div className="mt-4 border-t border-slate-800/80 pt-3">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-300 mb-2">
            <Sparkles className="h-3.5 w-3.5 text-indigo-400" />
            <span>Script pédagogique oralisé :</span>
          </div>
          <div className="max-h-48 overflow-y-auto rounded-xl bg-slate-900/80 border border-slate-800/80 p-3 text-xs leading-relaxed text-slate-300 whitespace-pre-wrap font-sans">
            {audio.script}
          </div>
        </div>
      )}
    </div>
  );
}
