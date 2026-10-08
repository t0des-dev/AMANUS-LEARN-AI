import {
  CreateQuizPayload,
  GenerateQuizPayload,
  Quiz,
  QuizAttempt,
  QuizResultsResponse,
  SubmitQuizPayload,
} from "../types/quiz";

import { getApiBaseUrl } from "./apiClient";

async function quizFetch<T>(
  endpoint: string,
  token: string,
  options: RequestInit = {}
): Promise<T> {
  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl.replace(/\/$/, "")}/${endpoint.replace(/^\//, "")}`;

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

  if (response.status === 204) {
    return {} as T;
  }

  return response.json() as Promise<T>;
}

export const quizService = {
  async list(
    token: string,
    params?: {
      organization_id?: string;
      course_id?: string;
      quiz_type?: string;
      type?: string;
      difficulty?: string;
    }
  ): Promise<Quiz[]> {
    const query = new URLSearchParams();
    if (params?.organization_id) query.append("organization_id", params.organization_id);
    if (params?.course_id) query.append("course_id", params.course_id);
    if (params?.quiz_type) query.append("quiz_type", params.quiz_type);
    if (params?.type) query.append("quiz_type", params.type);
    if (params?.difficulty) query.append("difficulty", params.difficulty);

    const qs = query.toString() ? `?${query.toString()}` : "";
    const res = await quizFetch<any>(`quizzes/${qs}`, token);
    return Array.isArray(res) ? res : res.results || [];
  },

  listQuizzes(
    token: string,
    params?: {
      organization_id?: string;
      course_id?: string;
      quiz_type?: string;
      type?: string;
      difficulty?: string;
    }
  ): Promise<Quiz[]> {
    return this.list(token, params);
  },

  async get(token: string, quizId: string): Promise<Quiz> {
    return quizFetch<Quiz>(`quizzes/${quizId}/`, token);
  },

  getQuiz(token: string, quizId: string): Promise<Quiz> {
    return this.get(token, quizId);
  },

  async create(token: string, payload: CreateQuizPayload): Promise<Quiz> {
    return quizFetch<Quiz>("quizzes/", token, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  createQuiz(token: string, payload: CreateQuizPayload): Promise<Quiz> {
    return this.create(token, payload);
  },

  async listByCourse(token: string, courseId: string): Promise<Quiz[]> {
    const res = await quizFetch<any>(`courses/${courseId}/quizzes/`, token);
    return Array.isArray(res) ? res : res.results || [];
  },

  async createForCourse(
    token: string,
    courseId: string,
    payload: Partial<CreateQuizPayload>
  ): Promise<Quiz> {
    return quizFetch<Quiz>(`courses/${courseId}/quizzes/`, token, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async generate(
    token: string,
    quizId: string,
    payload: GenerateQuizPayload = {}
  ): Promise<{ quiz: Quiz; generated_count: number }> {
    return quizFetch<{ quiz: Quiz; generated_count: number }>(
      `quizzes/${quizId}/generate/`,
      token,
      {
        method: "POST",
        body: JSON.stringify(payload),
      }
    );
  },

  generateQuestions(
    token: string,
    quizId: string,
    payload: GenerateQuizPayload = {}
  ): Promise<{ quiz: Quiz; generated_count: number }> {
    return this.generate(token, quizId, payload);
  },

  async start(token: string, quizId: string): Promise<QuizAttempt> {
    return quizFetch<QuizAttempt>(`quizzes/${quizId}/start/`, token, {
      method: "POST",
    });
  },

  startQuiz(token: string, quizId: string): Promise<QuizAttempt> {
    return this.start(token, quizId);
  },

  async submit(
    token: string,
    quizId: string,
    payload: SubmitQuizPayload
  ): Promise<QuizAttempt> {
    return quizFetch<QuizAttempt>(`quizzes/${quizId}/submit/`, token, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  submitQuiz(
    token: string,
    quizId: string,
    payload: SubmitQuizPayload
  ): Promise<QuizAttempt> {
    return this.submit(token, quizId, payload);
  },

  async results(token: string, quizId: string): Promise<QuizResultsResponse> {
    return quizFetch<QuizResultsResponse>(`quizzes/${quizId}/results/`, token);
  },

  getResults(token: string, quizId: string): Promise<QuizResultsResponse> {
    return this.results(token, quizId);
  },
};
