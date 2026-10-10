import { UserProfile } from "./auth";

export type DocumentStatus =
  | "UPLOADING"
  | "UPLOADED"
  | "EXTRACTING"
  | "OCR"
  | "STRUCTURING"
  | "CHUNKING"
  | "PROCESSING"
  | "COMPLETED"
  | "READY"
  | "FAILED"
  | "ARCHIVED";

export type DocumentProcessingStage =
  | "Uploading"
  | "Extracting"
  | "OCR"
  | "Structuring"
  | "Chunking"
  | "Completed"
  | "Failed";

export type DocumentFileType = "pdf" | "docx" | "pptx" | "txt";

export interface DocumentItem {
  id: string;
  organization: string;
  owner: UserProfile | null;
  title: string;
  description: string;
  file_name: string;
  file_type: string;
  file_size: number;
  file_size_human: string;
  file_extension: string;
  storage_key?: string;
  language: string;
  page_count: number;
  status: DocumentStatus;
  download_url?: string;
  error_message?: string;
  processing_metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface DocumentUploadPayload {
  file: File;
  organization_id: string;
  title?: string;
  description?: string;
  language?: string;
}

export interface DocumentUpdatePayload {
  title?: string;
  description?: string;
  language?: string;
  status?: DocumentStatus;
}

export interface DocumentProcessResponse {
  id: string;
  status: DocumentStatus;
  task_id?: string;
  message: string;
}

export interface DocumentStatusResponse {
  id: string;
  status: DocumentStatus;
  page_count: number;
  created_at: string;
  updated_at: string;
}

export interface DocumentProcessingStatusResponse {
  id: string;
  status: DocumentStatus;
  progress_stage: DocumentProcessingStage;
  page_count: number;
  pages_count: number;
  chunks_count: number;
  quality_grade?: "FULL" | "PARTIAL" | "UNUSABLE" | string;
  quality_warnings?: string[];
  error_message: string;
  updated_at: string;
}

export interface DocumentPageItem {
  id: string;
  document: string;
  page_number: number;
  text: string;
  ocr_used: boolean;
  metadata: {
    chapter?: string | null;
    section?: string | null;
    subsection?: string | null;
    char_count?: number;
    headings?: string[];
    [key: string]: any;
  };
  created_at: string;
  updated_at: string;
}

export interface DocumentPagesResponse {
  count: number;
  document_id: string;
  results: DocumentPageItem[];
}
