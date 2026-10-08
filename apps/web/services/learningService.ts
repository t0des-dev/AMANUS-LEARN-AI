import {
  CourseLearningProgressData,
  LearningPathItem,
  SectionCompletePayload,
  StudentDashboardData,
  StudySessionItem,
} from "../types/learning";

import { getApiBaseUrl } from "./apiClient";

async function learningFetch<T>(
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
    let errorMessage = "Une erreur est survenue lors de l'accès aux données d'apprentissage.";
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

export const learningService = {
  async getDashboard(token: string): Promise<StudentDashboardData> {
    return learningFetch<StudentDashboardData>("learning/dashboard/", token);
  },

  async listCourses(token: string): Promise<LearningPathItem[]> {
    const data = await learningFetch<any>("learning/courses/", token);
    return Array.isArray(data) ? data : data.results || [];
  },

  async getCourseProgress(
    token: string,
    courseId: string
  ): Promise<CourseLearningProgressData> {
    return learningFetch<CourseLearningProgressData>(
      `learning/courses/${courseId}/progress/`,
      token
    );
  },

  async completeSection(
    token: string,
    sectionId: string,
    payload: SectionCompletePayload = {}
  ): Promise<{ progress: any; course_progress: number; course_status: string }> {
    return learningFetch<{ progress: any; course_progress: number; course_status: string }>(
      `learning/sections/${sectionId}/complete/`,
      token,
      {
        method: "POST",
        body: JSON.stringify(payload),
      }
    );
  },

  async startStudySession(
    token: string,
    courseId: string
  ): Promise<StudySessionItem> {
    return learningFetch<StudySessionItem>("learning/sessions/start/", token, {
      method: "POST",
      body: JSON.stringify({ course_id: courseId }),
    });
  },

  async finishStudySession(
    token: string,
    sessionId: string
  ): Promise<StudySessionItem> {
    return learningFetch<StudySessionItem>(
      `learning/sessions/${sessionId}/finish/`,
      token,
      {
        method: "POST",
      }
    );
  },
};
