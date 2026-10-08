import {
  ChatMessage,
  ChatSession,
  CreateChatSessionPayload,
  PedagogicalCommand,
  SendMessagePayload,
  SendMessageResponse,
  SourceCitation,
} from "../types/chat";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

async function chatFetch<T>(
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
    let errorMessage = "Une erreur est survenue lors de l'opération sur le chat.";
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

export const chatService = {
  async listSessions(
    token: string,
    filters?: { organization_id?: string; document_id?: string }
  ): Promise<ChatSession[]> {
    const params = new URLSearchParams();
    if (filters?.organization_id) {
      params.append("organization_id", filters.organization_id);
    }
    if (filters?.document_id) {
      params.append("document_id", filters.document_id);
    }
    const query = params.toString() ? `?${params.toString()}` : "";
    const data = await chatFetch<PaginatedResponse<ChatSession> | ChatSession[]>(
      `chat/sessions/${query}`,
      token
    );

    if (Array.isArray(data)) {
      return data;
    }
    return data.results || [];
  },

  async getSession(token: string, id: string): Promise<ChatSession> {
    return chatFetch<ChatSession>(`chat/sessions/${id}/`, token);
  },

  async createSession(
    token: string,
    payload: CreateChatSessionPayload
  ): Promise<ChatSession> {
    return chatFetch<ChatSession>("chat/sessions/", token, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async deleteSession(token: string, id: string): Promise<void> {
    await chatFetch<void>(`chat/sessions/${id}/`, token, {
      method: "DELETE",
    });
  },

  async listCommands(token: string): Promise<PedagogicalCommand[]> {
    const res = await chatFetch<{ commands: PedagogicalCommand[] }>(
      "chat/commands/",
      token
    );
    return res.commands || [];
  },

  async sendMessageSync(
    token: string,
    sessionId: string,
    payload: SendMessagePayload
  ): Promise<SendMessageResponse> {
    return chatFetch<SendMessageResponse>(
      `chat/sessions/${sessionId}/messages/`,
      token,
      {
        method: "POST",
        body: JSON.stringify({ ...payload, stream: false }),
      }
    );
  },

  async sendMessageStream(
    token: string,
    sessionId: string,
    payload: SendMessagePayload,
    callbacks: {
      onStart?: (data: { user_message_id?: string; command?: string }) => void;
      onToken: (token: string) => void;
      onDone: (data: {
        message_id: string;
        sources: SourceCitation[];
        content: string;
        command?: string;
      }) => void;
      onError?: (err: Error) => void;
    }
  ): Promise<void> {
    const url = `${API_BASE_URL.replace(/\/$/, "")}/chat/sessions/${sessionId}/messages/`;

    try {
      const response = await fetch(url, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
          Accept: "text/event-stream",
        },
        body: JSON.stringify({ ...payload, stream: true }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.detail ||
            errorData.content ||
            `Erreur lors du streaming (status ${response.status})`
        );
      }

      if (!response.body) {
        throw new Error("Flux de streaming non supporté par le navigateur.");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        // Keep the last partial line in buffer
        buffer = lines.pop() || "";

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed || !trimmed.startsWith("data: ")) continue;

          try {
            const jsonStr = trimmed.slice(6);
            const eventData = JSON.parse(jsonStr);

            if (eventData.type === "start" && callbacks.onStart) {
              callbacks.onStart(eventData);
            } else if (eventData.type === "token") {
              callbacks.onToken(eventData.content || "");
            } else if (eventData.type === "done") {
              callbacks.onDone({
                message_id: eventData.message_id,
                sources: eventData.sources || [],
                content: eventData.content || "",
                command: eventData.command,
              });
            }
          } catch (e) {
            // Ignore partial SSE parsing issues
          }
        }
      }
    } catch (err: any) {
      if (callbacks.onError) {
        callbacks.onError(err instanceof Error ? err : new Error(String(err)));
      } else {
        throw err;
      }
    }
  },
};
