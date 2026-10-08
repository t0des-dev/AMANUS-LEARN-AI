"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  Send,
  Sparkles,
  Command,
  FileText,
  X,
  ChevronDown,
} from "lucide-react";
import { PedagogicalCommandCode } from "../../types/chat";
import { SUGGESTED_PEDAGOGICAL_PROMPTS } from "./SuggestedPrompt";

interface ChatInputProps {
  onSendMessage: (content: string, command?: PedagogicalCommandCode) => void;
  isLoading?: boolean;
  scopedDocumentTitle?: string | null;
  placeholder?: string;
  className?: string;
}

export function ChatInput({
  onSendMessage,
  isLoading = false,
  scopedDocumentTitle,
  placeholder = "Posez une question ou tapez une commande (ex: Explique-moi, Simplifie, Résume...)",
  className = "",
}: ChatInputProps) {
  const [content, setContent] = useState("");
  const [selectedCommand, setSelectedCommand] =
    useState<PedagogicalCommandCode | null>(null);
  const [showCommandsMenu, setShowCommandsMenu] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  // Close command menu when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setShowCommandsMenu(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Auto resize textarea height
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(
        textareaRef.current.scrollHeight,
        160
      )}px`;
    }
  }, [content]);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!content.trim() || isLoading) return;

    onSendMessage(content.trim(), selectedCommand || undefined);
    setContent("");
    setSelectedCommand(null);

    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleSelectCommand = (item: (typeof SUGGESTED_PEDAGOGICAL_PROMPTS)[0]) => {
    setSelectedCommand(item.command);
    setShowCommandsMenu(false);

    // If content doesn't already start with the command prefix, prepend it nicely
    if (!content.trim()) {
      setContent(`${item.prefix} `);
    }
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  };

  return (
    <div
      className={`relative rounded-2xl border border-slate-800 bg-slate-950/90 shadow-2xl backdrop-blur-md transition focus-within:border-indigo-500/70 ${className}`}
    >
      {/* Top bar with active scope & selected command badges */}
      <div className="flex flex-wrap items-center justify-between gap-2 px-3 pt-2.5 text-xs">
        <div className="flex flex-wrap items-center gap-1.5">
          {scopedDocumentTitle && (
            <div className="flex items-center gap-1.5 rounded-full border border-indigo-500/30 bg-indigo-950/40 px-2.5 py-0.5 text-[11px] font-medium text-indigo-300">
              <FileText className="h-3 w-3 text-indigo-400" />
              <span className="max-w-[200px] truncate">{scopedDocumentTitle}</span>
            </div>
          )}

          {selectedCommand && (
            <div className="flex items-center gap-1.5 rounded-full border border-violet-500/40 bg-violet-950/50 px-2.5 py-0.5 text-[11px] font-semibold text-violet-300">
              <Sparkles className="h-3 w-3 text-violet-400" />
              <span>Commande : {selectedCommand}</span>
              <button
                type="button"
                onClick={() => setSelectedCommand(null)}
                className="hover:text-white"
              >
                <X className="h-3 w-3" />
              </button>
            </div>
          )}
        </div>

        {/* Command picker trigger */}
        <div className="relative" ref={menuRef}>
          <button
            type="button"
            onClick={() => setShowCommandsMenu(!showCommandsMenu)}
            className="flex items-center gap-1 rounded-lg border border-slate-800 bg-slate-900/80 px-2 py-1 text-[11px] font-medium text-slate-300 transition hover:border-indigo-500/40 hover:text-white"
          >
            <Command className="h-3 w-3 text-indigo-400" />
            <span>Commandes pédagogiques</span>
            <ChevronDown className="h-3 w-3 text-slate-400" />
          </button>

          {showCommandsMenu && (
            <div className="absolute right-0 bottom-full mb-2 w-72 rounded-xl border border-slate-800 bg-slate-900/95 p-2 shadow-xl backdrop-blur-xl z-50">
              <div className="px-2 py-1 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                Choisir une posture pédagogique
              </div>
              <div className="mt-1 space-y-1">
                {SUGGESTED_PEDAGOGICAL_PROMPTS.map((item) => (
                  <button
                    key={item.command}
                    type="button"
                    onClick={() => handleSelectCommand(item)}
                    className="flex w-full items-center gap-2.5 rounded-lg px-2.5 py-1.5 text-left text-xs transition hover:bg-indigo-950/50 hover:text-white text-slate-300"
                  >
                    <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded bg-slate-800">
                      {item.icon}
                    </span>
                    <div className="overflow-hidden">
                      <div className="font-semibold">{item.label}</div>
                      <div className="truncate text-[10px] text-slate-400">
                        {item.description}
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Main input form */}
      <form onSubmit={handleSubmit} className="flex items-end gap-2 p-3">
        <textarea
          ref={textareaRef}
          value={content}
          onChange={(e) => setContent(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          rows={1}
          disabled={isLoading}
          className="flex-1 max-h-40 resize-none bg-transparent px-1 text-sm text-slate-100 placeholder-slate-500 focus:outline-none"
        />

        <button
          type="submit"
          disabled={!content.trim() || isLoading}
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 text-white shadow-md shadow-indigo-500/25 transition hover:scale-105 active:scale-95 disabled:pointer-events-none disabled:opacity-40"
          title="Envoyer (Entrée)"
        >
          <Send className="h-4 w-4" />
        </button>
      </form>
    </div>
  );
}
