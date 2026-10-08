"use client";

import React, { useState } from "react";
import {
  Save,
  RotateCcw,
  Sparkles,
  Clock,
  Target,
  FileText,
  AlertCircle,
  Check,
  Plus,
  Trash2,
} from "lucide-react";
import { CourseSectionItem, UpdateSectionPayload } from "../../types/course";

interface LessonEditorProps {
  lesson: CourseSectionItem;
  onSave: (payload: UpdateSectionPayload) => Promise<void>;
  onCancel?: () => void;
  className?: string;
}

export function LessonEditor({
  lesson,
  onSave,
  onCancel,
  className = "",
}: LessonEditorProps) {
  const [title, setTitle] = useState(lesson.title);
  const [estimatedMinutes, setEstimatedMinutes] = useState(
    lesson.estimated_minutes || 15
  );
  const [summary, setSummary] = useState(lesson.summary || "");
  const [content, setContent] = useState(lesson.content || "");
  const [objectives, setObjectives] = useState<string[]>(
    lesson.objectives && lesson.objectives.length > 0 ? lesson.objectives : [""]
  );

  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAddObjective = () => {
    setObjectives((prev) => [...prev, ""]);
  };

  const handleObjectiveChange = (index: number, val: string) => {
    setObjectives((prev) => {
      const copy = [...prev];
      copy[index] = val;
      return copy;
    });
  };

  const handleRemoveObjective = (index: number) => {
    setObjectives((prev) => prev.filter((_, idx) => idx !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setError(null);
    setSaveSuccess(false);

    try {
      await onSave({
        title,
        estimated_minutes: Number(estimatedMinutes),
        summary,
        content,
        objectives: objectives.filter((o) => o.trim().length > 0),
      });
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: any) {
      setError(err.message || "Erreur lors de la sauvegarde.");
    } finally {
      setIsSaving(false);
    }
  };

  const wordCount = content.trim() ? content.trim().split(/\s+/).length : 0;

  return (
    <form
      onSubmit={handleSubmit}
      className={`bg-white rounded-xl border border-gray-200 shadow-sm p-6 lg:p-8 space-y-6 ${className}`}
    >
      {/* Banner: AI content is completely editable */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200/80 rounded-xl p-4 flex items-start gap-3">
        <Sparkles className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
        <div className="text-xs lg:text-sm text-blue-900 leading-relaxed">
          <span className="font-semibold text-blue-950">
            Édition pédagogique libre :
          </span>{" "}
          Le contenu généré par l'IA est modifiable à tout moment. Vous pouvez corriger, restructurer, ajouter des exemples ou supprimer des notions selon vos exigences d'enseignement.
        </div>
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {saveSuccess && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-sm text-emerald-700 flex items-center gap-2">
          <Check className="w-4 h-4 shrink-0" />
          <span>Modifications enregistrées avec succès !</span>
        </div>
      )}

      {/* Title & Estimated Minutes */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="md:col-span-3 space-y-1">
          <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider">
            Titre de la leçon
          </label>
          <input
            type="text"
            required
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full px-3.5 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Ex : Introduction aux Transformers"
          />
        </div>

        <div className="space-y-1">
          <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider flex items-center gap-1">
            <Clock className="w-3.5 h-3.5 text-gray-400" />
            Durée (min)
          </label>
          <input
            type="number"
            min={1}
            max={300}
            value={estimatedMinutes}
            onChange={(e) => setEstimatedMinutes(Number(e.target.value))}
            className="w-full px-3.5 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Summary */}
      <div className="space-y-1">
        <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider">
          Synthèse / Résumé rapide
        </label>
        <textarea
          rows={2}
          value={summary}
          onChange={(e) => setSummary(e.target.value)}
          className="w-full px-3.5 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 leading-relaxed"
          placeholder="Brève synthèse en 1 ou 2 phrases..."
        />
      </div>

      {/* Pedagogical Objectives */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider flex items-center gap-1.5">
            <Target className="w-3.5 h-3.5 text-emerald-600" />
            Objectifs pédagogiques
          </label>
          <button
            type="button"
            onClick={handleAddObjective}
            className="text-xs text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1"
          >
            <Plus className="w-3 h-3" />
            Ajouter un objectif
          </button>
        </div>

        <div className="space-y-2">
          {objectives.map((obj, idx) => (
            <div key={idx} className="flex items-center gap-2">
              <input
                type="text"
                value={obj}
                onChange={(e) => handleObjectiveChange(idx, e.target.value)}
                placeholder={`Objectif ${idx + 1}...`}
                className="flex-1 px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-xs lg:text-sm text-gray-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              {objectives.length > 1 && (
                <button
                  type="button"
                  onClick={() => handleRemoveObjective(idx)}
                  className="p-2 text-gray-400 hover:text-red-600 rounded-lg transition-colors"
                  title="Supprimer"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Lesson Content Markdown/Text Area */}
      <div className="space-y-1">
        <div className="flex items-center justify-between">
          <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider flex items-center gap-1.5">
            <FileText className="w-3.5 h-3.5 text-blue-600" />
            Contenu didactique complet
          </label>
          <span className="text-xs text-gray-400 font-mono">
            {wordCount} mots
          </span>
        </div>
        <textarea
          rows={14}
          value={content}
          onChange={(e) => setContent(e.target.value)}
          className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-900 font-mono focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 leading-relaxed"
          placeholder="Rédigez ou éditez le contenu pédagogique de cette leçon..."
        />
      </div>

      {/* Form Action Buttons */}
      <div className="pt-4 border-t border-gray-200 flex items-center justify-end gap-3">
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            disabled={isSaving}
            className="px-4 py-2 border border-gray-200 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
          >
            Annuler
          </button>
        )}

        <button
          type="submit"
          disabled={isSaving}
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg text-sm font-semibold transition-colors shadow-sm"
        >
          <Save className="w-4 h-4" />
          {isSaving ? "Enregistrement..." : "Enregistrer la leçon"}
        </button>
      </div>
    </form>
  );
}
