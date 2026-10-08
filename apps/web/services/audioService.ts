import {
  AudioContent,
  AudioGenerationRequestPayload,
  TTSVoice,
} from "../types/audio";

import { getApiBaseUrl } from "./apiClient";

async function audioFetch<T>(
  endpoint: string,
  token: string,
  options: RequestInit = {}
): Promise<T> {
  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl.replace(/\/$/, "")}/${endpoint.replace(/^\//, "")}`;

  const headers: Record<string, string> = {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (response.status === 204) {
    return {} as T;
  }

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    let errorMessage = "Une erreur est survenue lors de l'opération audio.";
    if (typeof data.detail === "string") {
      errorMessage = data.detail;
    } else if (typeof data.message === "string") {
      errorMessage = data.message;
    } else if (typeof data === "object" && data !== null) {
      const firstKey = Object.keys(data)[0];
      if (firstKey && Array.isArray(data[firstKey])) {
        errorMessage = `${firstKey}: ${data[firstKey].join(" ")}`;
      } else if (firstKey && typeof data[firstKey] === "string") {
        errorMessage = `${firstKey}: ${data[firstKey]}`;
      }
    }
    throw new Error(errorMessage);
  }

  return data as T;
}

export const audioService = {
  async getSectionAudio(
    token: string,
    sectionId: string
  ): Promise<AudioContent | null> {
    try {
      return await audioFetch<AudioContent>(
        `sections/${sectionId}/audio/`,
        token
      );
    } catch (err: any) {
      if (err.message?.includes("404") || err.message?.includes("Aucun")) {
        return null;
      }
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
