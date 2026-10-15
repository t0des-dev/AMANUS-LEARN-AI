import {
  FlashcardDeckItem,
  ReviewSubmitResponse,
} from "../types/flashcard";
import { authedRequest } from "./apiClient";

async function flashcardFetch<T>(
  endpoint: string,
  token: string,
  options: RequestInit = {}
): Promise<T> {
  return authedRequest<T>(endpoint, options, token);
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
