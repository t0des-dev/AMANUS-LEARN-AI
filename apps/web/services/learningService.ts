import {
  CourseLearningProgressData,
  LearningPathItem,
  SectionCompletePayload,
  StudentDashboardData,
  StudySessionItem,
} from "../types/learning";

import { authedRequest } from "./apiClient";

async function learningFetch<T>(
  endpoint: string,
  token: string,
  options: RequestInit = {}
): Promise<T> {
  return authedRequest<T>(endpoint, options, token, "Une erreur est survenue lors de l'accès aux données d'apprentissage.");
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
