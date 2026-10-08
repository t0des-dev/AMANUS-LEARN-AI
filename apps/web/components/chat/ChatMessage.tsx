"use client";

import React, { useState } from "react";
import {
  Sparkles,
  User,
  Copy,
  Check,
  Bookmark,
  Zap,
  FileText,
  Layers,
  HelpCircle,
  CheckCircle,
  GitCompare,
} from "lucide-react";
import { ChatMessage as ChatMessageType, PedagogicalCommandCode } from "../../types/chat";
import { SourceCitation } from "./SourceCitation";

interface ChatMessageProps {
  message: ChatMessageType;
  isStreaming?: boolean;
}

const COMMAND_BADGES: Record<
  string,
  { label: string; icon: React.ReactNode; color: string }
> = {
  EXPLAIN: {
    label: "Explique-moi",
    icon: <Sparkles className="h-3 w-3" />,
    color: "bg-indigo-500/10 text-indigo-400 border-indigo-500/30",
  },
  SIMPLIFY: {
    label: "Simplifie",
    icon: <Zap className="h-3 w-3" />,
    color: "bg-amber-500/10 text-amber-400 border-amber-500/30",
  },
  SUMMARY: {
    label: "Résume",
    icon: <FileText className="h-3 w-3" />,
    color: "bg-sky-500/10 text-sky-400 border-sky-500/30",
  },
  EXAMPLE: {
    label: "Exemple",
    icon: <Layers className="h-3 w-3" />,
    color: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
  },
  QUIZ: {
    label: "Interroge-moi",
    icon: <HelpCircle className="h-3 w-3" />,
    color: "bg-purple-500/10 text-purple-400 border-purple-500/30",
  },
  REVISION: {
    label: "Révision",
    icon: <CheckCircle className="h-3 w-3" />,
    color: "bg-rose-500/10 text-rose-400 border-rose-500/30",
  },
  COMPARE: {
    label: "Compare",
    icon: <GitCompare className="h-3 w-3" />,
    color: "bg-teal-500/10 text-teal-400 border-teal-500/30",
  },
  DEFINE: {
    label: "Définis",
    icon: <Bookmark className="h-3 w-3" />,
    color: "bg-blue-500/10 text-blue-400 border-blue-500/30",
  },
};

export function ChatMessage({ message, isStreaming = false }: ChatMessageProps) {
  const [copied, setCopied] = useState(false);
  const [activeCitationId, setActiveCitationId] = useState<number | null>(null);

  const isUser = message.role === "user";
  const commandBadge = message.command ? COMMAND_BADGES[message.command] : null;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback
    }
  };

  // Convert inline citations like [1], [2] into interactive highlight buttons
  const renderFormattedContent = (text: string) => {
    if (!text) return null;

    const parts = text.split(/(\[\d+\])/g);
    return parts.map((part, index) => {
      const match = part.match(/^\[(\d+)\]$/);
      if (match) {
        const citationId = parseInt(match[1], 10);
        const hasSource = message.sources?.some(
          (s) => s.citation_id === citationId
        );

        if (hasSource) {
          const isSelected = activeCitationId === citationId;
          return (
            <button
              key={index}
              type="button"
              onClick={() =>
                setActiveCitationId((prev) => (prev === citationId ? null : citationId))
              }
              className={`inline-flex items-center px-1.5 py-0.5 mx-0.5 rounded text-[11px] font-bold transition ${
                isSelected
                  ? "bg-indigo-500 text-white ring-2 ring-indigo-300"
                  : "bg-indigo-900/60 text-indigo-300 hover:bg-indigo-700/60"
              }`}
            >
              {part}
            </button>
          );
        }
      }

      return <span key={index}>{part}</span>;
    });
  };

  return (
    <div
      className={`group flex gap-3.5 my-3 ${
        isUser ? "flex-row-reverse" : "flex-row"
      }`}
    >
      {/* Avatar */}
      <div
        className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl shadow-md ${
          isUser
            ? "bg-gradient-to-tr from-slate-700 to-slate-600 text-slate-200"
            : "bg-gradient-to-tr from-indigo-600 to-violet-500 text-white shadow-indigo-500/20"
        }`}
      >
        {isUser ? <User className="h-4 w-4" /> : <Sparkles className="h-4 w-4" />}
      </div>

      {/* Bubble container */}
      <div
        className={`flex flex-col max-w-[85%] sm:max-w-[78%] ${
          isUser ? "items-end" : "items-start"
        }`}
      >
        {/* Header / Badges */}
        <div className="mb-1 flex items-center gap-2 text-xs text-slate-400">
          <span className="font-semibold text-slate-300">
            {isUser ? "Vous" : "AI Tutor"}
          </span>

          {commandBadge && (
            <span
              className={`flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-semibold ${commandBadge.color}`}
            >
              {commandBadge.icon}
              <span>{commandBadge.label}</span>
            </span>
          )}

          <span className="text-[10px] text-slate-500">
            {new Date(message.created_at).toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </span>
        </div>

        {/* Message bubble */}
        <div
          className={`relative rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-sm transition ${
            isUser
              ? "rounded-tr-xs bg-indigo-600 text-white"
              : "rounded-tl-xs border border-slate-800 bg-slate-900/90 text-slate-200 backdrop-blur-md"
          }`}
        >
          <div className="whitespace-pre-wrap font-normal break-words">
            {renderFormattedContent(message.content)}
            {isStreaming && (
              <span className="inline-block h-3.5 w-1.5 ml-1 bg-indigo-400 animate-pulse" />
            )}
          </div>

          {/* Copy button */}
          {!isUser && !isStreaming && (
            <button
              type="button"
              onClick={handleCopy}
              className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition rounded p-1 text-slate-400 hover:text-white hover:bg-slate-800"
              title="Copier le message"
            >
              {copied ? (
                <Check className="h-3.5 w-3.5 text-emerald-400" />
              ) : (
                <Copy className="h-3.5 w-3.5" />
              )}
            </button>
          )}

          {/* Source Citations */}
          {!isUser && message.sources && message.sources.length > 0 && (
            <SourceCitation
              sources={message.sources}
              activeCitationId={activeCitationId}
              onSelectCitation={(id) => setActiveCitationId(id)}
            />
          )}
        </div>
      </div>
    </div>
  );
}
