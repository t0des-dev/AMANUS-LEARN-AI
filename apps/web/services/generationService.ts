import {
  AIGeneration,
  GenerateRequestPayload,
  KeyPointsResult,
  LessonResult,
  ObjectivesResult,
  SummaryResult,
} from "../types/generation";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function generationFetch<T>(
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

export const generationService = {
  async generateSummary(
    documentId: string,
    token: string,
    payload: GenerateRequestPayload = {}
  ): Promise<AIGeneration<SummaryResult>> {
    return generationFetch<AIGeneration<SummaryResult>>(
      `documents/${documentId}/generate/summary/`,
      token,
      {
        method: "POST",
        body: JSON.stringify(payload),
      }
    );
  },

  async generateCourse(
    documentId: string,
    token: string,
    payload: GenerateRequestPayload = {}
  ): Promise<AIGeneration<LessonResult>> {
    return generationFetch<AIGeneration<LessonResult>>(
      `documents/${documentId}/generate/course/`,
      token,
      {
        method: "POST",
        body: JSON.stringify(payload),
      }
    );
  },

  async generateObjectives(
    documentId: string,
    token: string,
    payload: GenerateRequestPayload = {}
  ): Promise<AIGeneration<ObjectivesResult>> {
    return generationFetch<AIGeneration<ObjectivesResult>>(
      `documents/${documentId}/generate/objectives/`,
      token,
      {
        method: "POST",
        body: JSON.stringify(payload),
      }
    );
  },

  async generateKeyPoints(
    documentId: string,
    token: string,
    payload: GenerateRequestPayload = {}
  ): Promise<AIGeneration<KeyPointsResult>> {
    return generationFetch<AIGeneration<KeyPointsResult>>(
      `documents/${documentId}/generate/key-points/`,
      token,
      {
        method: "POST",
        body: JSON.stringify(payload),
      }
    );
  },
};
