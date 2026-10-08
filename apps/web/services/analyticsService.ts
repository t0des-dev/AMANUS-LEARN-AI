import {
  CourseAnalyticsResponse,
  QuizAnalyticsResponse,
  StudentAnalyticsResponse,
  StudentPerformanceItem,
} from "../types/analytics";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function analyticsFetch<T>(
  endpoint: string,
  token: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL.replace(/\/$/, "")}/${endpoint.replace(/^\//, "")}`;

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
    let errorMessage = "Une erreur est survenue lors de l'accès aux statistiques.";
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

  async getQuizAnalytics(
    token: string,
    quizId: string
  ): Promise<QuizAnalyticsResponse> {
    return analyticsFetch<QuizAnalyticsResponse>(
      `analytics/quizzes/${quizId}/`,
      token
    );
  },
};
