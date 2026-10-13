import {
  PodcastEpisodeItem,
  PodcastGenerateRequest,
} from "../types/podcast";
import { getApiBaseUrl } from "./apiClient";

async function podcastFetch<T>(
  endpoint: string,
  token: string,
  options: RequestInit = {}
): Promise<T> {
  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl.replace(/\/$/, "")}/${endpoint.replace(/^\//, "")}`;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
    ...(options.headers as Record<string, string>),
  };

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = `Erreur HTTP ${response.status}`;
    try {
      const errorJson = await response.json();
      errorDetail = errorJson.detail || errorJson.message || JSON.stringify(errorJson);
    } catch {
      // Keep default
    }
    throw new Error(errorDetail);
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json() as Promise<T>;
}

export const podcastService = {
  async listPodcasts(
    token: string,
    params?: { document_id?: string; course_id?: string }
  ): Promise<PodcastEpisodeItem[]> {
    const query = new URLSearchParams();
    if (params?.document_id) query.append("document_id", params.document_id);
    if (params?.course_id) query.append("course_id", params.course_id);
    const qs = query.toString() ? `?${query.toString()}` : "";
    return podcastFetch<PodcastEpisodeItem[]>(`audio/podcasts/${qs}`, token);
  },

  async getPodcast(token: string, id: string): Promise<PodcastEpisodeItem> {
    return podcastFetch<PodcastEpisodeItem>(`audio/podcasts/${id}/`, token);
  },

  async generatePodcast(
    token: string,
    req: PodcastGenerateRequest
  ): Promise<PodcastEpisodeItem> {
    return podcastFetch<PodcastEpisodeItem>("audio/podcasts/", token, {
      method: "POST",
      body: JSON.stringify(req),
    });
  },

  async deletePodcast(token: string, id: string): Promise<void> {
    await podcastFetch<void>(`audio/podcasts/${id}/`, token, {
      method: "DELETE",
    });
  },
};
