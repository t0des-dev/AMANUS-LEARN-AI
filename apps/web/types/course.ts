export type CourseLevel =
  | "BEGINNER"
  | "INTERMEDIATE"
  | "ADVANCED"
  | "EXPERT";

export type CourseStatus = "DRAFT" | "PUBLISHED" | "ARCHIVED";

export interface CourseSectionItem {
  id: string;
  course?: string;
  parent: string | null;
  title: string;
  order: number;
  content: string;
  summary: string;
  objectives: string[];
  estimated_minutes: number;
  level_depth: number;
  children?: CourseSectionItem[];
  created_at: string;
  updated_at: string;
}

export interface CourseItem {
  id: string;
  organization: string;
  organization_name?: string;
  document: string | null;
  created_by: string | null;
  creator_name?: string;
  title: string;
  description: string;
  language: string;
  level: CourseLevel;
  status: CourseStatus;
  sections_count: number;
  total_estimated_minutes: number;
  sections?: CourseSectionItem[];
  created_at: string;
  updated_at: string;
}

export interface CreateCoursePayload {
  organization: string;
  document?: string | null;
  title: string;
  description?: string;
  language?: string;
  level?: CourseLevel;
  status?: CourseStatus;
}

export interface UpdateCoursePayload {
  title?: string;
  description?: string;
  language?: string;
  level?: CourseLevel;
  status?: CourseStatus;
  document?: string | null;
}

export interface CreateSectionPayload {
  parent?: string | null;
  title: string;
  order?: number;
  content?: string;
  summary?: string;
  objectives?: string[];
  estimated_minutes?: number;
}

export interface UpdateSectionPayload {
  parent?: string | null;
  title?: string;
  order?: number;
  content?: string;
  summary?: string;
  objectives?: string[];
  estimated_minutes?: number;
}

export interface GenerateCoursePayload {
  document_id?: string;
  provider?: string;
  model?: string;
  focus?: string;
  top_k?: number;
}
