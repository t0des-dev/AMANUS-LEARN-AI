import {
  AudioContent,
  AudioGenerationRequestPayload,
  TTSVoice,
} from "../types/audio";

import { authedRequest } from "./apiClient";

async function audioFetch<T>(
  endpoint: string,
  token: string,
  options: RequestInit = {}
): Promise<T> {
  return authedRequest<T>(endpoint, options, token, "Une erreur est survenue lors de l'opération audio.");
}

export const audioService = {
  async getSectionAudio(
    token: string,
    sectionId: string
  ): Promise<AudioContent | null> {
    if (!sectionId || sectionId === "null" || sectionId === "undefined") {
      return null;
    }
    try {
      const data = await audioFetch<any>(
        `sections/${sectionId}/audio/`,
        token
      );
      if (!data || !data.id || data.status === "NONE") {
        return null;
      }
      return data as AudioContent;
    } catch {
      return null;
    }
  },

  async requestSectionAudio(
    token: string,
    sectionId: string,
    payload: AudioGenerationRequestPayload = {}
  ): Promise<AudioContent> {
    return audioFetch<AudioContent>(`sections/${sectionId}/audio/`, token, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async getAudioDetail(token: string, audioId: string): Promise<AudioContent> {
    return audioFetch<AudioContent>(`audio/${audioId}/`, token);
  },

  async deleteAudio(token: string, audioId: string): Promise<void> {
    await audioFetch<void>(`audio/${audioId}/`, token, {
      method: "DELETE",
    });
  },

  async listVoices(token: string, language?: string): Promise<TTSVoice[]> {
    const query = language ? `?language=${encodeURIComponent(language)}` : "";
    const res = await audioFetch<{ voices: TTSVoice[] }>(
      `audio/voices/${query}`,
      token
    );
    return res.voices || [];
  },
};
