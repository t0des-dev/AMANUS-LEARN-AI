export type GenerationType =
  | "SUMMARY"
  | "KEY_POINTS"
  | "OBJECTIVES"
  | "LESSON"
  | "REVISION_SHEET";

export type GenerationStatus = "PENDING" | "SUCCESS" | "FAILED";

export interface GenerateRequestPayload {
  provider?: string;
  model?: string;
  focus?: string;
  top_k?: number;
}

export interface SummaryResult {
  overview: string;
  key_takeaways: string[];
  chapters_summary?: Array<{
    title: string;
    summary: string;
  }>;
  citations?: Array<{
    citation_id: number;
    chunk_id: string;
    document_title: string;
    page: number | null;
    snippet: string;
  }>;
  sources_summary?: string;
}

export interface KeyPointsResult {
  key_points: Array<{
    point: string;
    explanation: string;
  }>;
  citations?: unknown[];
  sources_summary?: string;
}

export interface ObjectivesResult {
  objectives: Array<{
    level: string;
    objective: string;
  }>;
  citations?: unknown[];
  sources_summary?: string;
}

export interface LessonResult {
  title: string;
  introduction: string;
  sections: Array<{
    title: string;
    content: string;
  }>;
  conclusion: string;
  citations?: unknown[];
  sources_summary?: string;
}

export interface AIGeneration<T = Record<string, unknown>> {
  id: string;
  organization: string;
  user: string | null;
  document: string | null;
  type: GenerationType;
  provider: string;
  model: string;
  prompt_version: string;
  input_tokens: number;
  output_tokens: number;
  status: GenerationStatus;
  result: T;
  error: string;
  created_at: string;
}
