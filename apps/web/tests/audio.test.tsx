import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { AudioProgress, formatAudioTime } from "../components/audio/AudioProgress";
import { AudioPlayer } from "../components/audio/AudioPlayer";
import { AudioContent } from "../types/audio";

describe("Audio Components", () => {
  describe("formatAudioTime helper", () => {
    it("formats seconds into mm:ss format", () => {
      expect(formatAudioTime(0)).toBe("00:00");
      expect(formatAudioTime(65)).toBe("01:05");
      expect(formatAudioTime(3600)).toBe("60:00");
      expect(formatAudioTime(-5)).toBe("00:00");
    });
  });

  describe("AudioProgress", () => {
    it("renders formatted time and duration", () => {
      render(
        <AudioProgress
          currentTime={45}
          duration={180}
          onSeek={vi.fn()}
        />
      );

      expect(screen.getByText("00:45")).toBeInTheDocument();
      expect(screen.getByText("03:00")).toBeInTheDocument();
    });
  });

  describe("AudioPlayer", () => {
    const mockAudio: AudioContent = {
      id: "aud-1",
      course_id: "c-1",
      course_title: "Module 1 Audio",
      section_id: "sec-1",
      audio_url: "https://example.com/audio.mp3",
      duration: 120,
      status: "COMPLETED",
      voice_id: "pierre",
      voice_provider: "mock",
      storage_key: "audios/aud-1.mp3",
      language: "fr",
      script: "Bienvenue dans ce cours audio interactif.",
      created_at: "2026-01-01",
      updated_at: "2026-01-01",
    };

    it("renders player with audio title", () => {
      render(<AudioPlayer audio={mockAudio} title="Module 1 Audio" />);
      expect(screen.getByText("Module 1 Audio")).toBeInTheDocument();
      expect(screen.getByText("02:00")).toBeInTheDocument();
    });
  });
});
