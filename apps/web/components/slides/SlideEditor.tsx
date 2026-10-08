"use client";

import React, { useState, useEffect } from "react";
import {
  Save,
  FileEdit,
  ListPlus,
  MessageSquare,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
} from "lucide-react";
import { PresentationSlide, UpdateSlidePayload } from "../../types/presentation";

interface SlideEditorProps {
  slide: PresentationSlide | null;
  onSave: (slideId: string, payload: UpdateSlidePayload) => Promise<void>;
  isSaving: boolean;
}

export const SlideEditor: React.FC<SlideEditorProps> = ({
  slide,
  onSave,
  isSaving,
}) => {
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [speakerNotes, setSpeakerNotes] = useState("");
  const [imagePrompt, setImagePrompt] = useState("");
  const [isDirty, setIsDirty] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  // Sync internal state with active slide
  useEffect(() => {
    if (slide) {
      setTitle(slide.title || "");
      setContent(slide.content || "");
      setSpeakerNotes(slide.speaker_notes || "");
      setImagePrompt(slide.image_prompt || "");
      setIsDirty(false);
      setSavedSuccess(false);
    }
  }, [slide]);

  if (!slide) {
    return (
      <aside className="w-80 lg:w-96 bg-slate-900 border-l border-slate-800 p-6 flex items-center justify-center text-slate-500 text-sm">
        Sélectionnez une diapositive pour commencer l&apos;édition.
      </aside>
    );
  }

  const handleFieldChange = (setter: React.Dispatch<React.SetStateAction<string>>) => {
    return (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
      setter(e.target.value);
      setIsDirty(true);
      setSavedSuccess(false);
    };
  };

  const handleAddBullet = () => {
    setContent((prev) => (prev ? `${prev}\n• Nouvelle idée clé` : "• Nouvelle idée clé"));
    setIsDirty(true);
  };

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!slide) return;

    try {
      await onSave(slide.id, {
        title: title.trim(),
        content: content.trim(),
        speaker_notes: speakerNotes.trim(),
        image_prompt: imagePrompt.trim(),
      });
      setIsDirty(false);
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 2500);
    } catch {
      // handled by parent or toast
    }
  };

  return (
    <aside className="w-80 lg:w-96 bg-slate-900 border-l border-slate-800 flex flex-col h-full overflow-hidden">
      {/* Editor Header */}
      <div className="p-4 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileEdit className="w-4 h-4 text-indigo-400" />
          <h3 className="text-sm font-semibold text-slate-200">
            Éditeur de Slide #{slide.slide_number}
          </h3>
        </div>

        {/* Status indicator */}
        <div className="flex items-center gap-1.5 text-xs">
          {isSaving ? (
            <span className="text-indigo-400 animate-pulse font-medium">Sauvegarde...</span>
          ) : savedSuccess ? (
            <span className="text-emerald-400 flex items-center gap-1 font-medium">
              <CheckCircle2 className="w-3.5 h-3.5" /> Enregistré
            </span>
          ) : isDirty ? (
            <span className="text-amber-400 font-medium">Modifié</span>
          ) : (
            <span className="text-slate-500">À jour</span>
          )}
        </div>
      </div>

      {/* Editor Form */}
      <form onSubmit={handleFormSubmit} className="flex-1 overflow-y-auto p-4 space-y-5 custom-scrollbar">
        {/* Title Input */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
            Titre de la diapositive
          </label>
          <input
            type="text"
            value={title}
            onChange={handleFieldChange(setTitle)}
            placeholder="Ex: Les Fondements de l'Architecture"
            className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-slate-100 text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition"
          />
        </div>

        {/* Content / Bullet points Input */}
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400">
              Contenu didactique (Points clés)
            </label>
            <button
              type="button"
              onClick={handleAddBullet}
              className="text-[11px] font-medium text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
            >
              <ListPlus className="w-3 h-3" />
              + Ajouter puce
            </button>
          </div>
          <textarea
            rows={6}
            value={content}
            onChange={handleFieldChange(setContent)}
            placeholder="• Premier point pédagogique&#10;• Deuxième notion clé&#10;• Exemple d'application"
            className="w-full px-3 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-100 text-xs md:text-sm font-sans focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition resize-y leading-relaxed"
          />
          <p className="text-[11px] text-slate-500 mt-1">
            Chaque ligne commençant par une puce ou un tiret s&apos;affichera sous forme de point clé.
          </p>
        </div>

        {/* Speaker Notes */}
        <div>
          <div className="flex items-center gap-1.5 mb-1.5">
            <MessageSquare className="w-3.5 h-3.5 text-indigo-400" />
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400">
              Notes pour l&apos;orateur
            </label>
          </div>
          <textarea
            rows={4}
            value={speakerNotes}
            onChange={handleFieldChange(setSpeakerNotes)}
            placeholder="Conseils de présentation, anecdotes et explications verbales détaillées..."
            className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-slate-100 text-xs focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition resize-y"
          />
        </div>

        {/* Visual / Image Prompt */}
        <div>
          <div className="flex items-center gap-1.5 mb-1.5">
            <Sparkles className="w-3.5 h-3.5 text-amber-400" />
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400">
              Idée visuelle / Prompt d&apos;illustration
            </label>
          </div>
          <input
            type="text"
            value={imagePrompt}
            onChange={handleFieldChange(setImagePrompt)}
            placeholder="Ex: Schéma synoptique illustrant le flux des données"
            className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-slate-100 text-xs focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition"
          />
        </div>

        {/* Submit button */}
        <div className="pt-2">
          <button
            type="submit"
            disabled={!isDirty || isSaving}
            className="w-full py-2.5 px-4 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-500 disabled:cursor-not-allowed text-white font-semibold text-xs rounded-xl shadow-md transition flex items-center justify-center gap-2"
          >
            <Save className="w-4 h-4" />
            <span>Enregistrer la slide</span>
          </button>
        </div>
      </form>
    </aside>
  );
};
