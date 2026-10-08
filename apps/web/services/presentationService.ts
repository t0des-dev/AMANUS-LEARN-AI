import {
  CreatePresentationPayload,
  CreateSlidePayload,
  ExportResponse,
  Presentation,
  PresentationSlide,
  UpdatePresentationPayload,
  UpdateSlidePayload,
} from "../types/presentation";

import { getApiBaseUrl } from "./apiClient";

async function presentationFetch<T>(
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
    let errorMessage = "Une erreur est survenue lors de l'opération sur la présentation.";
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

export const presentationService = {
  async getPresentation(token: string, id: string): Promise<Presentation> {
    return presentationFetch<Presentation>(`presentations/${id}/`, token);
  },

  async updatePresentation(
    token: string,
    id: string,
    payload: UpdatePresentationPayload
  ): Promise<Presentation> {
    return presentationFetch<Presentation>(`presentations/${id}/`, token, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  },

  async createPresentation(
    token: string,
    courseId: string,
    payload: CreatePresentationPayload = {}
  ): Promise<Presentation> {
    return presentationFetch<Presentation>(
      `courses/${courseId}/presentations/`,
      token,
      {
        method: "POST",
        body: JSON.stringify(payload),
      }
    );
  },

  async listCoursePresentations(
    token: string,
    courseId: string
  ): Promise<Presentation[]> {
    return presentationFetch<Presentation[]>(
      `courses/${courseId}/presentations/`,
      token
    );
  },

  async addSlide(
    token: string,
    presentationId: string,
    payload: CreateSlidePayload = {}
  ): Promise<PresentationSlide> {
    return presentationFetch<PresentationSlide>(
      `presentations/${presentationId}/slides/`,
      token,
      {
        method: "POST",
        body: JSON.stringify(payload),
      }
    );
  },

  async updateSlide(
    token: string,
    presentationId: string,
    slideId: string,
    payload: UpdateSlidePayload
  ): Promise<PresentationSlide> {
    return presentationFetch<PresentationSlide>(
      `presentations/${presentationId}/slides/${slideId}/`,
      token,
      {
        method: "PATCH",
        body: JSON.stringify(payload),
      }
    );
  },

  async deleteSlide(
    token: string,
    presentationId: string,
    slideId: string
  ): Promise<void> {
    await presentationFetch<void>(
      `presentations/${presentationId}/slides/${slideId}/`,
      token,
      {
        method: "DELETE",
      }
    );
  },

  async reorderSlides(
    token: string,
    presentationId: string,
    slides: { id: string; slide_number: number }[]
  ): Promise<Presentation> {
    return presentationFetch<Presentation>(
      `presentations/${presentationId}/reorder/`,
      token,
      {
        method: "POST",
        body: JSON.stringify({ slides }),
      }
    );
  },

  async exportPresentation(
    token: string,
    presentationId: string,
    asyncExport = false
  ): Promise<ExportResponse> {
    const query = asyncExport ? "?async=true" : "";
    return presentationFetch<ExportResponse>(
      `presentations/${presentationId}/export/${query}`,
      token,
      {
        method: "POST",
        body: JSON.stringify({ async: asyncExport }),
      }
    );
  },
};
