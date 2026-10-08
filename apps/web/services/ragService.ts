import {
  RAGQueryResponse,
  RAGSearchPayload,
  RAGSearchResponse,
} from "../types/rag";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function ragFetch<T>(
  endpoint: string,
  token: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL.replace(/\/$/, "")}/${endpoint.replace(/^\//, "")}`;

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
      errorDetail =
        errorJson.detail ||
        errorJson.message ||
        JSON.stringify(errorJson);
    } catch {
      // Keep default
    }
    throw new Error(errorDetail);
  }

  return response.json() as Promise<T>;
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
