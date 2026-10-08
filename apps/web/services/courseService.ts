import {
  CourseItem,
  CourseSectionItem,
  CreateCoursePayload,
  CreateSectionPayload,
  GenerateCoursePayload,
  UpdateCoursePayload,
  UpdateSectionPayload,
} from "../types/course";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function courseFetch<T>(
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

  if (response.status === 204) {
    return {} as T;
  }

  return response.json() as Promise<T>;
}

export const courseService = {
  async list(
    token: string,
    params?: { organization_id?: string; status?: string; level?: string }
  ): Promise<CourseItem[]> {
    const query = new URLSearchParams();
    if (params?.organization_id) query.append("organization_id", params.organization_id);
    if (params?.status) query.append("status", params.status);
    if (params?.level) query.append("level", params.level);

    const qs = query.toString() ? `?${query.toString()}` : "";
    const res = await courseFetch<any>(`courses/${qs}`, token);
    return Array.isArray(res) ? res : res.results || [];
  },

  async get(token: string, courseId: string): Promise<CourseItem> {
    return courseFetch<CourseItem>(`courses/${courseId}/`, token);
  },

  async create(token: string, payload: CreateCoursePayload): Promise<CourseItem> {
    return courseFetch<CourseItem>("courses/", token, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async update(token: string, courseId: string, payload: UpdateCoursePayload): Promise<CourseItem> {
    return courseFetch<CourseItem>(`courses/${courseId}/`, token, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  },

  async delete(token: string, courseId: string): Promise<void> {
    return courseFetch<void>(`courses/${courseId}/`, token, {
      method: "DELETE",
    });
  },

  async listSections(token: string, courseId: string): Promise<CourseSectionItem[]> {
    const res = await courseFetch<any>(`courses/${courseId}/sections/`, token);
    return Array.isArray(res) ? res : res.results || [];
  },

  async createSection(
    token: string,
    courseId: string,
    payload: CreateSectionPayload
  ): Promise<CourseSectionItem> {
    return courseFetch<CourseSectionItem>(`courses/${courseId}/sections/`, token, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async getSection(token: string, sectionId: string): Promise<CourseSectionItem> {
    return courseFetch<CourseSectionItem>(`sections/${sectionId}/`, token);
  },

  async updateSection(
    token: string,
    sectionId: string,
    payload: UpdateSectionPayload
  ): Promise<CourseSectionItem> {
    return courseFetch<CourseSectionItem>(`sections/${sectionId}/`, token, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  },

  async deleteSection(token: string, sectionId: string): Promise<void> {
    return courseFetch<void>(`sections/${sectionId}/`, token, {
      method: "DELETE",
    });
  },

  async generate(
    token: string,
    courseId: string,
    payload: GenerateCoursePayload = {}
  ): Promise<CourseItem> {
    return courseFetch<CourseItem>(`courses/${courseId}/generate/`, token, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
};
