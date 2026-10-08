import {
  DocumentItem,
  DocumentProcessResponse,
  DocumentStatus,
  DocumentStatusResponse,
  DocumentUpdatePayload,
  DocumentUploadPayload,
} from "../types/document";

import { getApiBaseUrl } from "./apiClient";

interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

async function documentFetch<T>(
  endpoint: string,
  token: string,
  options: RequestInit = {}
): Promise<T> {
  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl.replace(/\/$/, "")}/${endpoint.replace(/^\//, "")}`;
  const isFormData = options.body instanceof FormData;

  const headers: Record<string, string> = {
    Authorization: `Bearer ${token}`,
    ...(options.headers as Record<string, string>),
  };

  if (!isFormData) {
    headers["Content-Type"] = "application/json";
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (response.status === 204) {
    return {} as T;
  }

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    let errorMessage = "Une erreur est survenue lors de l'opération sur le document.";
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

export const documentService = {
  async list(
    token: string,
    filters?: { organization_id?: string; search?: string; status?: DocumentStatus }
  ): Promise<DocumentItem[]> {
    const params = new URLSearchParams();
    if (filters?.organization_id) {
      params.append("organization_id", filters.organization_id);
    }
    if (filters?.search) {
      params.append("search", filters.search);
    }
    if (filters?.status) {
      params.append("status", filters.status);
    }

    const query = params.toString() ? `?${params.toString()}` : "";
    const data = await documentFetch<PaginatedResponse<DocumentItem> | DocumentItem[]>(
      `documents/${query}`,
      token
    );

    if (Array.isArray(data)) {
      return data;
    }
    return data.results || [];
  },

  async get(token: string, id: string): Promise<DocumentItem> {
    return documentFetch<DocumentItem>(`documents/${id}/`, token);
  },

  async upload(
    token: string,
    payload: DocumentUploadPayload,
    onProgress?: (percent: number) => void
  ): Promise<DocumentItem> {
    const formData = new FormData();
    formData.append("file", payload.file);
    formData.append("organization_id", payload.organization_id);
    if (payload.title) {
      formData.append("title", payload.title);
    }
    if (payload.description) {
      formData.append("description", payload.description);
    }
    if (payload.language) {
      formData.append("language", payload.language);
    }

    // Support upload progress via XMLHttpRequest if available in browser
    if (typeof window !== "undefined" && window.XMLHttpRequest && onProgress) {
      return new Promise<DocumentItem>((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        const baseUrl = getApiBaseUrl();
        const url = `${baseUrl.replace(/\/$/, "")}/documents/`;

        xhr.open("POST", url);
        xhr.setRequestHeader("Authorization", `Bearer ${token}`);

        xhr.upload.onprogress = (event) => {
          if (event.lengthComputable) {
            const percent = Math.round((event.loaded / event.total) * 100);
            onProgress(percent);
          }
        };

        xhr.onload = () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            try {
              const res = JSON.parse(xhr.responseText);
              resolve(res);
            } catch (err) {
              reject(new Error("Réponse serveur invalide."));
            }
          } else {
            try {
              const errData = JSON.parse(xhr.responseText);
              const msg =
                errData.file?.[0] ||
                errData.detail ||
                errData.message ||
                "Erreur lors de l'upload du document.";
              reject(new Error(msg));
            } catch {
              reject(new Error(`Erreur ${xhr.status}: Upload impossible.`));
            }
          }
        };

        xhr.onerror = () => reject(new Error("Échec de connexion au serveur."));
        xhr.send(formData);
      });
    }

    return documentFetch<DocumentItem>("documents/", token, {
      method: "POST",
      body: formData,
    });
  },

  async update(
    token: string,
    id: string,
    payload: DocumentUpdatePayload
  ): Promise<DocumentItem> {
    return documentFetch<DocumentItem>(`documents/${id}/`, token, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  },

  async delete(token: string, id: string): Promise<void> {
    await documentFetch<void>(`documents/${id}/`, token, {
      method: "DELETE",
    });
  },

  async process(token: string, id: string): Promise<DocumentProcessResponse> {
    return documentFetch<DocumentProcessResponse>(`documents/${id}/process/`, token, {
      method: "POST",
    });
  },

  async getStatus(token: string, id: string): Promise<DocumentStatusResponse> {
    return documentFetch<DocumentStatusResponse>(`documents/${id}/status/`, token);
  },

  async getProcessingStatus(
    token: string,
    id: string
  ): Promise<import("../types/document").DocumentProcessingStatusResponse> {
    return documentFetch<import("../types/document").DocumentProcessingStatusResponse>(
      `documents/${id}/processing-status/`,
      token
    );
  },

  async getPages(
    token: string,
    id: string
  ): Promise<import("../types/document").DocumentPagesResponse> {
    return documentFetch<import("../types/document").DocumentPagesResponse>(
      `documents/${id}/pages/`,
      token
    );
  },
};
