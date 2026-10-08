export interface RAGSearchPayload {
  query: string;
  organization_id: string;
  document_id?: string | null;
  top_k?: number;
}

export interface RAGSearchResultItem {
  chunk_id: string;
  document_id: string;
  document_title: string;
  page: number | null;
  page_number?: number | null;
  chapter: string | null;
  section: string | null;
  subsection: string | null;
  chunk_index: number;
  content: string;
  score: number;
  distance?: number;
  metadata?: Record<string, any>;
}

export interface RAGCitationItem {
  citation_id: number;
  chunk_id: string;
  document_id: string;
  document_title: string;
  page: number | null;
  page_number?: number | null;
  chapter: string | null;
  section: string | null;
  subsection: string | null;
  snippet: string;
  score: number;
}

export interface RAGSearchResponse {
  query: string;
  organization_id: string;
  document_id: string | null;
  count: number;
  results: RAGSearchResultItem[];
}

export interface RAGQueryResponse {
  query: string;
  organization_id: string;
  document_id: string | null;
  count: number;
  results: RAGSearchResultItem[];
  citations: RAGCitationItem[];
  context: string;
  sources_summary: string;
}
