import {
  RAGQueryResponse,
  RAGSearchPayload,
  RAGSearchResponse,
} from "../types/rag";

import { authedRequest } from "./apiClient";

async function ragFetch<T>(
  endpoint: string,
  token: string,
  options: RequestInit = {}
): Promise<T> {
  return authedRequest<T>(endpoint, options, token);
}

export const ragService = {
  async search(token: string, payload: RAGSearchPayload): Promise<RAGSearchResponse> {
    return ragFetch<RAGSearchResponse>("rag/search/", token, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async query(token: string, payload: RAGSearchPayload): Promise<RAGQueryResponse> {
    return ragFetch<RAGQueryResponse>("rag/query/", token, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
};
