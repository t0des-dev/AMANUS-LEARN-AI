"use client";

import React from "react";
import { Plus, ChevronUp, ChevronDown, Trash2, Layout, Layers } from "lucide-react";
import { PresentationSlide } from "../../types/presentation";

interface SlideNavigatorProps {
  slides: PresentationSlide[];
  activeSlideId: string | null;
  onSelectSlide: (slideId: string) => void;
  onAddSlide: () => void;
  onDeleteSlide: (slideId: string) => void;
  onMoveSlide: (slideId: string, direction: "up" | "down") => void;
  isSaving?: boolean;
}

export const SlideNavigator: React.FC<SlideNavigatorProps> = ({
  slides,
  activeSlideId,
  onSelectSlide,
  onAddSlide,
  onDeleteSlide,
  onMoveSlide,
  isSaving = false,
}) => {
  return (
    <aside className="w-72 bg-slate-900 border-r border-slate-800 flex flex-col h-full select-none">
      {/* Header */}
      <div className="p-4 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2 text-slate-200 font-semibold text-sm">
          <Layers className="w-4 h-4 text-indigo-400" />
          <span>Plan des Slides</span>
          <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 font-mono">
            {slides.length}
          </span>
        </div>
        <button
          onClick={onAddSlide}
          disabled={isSaving}
          title="Ajouter une slide"
          className="flex items-center gap-1 text-xs bg-indigo-600 hover:bg-indigo-500 text-white font-medium px-2.5 py-1.5 rounded-lg transition shadow-sm hover:shadow active:scale-95 disabled:opacity-50"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Ajouter</span>
        </button>
      </div>

      {/* Slide Thumbnails List */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2.5 custom-scrollbar">
        {slides.length === 0 ? (
          <div className="text-center py-12 px-4 text-slate-500 text-sm">
            <Layout className="w-8 h-8 mx-auto mb-2 opacity-40" />
            Aucune diapositive. Cliquez sur « Ajouter » pour commencer.
          </div>
        ) : (
          slides.map((slide, index) => {
            const isActive = slide.id === activeSlideId;
            const isFirst = index === 0;
            const isLast = index === slides.length - 1;

            return (
              <div
                key={slide.id}
                onClick={() => onSelectSlide(slide.id)}
                className={`group relative rounded-xl p-3 border transition cursor-pointer ${
                  isActive
                    ? "bg-slate-800/90 border-indigo-500 shadow-md shadow-indigo-950/40"
                    : "bg-slate-900/60 border-slate-800/80 hover:bg-slate-800/50 hover:border-slate-700"
                }`}
              >
                {/* Top bar inside card */}
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center gap-1.5">
                    <span
                      className={`text-xs font-mono font-bold px-1.5 py-0.5 rounded ${
                        isActive
                          ? "bg-indigo-500 text-white"
                          : "bg-slate-800 text-slate-400 group-hover:text-slate-300"
                      }`}
                    >
                      #{slide.slide_number}
                    </span>
                    <span className="text-[10px] text-slate-500 uppercase tracking-wider">
                      Slide
                    </span>
                  </div>

                  {/* Actions: Reorder & Delete */}
                  <div className="flex items-center gap-0.5 opacity-60 group-hover:opacity-100 transition">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onMoveSlide(slide.id, "up");
                      }}
                      disabled={isFirst || isSaving}
                      title="Monter la diapositive"
                      className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-700 disabled:opacity-20 disabled:hover:bg-transparent"
                    >
                      <ChevronUp className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onMoveSlide(slide.id, "down");
                      }}
                      disabled={isLast || isSaving}
                      title="Descendre la diapositive"
                      className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-700 disabled:opacity-20 disabled:hover:bg-transparent"
                    >
                      <ChevronDown className="w-3.5 h-3.5" />
                    </button>
                    {slides.length > 1 && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          if (confirm(`Supprimer la slide #${slide.slide_number} : "${slide.title}" ?`)) {
                            onDeleteSlide(slide.id);
                          }
                        }}
                        disabled={isSaving}
                        title="Supprimer la diapositive"
                        className="p-1 rounded text-rose-400 hover:text-rose-200 hover:bg-rose-950/60 disabled:opacity-20"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                </div>

                {/* Slide Title preview */}
                <h4
                  className={`text-xs font-medium truncate ${
                    isActive ? "text-white font-semibold" : "text-slate-300"
                  }`}
                >
                  {slide.title || "Sans titre"}
                </h4>

                {/* Content snippet preview */}
                <p className="text-[11px] text-slate-500 line-clamp-2 mt-1 leading-relaxed">
                  {slide.content || "Aucun contenu didactique rédigé..."}
                </p>
              </div>
            );
          })
        )}
      </div>
    </aside>
  );
};
