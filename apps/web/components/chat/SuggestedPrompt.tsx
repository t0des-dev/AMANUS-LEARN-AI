"use client";

import React from "react";
import {
  Sparkles,
  Zap,
  FileText,
  Layers,
  HelpCircle,
  CheckCircle,
  GitCompare,
  Bookmark,
} from "lucide-react";
import { PedagogicalCommandCode } from "../../types/chat";

export interface SuggestedPromptItem {
  command: PedagogicalCommandCode;
  label: string;
  prefix: string;
  description: string;
  icon: React.ReactNode;
  samplePrompt: string;
}

export const SUGGESTED_PEDAGOGICAL_PROMPTS: SuggestedPromptItem[] = [
  {
    command: "EXPLAIN",
    label: "Explique-moi",
    prefix: "Explique-moi",
    description: "Explication claire, rigoureuse et progressive étape par étape.",
    icon: <Sparkles className="h-4 w-4 text-indigo-400" />,
    samplePrompt: "Explique-moi les concepts fondamentaux de ce chapitre",
  },
  {
    command: "SIMPLIFY",
    label: "Simplifie",
    prefix: "Simplifie",
    description: "Vulgarisation accessible pour débutant avec analogies concrètes.",
    icon: <Zap className="h-4 w-4 text-amber-400" />,
    samplePrompt: "Simplifie le mécanisme principal comme si j'étais débutant",
  },
  {
    command: "SUMMARY",
    label: "Résume",
    prefix: "Résume",
    description: "Synthèse concise des points clés et des idées maîtresses.",
    icon: <FileText className="h-4 w-4 text-sky-400" />,
    samplePrompt: "Résume les points essentiels et les conclusions à retenir",
  },
  {
    command: "EXAMPLE",
    label: "Donne un exemple",
    prefix: "Donne un exemple de",
    description: "Cas pratiques, scénarios réalistes et illustrations concrètes.",
    icon: <Layers className="h-4 w-4 text-emerald-400" />,
    samplePrompt: "Donne un exemple concret d'application de cette notion",
  },
  {
    command: "QUIZ",
    label: "Interroge-moi",
    prefix: "Interroge-moi sur",
    description: "Questions interactives stimulantes pour valider tes acquis.",
    icon: <HelpCircle className="h-4 w-4 text-purple-400" />,
    samplePrompt: "Interroge-moi avec 3 questions pour tester ma compréhension",
  },
  {
    command: "REVISION",
    label: "Fais-moi réviser",
    prefix: "Fais-moi réviser",
    description: "Fiche express de révision, points d'attention et pièges fréquents.",
    icon: <CheckCircle className="h-4 w-4 text-rose-400" />,
    samplePrompt: "Fais-moi réviser les définitions clés et les pièges classiques",
  },
  {
    command: "COMPARE",
    label: "Compare",
    prefix: "Compare",
    description: "Comparaison méthodique, points communs, nuances et cas d'usage.",
    icon: <GitCompare className="h-4 w-4 text-teal-400" />,
    samplePrompt: "Compare les différentes approches présentées dans le document",
  },
  {
    command: "DEFINE",
    label: "Définis",
    prefix: "Définis",
    description: "Définition académique exacte, nette et contextualisée.",
    icon: <Bookmark className="h-4 w-4 text-blue-400" />,
    samplePrompt: "Définis précisément le concept central et son importance",
  },
];

interface SuggestedPromptProps {
  onSelectPrompt: (promptText: string, command: PedagogicalCommandCode) => void;
  layout?: "grid" | "pills";
  className?: string;
}

export function SuggestedPrompt({
  onSelectPrompt,
  layout = "grid",
  className = "",
}: SuggestedPromptProps) {
  if (layout === "pills") {
    return (
      <div className={`flex flex-wrap items-center gap-1.5 ${className}`}>
        {SUGGESTED_PEDAGOGICAL_PROMPTS.map((item) => (
          <button
            key={item.command}
            type="button"
            onClick={() => onSelectPrompt(item.samplePrompt, item.command)}
            className="group flex items-center gap-1.5 rounded-full border border-slate-800 bg-slate-900/80 px-3 py-1.5 text-xs text-slate-300 transition hover:border-indigo-500/50 hover:bg-indigo-950/40 hover:text-white"
          >
            <span className="transition group-hover:scale-110">{item.icon}</span>
            <span className="font-medium">{item.label}</span>
          </button>
        ))}
      </div>
    );
  }

  return (
    <div className={`grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 ${className}`}>
      {SUGGESTED_PEDAGOGICAL_PROMPTS.map((item) => (
        <button
          key={item.command}
          type="button"
          onClick={() => onSelectPrompt(item.samplePrompt, item.command)}
          className="group flex flex-col items-start rounded-xl border border-slate-800/80 bg-slate-900/60 p-3.5 text-left transition hover:-translate-y-0.5 hover:border-indigo-500/40 hover:bg-slate-900 hover:shadow-lg hover:shadow-indigo-950/20"
        >
          <div className="mb-2 flex h-8 w-8 items-center justify-center rounded-lg bg-slate-800/80 transition group-hover:bg-indigo-900/30">
            {item.icon}
          </div>
          <span className="text-sm font-semibold text-slate-100 group-hover:text-indigo-300 transition">
            {item.label}
          </span>
          <p className="mt-1 text-xs text-slate-400 line-clamp-2">
            {item.description}
          </p>
        </button>
      ))}
    </div>
  );
}
