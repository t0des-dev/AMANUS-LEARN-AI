"use client";

import React, { useRef } from "react";

interface AudioProgressProps {
  currentTime: number;
  duration: number;
  onSeek: (newTime: number) => void;
  bufferedPercent?: number;
  className?: string;
}

export function formatAudioTime(seconds: number): string {
  if (isNaN(seconds) || seconds < 0) return "00:00";
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
}

export function AudioProgress({
  currentTime,
  duration,
  onSeek,
  bufferedPercent = 0,
  className = "",
}: AudioProgressProps) {
  const progressBarRef = useRef<HTMLDivElement>(null);

  const progressPercent =
    duration > 0 ? Math.min(100, Math.max(0, (currentTime / duration) * 100)) : 0;

  const handleSeek = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!progressBarRef.current || duration <= 0) return;
    const rect = progressBarRef.current.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const clickRatio = Math.max(0, Math.min(1, clickX / rect.width));
    onSeek(clickRatio * duration);
  };

  return (
    <div className={`flex flex-col gap-1.5 w-full select-none ${className}`}>
      {/* Interactive Progress Bar */}
      <div
        ref={progressBarRef}
        onClick={handleSeek}
        className="group relative h-2.5 w-full cursor-pointer rounded-full bg-slate-800/80 transition hover:h-3"
      >
        {/* Buffered bar */}
        {bufferedPercent > 0 && (
          <div
            className="absolute top-0 bottom-0 left-0 rounded-full bg-slate-700/60 transition-all duration-300"
            style={{ width: `${Math.min(100, bufferedPercent)}%` }}
          />
        )}

        {/* Played progress bar */}
        <div
          className="absolute top-0 bottom-0 left-0 rounded-full bg-gradient-to-r from-indigo-500 to-violet-500 shadow-sm shadow-indigo-500/30"
          style={{ width: `${progressPercent}%` }}
        />

        {/* Draggable Scrubber Thumb */}
        <div
          className="absolute top-1/2 -translate-y-1/2 -ml-2 h-4 w-4 rounded-full bg-white shadow-md ring-2 ring-indigo-500 transition scale-0 group-hover:scale-100"
          style={{ left: `${progressPercent}%` }}
        />
      </div>

      {/* Time stamps */}
      <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
        <span>{formatAudioTime(currentTime)}</span>
        <span>{formatAudioTime(duration)}</span>
      </div>
    </div>
  );
}
