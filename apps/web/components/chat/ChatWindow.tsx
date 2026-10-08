"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import {
  Sparkles,
  ArrowLeft,
  FileText,
  AlertCircle,
  GraduationCap,
  MessageSquare,
} from "lucide-react";
import {
  ChatMessage as ChatMessageType,
  ChatSession,
  PedagogicalCommandCode,
  SourceCitation as SourceCitationType,
} from "../../types/chat";
import { chatService } from "../../services/chatService";
import { ChatMessage } from "./ChatMessage";
import { ChatInput } from "./ChatInput";
import { TypingIndicator } from "./TypingIndicator";
import { SuggestedPrompt } from "./SuggestedPrompt";

interface ChatWindowProps {
  session: ChatSession;
  token: string;
  onSessionUpdated?: (updatedSession: ChatSession) => void;
  className?: string;
}

export function ChatWindow({
  session,
  token,
  onSessionUpdated,
  className = "",
}: ChatWindowProps) {
  const [messages, setMessages] = useState<ChatMessageType[]>(
    session.messages || []
  );
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  const scrollToBottom = (behavior: ScrollBehavior = "smooth") => {
    messagesEndRef.current?.scrollIntoView({ behavior });
  };

  useEffect(() => {
    setMessages(session.messages || []);
    scrollToBottom("auto");
  }, [session.id, session.messages]);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isStreaming]);

  const handleSendMessage = async (
    content: string,
    command?: PedagogicalCommandCode
  ) => {
    if (!content.trim() || isLoading) return;

    setError(null);
    setIsLoading(true);

    const tempUserId = `user-${Date.now()}`;
    const userMessage: ChatMessageType = {
      id: tempUserId,
      session_id: session.id,
      role: "user",
      content,
      command: command || null,
      sources: [],
      created_at: new Date().toISOString(),
    };

    const tempAssistantId = `assistant-${Date.now()}`;
    const initialAssistantMessage: ChatMessageType = {
      id: tempAssistantId,
      session_id: session.id,
      role: "assistant",
      content: "",
      command: command || null,
      sources: [],
      created_at: new Date().toISOString(),
    };

    // Optimistically append user message
    setMessages((prev) => [...prev, userMessage]);

    try {
      let hasStartedReceiving = false;

      await chatService.sendMessageStream(
        token,
        session.id,
        {
          content,
          command,
          document_id: session.document?.id,
          stream: true,
        },
        {
          onStart: () => {
            // First event from backend
          },
          onToken: (tokenChunk: string) => {
            if (!hasStartedReceiving) {
              hasStartedReceiving = true;
              setIsLoading(false);
              setIsStreaming(true);
              setMessages((prev) => [...prev, initialAssistantMessage]);
            }

            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === tempAssistantId
                  ? { ...msg, content: msg.content + tokenChunk }
                  : msg
              )
            );
          },
          onDone: ({
            message_id,
            sources,
            content: finalContent,
            command: finalCommand,
          }) => {
            setIsStreaming(false);
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === tempAssistantId
                  ? {
                      ...msg,
                      id: message_id,
                      content: finalContent || msg.content,
                      sources,
                      command: (finalCommand as PedagogicalCommandCode) || msg.command,
                    }
                  : msg
              )
            );

            // Update session updated_at
            if (onSessionUpdated) {
              onSessionUpdated({
                ...session,
                updated_at: new Date().toISOString(),
              });
            }
          },
          onError: async (err) => {
            // Fallback to sync API
            try {
              const res = await chatService.sendMessageSync(token, session.id, {
                content,
                command,
                document_id: session.document?.id,
              });

              setMessages((prev) => {
                const filtered = prev.filter(
                  (m) => m.id !== tempAssistantId && m.id !== tempUserId
                );
                return [
                  ...filtered,
                  res.user_message,
                  res.assistant_message,
                ];
              });
            } catch (fallbackErr: any) {
              setError(
                fallbackErr.message ||
                  err.message ||
                  "Une erreur est survenue lors de la réponse de l'assistant."
              );
            } finally {
              setIsLoading(false);
              setIsStreaming(false);
            }
          },
        }
      );
    } catch (err: any) {
      setError(err.message || "Erreur de transmission.");
      setIsLoading(false);
      setIsStreaming(false);
    }
  };

  return (
    <div
      className={`flex h-full flex-col overflow-hidden rounded-2xl border border-slate-800 bg-slate-950/70 shadow-2xl backdrop-blur-xl ${className}`}
    >
      {/* Top Header */}
      <div className="flex h-16 shrink-0 items-center justify-between border-b border-slate-800 px-4 sm:px-6">
        <div className="flex items-center gap-3">
          <Link
            href="/chat"
            className="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-800 bg-slate-900 text-slate-400 transition hover:bg-slate-800 hover:text-white md:hidden"
          >
            <ArrowLeft className="h-4 w-4" />
          </Link>

          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 text-white shadow-md shadow-indigo-500/20">
            <GraduationCap className="h-5 w-5" />
          </div>

          <div>
            <h1 className="text-sm sm:text-base font-bold text-white line-clamp-1">
              {session.title || "Session pédagogique"}
            </h1>
            <div className="flex items-center gap-2 text-[11px] text-slate-400">
              <span className="flex items-center gap-1 text-emerald-400">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                RAG Actif
              </span>
              {session.document && (
                <>
                  <span>•</span>
                  <span className="flex items-center gap-1 text-indigo-300">
                    <FileText className="h-3 w-3" />
                    {session.document.title}
                  </span>
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Message scroll area */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
        {messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center text-center p-4">
            <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-tr from-indigo-600/30 to-violet-500/20 border border-indigo-500/30 text-indigo-400 shadow-xl shadow-indigo-950/40">
              <Sparkles className="h-7 w-7" />
            </div>
            <h3 className="text-lg font-bold text-slate-100">
              Comment puis-je vous aider aujourd&apos;hui ?
            </h3>
            <p className="mt-1 max-w-md text-xs sm:text-sm text-slate-400">
              Je suis votre tuteur pédagogique. Je me base strictement sur vos
              documents de cours pour vous expliquer, vulgariser ou tester vos
              connaissances.
            </p>

            <div className="mt-6 w-full max-w-2xl">
              <SuggestedPrompt
                layout="pills"
                onSelectPrompt={(prompt, cmd) => handleSendMessage(prompt, cmd)}
              />
            </div>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <ChatMessage
                key={message.id}
                message={message}
                isStreaming={
                  isStreaming &&
                  message.role === "assistant" &&
                  message.id.startsWith("assistant-")
                }
              />
            ))}

            {isLoading && !isStreaming && (
              <div className="my-2">
                <TypingIndicator />
              </div>
            )}
          </>
        )}

        {error && (
          <div className="flex items-center gap-2 rounded-xl border border-red-500/40 bg-red-950/30 p-3 text-xs text-red-300">
            <AlertCircle className="h-4 w-4 shrink-0 text-red-400" />
            <span>{error}</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Bottom input area */}
      <div className="shrink-0 border-t border-slate-800/80 bg-slate-950/80 p-3 sm:p-4">
        <ChatInput
          onSendMessage={handleSendMessage}
          isLoading={isLoading || isStreaming}
          scopedDocumentTitle={session.document?.title}
        />
      </div>
    </div>
  );
}
