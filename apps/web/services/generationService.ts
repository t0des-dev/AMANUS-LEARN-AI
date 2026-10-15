import {
  AIGeneration,
  GenerateRequestPayload,
  KeyPointsResult,
  LessonResult,
  ObjectivesResult,
  SummaryResult,
} from "../types/generation";

import { authedRequest } from "./apiClient";

async function generationFetch<T>(
  endpoint: string,
  token: string,
  options: RequestInit = {}
): Promise<T> {
  return authedRequest<T>(endpoint, options, token);
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
