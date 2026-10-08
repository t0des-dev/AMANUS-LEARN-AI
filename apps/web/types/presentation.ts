export type PresentationTheme =
  | "modern_dark"
  | "minimal_light"
  | "academic_indigo"
  | "corporate_blue";

export type PresentationStatus =
  | "DRAFT"
  | "GENERATING"
  | "READY"
  | "EXPORTING"
  | "FAILED";

export interface PresentationSlide {
  id: string;
  presentation: string;
  slide_number: number;
  title: string;
  content: string;
  speaker_notes: string;
  image_prompt: string;
  image_url: string;
  created_at: string;
  updated_at: string;
}

export interface Presentation {
  id: string;
  course: string;
  course_title: string;
  title: string;
  theme: PresentationTheme;
  status: PresentationStatus;
  storage_key: string;
  export_url: string | null;
  slides_count: number;
  slides: PresentationSlide[];
  created_at: string;
  updated_at: string;
}

export interface CreatePresentationPayload {
  title?: string;
  theme?: PresentationTheme;
}

export interface UpdatePresentationPayload {
  title?: string;
  theme?: PresentationTheme;
  slides_order?: { id: string; slide_number: number }[];
}

export interface CreateSlidePayload {
  title?: string;
  content?: string;
  speaker_notes?: string;
  image_prompt?: string;
  image_url?: string;
  slide_number?: number;
}

export interface UpdateSlidePayload {
  title?: string;
  content?: string;
  speaker_notes?: string;
  image_prompt?: string;
  image_url?: string;
  slide_number?: number;
}

export interface ExportResponse {
  status: PresentationStatus;
  storage_key?: string;
  export_url?: string | null;
  task_id?: string;
  message?: string;
  presentation?: Presentation;
}
