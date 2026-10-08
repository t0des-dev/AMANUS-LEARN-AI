export type PedagogicalCommandCode =
  | "EXPLAIN"
  | "SIMPLIFY"
  | "SUMMARY"
  | "EXAMPLE"
  | "QUIZ"
  | "REVISION"
  | "COMPARE"
  | "DEFINE";

export interface PedagogicalCommand {
  code: PedagogicalCommandCode;
  label: string;
  description: string;
}

export interface SourceCitation {
  citation_id: number;
  chunk_id?: string;
  document_id: string;
  document_title: string;
  page?: number | null;
  page_number?: number | null;
  chapter?: string | null;
  section?: string | null;
  subsection?: string | null;
  snippet: string;
  score?: number | null;
}

export interface ChatMessage {
  id: string;
  session_id?: string;
  role: "user" | "assistant" | "system";
  sender?: string;
  content: string;
  command?: PedagogicalCommandCode | null;
  sources: SourceCitation[];
  tokens_used?: number;
  metadata?: Record<string, any>;
  created_at: string;
}

export interface ScopedDocumentInfo {
  id: string;
  title: string;
  file_type?: string;
  status?: string;
}

export interface ScopedCourseInfo {
  id: string;
  title: string;
  level?: string;
  status?: string;
}

export interface ChatSession {
  id: string;
  title: string;
  organization_id: string;
  user_id: string;
  document?: ScopedDocumentInfo | null;
  course?: ScopedCourseInfo | null;
  message_count?: number;
  last_message?: {
    id: string;
    role: string;
    content: string;
    created_at: string;
  } | null;
  messages?: ChatMessage[];
  created_at: string;
  updated_at: string;
}

export interface CreateChatSessionPayload {
  title?: string;
  organization_id?: string;
  document_id?: string;
  course_id?: string;
  initial_message?: string;
}

export interface SendMessagePayload {
  content: string;
  command?: PedagogicalCommandCode | string;
  stream?: boolean;
  document_id?: string;
}

export interface SendMessageResponse {
  session_id: string;
  user_message: ChatMessage;
  assistant_message: ChatMessage;
}
