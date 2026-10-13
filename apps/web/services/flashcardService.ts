import {
  FlashcardDeckItem,
  ReviewSubmitResponse,
} from "../types/flashcard";
import { getApiBaseUrl } from "./apiClient";

async function flashcardFetch<T>(
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

export const flashcardService = {
  async listDecks(
    token: string,
    params?: { course_id?: string; document_id?: string }
  ): Promise<FlashcardDeckItem[]> {
    const query = new URLSearchParams();
    if (params?.course_id) query.append("course_id", params.course_id);
    if (params?.document_id) query.append("document_id", params.document_id);
    const qs = query.toString() ? `?${query.toString()}` : "";
    return flashcardFetch<FlashcardDeckItem[]>(`learning/flashcard-decks/${qs}`, token);
  },

  async getDeck(token: string, deckId: string): Promise<FlashcardDeckItem> {
    return flashcardFetch<FlashcardDeckItem>(`learning/flashcard-decks/${deckId}/`, token);
  },

  async createDeck(
    token: string,
    payload: {
      organization_id: string;
      title: string;
      description?: string;
      course_id?: string;
      document_id?: string;
      cards?: { front: string; back: string; hint?: string; source_citation?: string }[];
    }
  ): Promise<FlashcardDeckItem> {
    return flashcardFetch<FlashcardDeckItem>("learning/flashcard-decks/", token, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async submitReview(
    token: string,
    cardId: string,
    quality: number
  ): Promise<ReviewSubmitResponse> {
    return flashcardFetch<ReviewSubmitResponse>(`learning/flashcards/${cardId}/review/`, token, {
      method: "POST",
      body: JSON.stringify({ quality }),
    });
  },
};
