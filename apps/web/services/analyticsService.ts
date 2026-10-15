import {
  CourseAnalyticsResponse,
  StudentAnalyticsResponse,
  StudentPerformanceItem,
} from "../types/analytics";

import { authedRequest } from "./apiClient";

async function analyticsFetch<T>(
  endpoint: string,
  token: string,
  options: RequestInit = {}
): Promise<T> {
  return authedRequest<T>(endpoint, options, token, "Une erreur est survenue lors de l'accès aux statistiques.");
}

export const analyticsService = {
  async getStudentAnalytics(token: string): Promise<StudentAnalyticsResponse> {
    return analyticsFetch<StudentAnalyticsResponse>("analytics/student/", token);
  },

  async getCourseAnalytics(
    token: string,
    courseId: string
  ): Promise<CourseAnalyticsResponse> {
    return analyticsFetch<CourseAnalyticsResponse>(
      `analytics/courses/${courseId}/`,
      token
    );
  },

  async getCourseStudentsPerformance(
    token: string,
    courseId: string
  ): Promise<StudentPerformanceItem[]> {
    return analyticsFetch<StudentPerformanceItem[]>(
      `analytics/courses/${courseId}/students/`,
      token
    );
  },
};
