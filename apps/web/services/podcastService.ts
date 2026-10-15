import {
  PodcastEpisodeItem,
  PodcastGenerateRequest,
} from "../types/podcast";
import { authedRequest } from "./apiClient";

async function podcastFetch<T>(
  endpoint: string,
  token: string,
  options: RequestInit = {}
): Promise<T> {
  return authedRequest<T>(endpoint, options, token);
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
