"use client";

import React from "react";
import Link from "next/link";
import {
  Clock,
  Target,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Edit3,
  Bookmark,
  Share2,
} from "lucide-react";
import { CourseSectionItem } from "../../types/course";
import { AudioGenerationButton } from "../../components/audio/AudioGenerationButton";

interface LessonViewerProps {
  courseId: string;
  lesson: CourseSectionItem;
  isCompleted?: boolean;
  onToggleComplete?: () => void;
  onNext?: () => void;
  onPrev?: () => void;
  hasPrev?: boolean;
  hasNext?: boolean;
  isTeacher?: boolean;
}

export function LessonViewer({
  courseId,
  lesson,
  isCompleted = false,
  onToggleComplete,
  onNext,
  onPrev,
  hasPrev = false,
  hasNext = false,
  isTeacher = false,
}: LessonViewerProps) {
  return (
    <article className="max-w-4xl mx-auto py-8 px-6 lg:px-10 bg-white min-h-screen">
      {/* Top action bar */}
      <div className="flex items-center justify-between border-b border-gray-100 pb-4 mb-6">
        <div className="flex items-center gap-3 text-xs text-gray-500">
          <span className="flex items-center gap-1">
            <Clock className="w-3.5 h-3.5 text-purple-500" />
            {lesson.estimated_minutes} min de lecture
          </span>
          <span>•</span>
          <span className="text-gray-400">Ordre #{lesson.order + 1}</span>
        </div>

        <div className="flex items-center gap-2">
          {isTeacher && (
            <Link
              href={`/courses/${courseId}/edit?section=${lesson.id}`}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-gray-200 text-xs font-medium text-gray-700 hover:bg-gray-50 transition-colors"
            >
              <Edit3 className="w-3.5 h-3.5 text-blue-600" />
              Modifier cette leçon
            </Link>
          )}

          {onToggleComplete && (
            <button
              type="button"
              onClick={onToggleComplete}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                isCompleted
                  ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              }`}
            >
              <CheckCircle2
                className={`w-3.5 h-3.5 ${
                  isCompleted ? "text-emerald-600" : "text-gray-400"
                }`}
              />
              {isCompleted ? "Terminée" : "Marquer comme terminée"}
            </button>
          )}
        </div>
      </div>

      {/* Lesson Title & Audio Action */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <h1 className="text-2xl lg:text-3xl font-extrabold text-gray-900 leading-tight">
          {lesson.title}
        </h1>
        <AudioGenerationButton
          sectionId={lesson.id}
          sectionTitle={lesson.title}
        />
      </div>

      {/* Pedagogical Objectives Box */}
      {lesson.objectives && lesson.objectives.length > 0 && (
        <div className="bg-emerald-50/70 border border-emerald-200/80 rounded-xl p-5 mb-8">
          <div className="flex items-center gap-2 text-emerald-800 text-sm font-semibold mb-3">
            <Target className="w-4 h-4 text-emerald-600" />
            Objectifs pédagogiques de cette leçon
          </div>
          <ul className="space-y-2">
            {lesson.objectives.map((obj, idx) => (
              <li
                key={idx}
                className="text-xs lg:text-sm text-emerald-900 flex items-start gap-2"
              >
                <span className="text-emerald-500 font-bold">•</span>
                <span>{obj}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Lesson Summary if available */}
      {lesson.summary && (
        <div className="bg-blue-50/60 border-l-4 border-blue-500 p-4 rounded-r-lg mb-8">
          <p className="text-xs lg:text-sm text-blue-900 font-medium italic">
            « {lesson.summary} »
          </p>
        </div>
      )}

      {/* Lesson Content Body */}
      <div className="prose prose-blue max-w-none text-gray-800 leading-relaxed space-y-4 mb-12">
        {lesson.content ? (
          lesson.content.split("\n\n").map((paragraph, pIdx) => {
            if (paragraph.startsWith("# ")) {
              return (
                <h2 key={pIdx} className="text-xl font-bold text-gray-900 pt-4">
                  {paragraph.replace(/^#\s+/, "")}
                </h2>
              );
            }
            if (paragraph.startsWith("## ")) {
              return (
                <h3 key={pIdx} className="text-lg font-bold text-gray-800 pt-3">
                  {paragraph.replace(/^##\s+/, "")}
                </h3>
              );
            }
            if (paragraph.startsWith("- ") || paragraph.startsWith("* ")) {
              return (
                <ul key={pIdx} className="list-disc pl-5 space-y-1">
                  {paragraph.split("\n").map((item, iIdx) => (
                    <li key={iIdx} className="text-sm">
                      {item.replace(/^[-*]\s+/, "")}
                    </li>
                  ))}
                </ul>
              );
            }
            return (
              <p key={pIdx} className="text-sm lg:text-base leading-relaxed text-gray-700">
                {paragraph}
              </p>
            );
          })
        ) : (
          <div className="text-center py-12 text-sm text-gray-400 italic">
            Aucun contenu rédigé pour cette leçon. Cliquez sur « Modifier cette leçon » pour ajouter du texte.
          </div>
        )}
      </div>

      {/* Navigation Footer */}
      <div className="border-t border-gray-200 pt-6 flex items-center justify-between">
        <button
          type="button"
          onClick={onPrev}
          disabled={!hasPrev}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            hasPrev
              ? "text-gray-700 bg-gray-100 hover:bg-gray-200"
              : "text-gray-300 bg-gray-50 cursor-not-allowed"
          }`}
        >
          <ChevronLeft className="w-4 h-4" />
          Leçon précédente
        </button>

        <button
          type="button"
          onClick={onNext}
          disabled={!hasNext}
          className={`flex items-center gap-2 px-5 py-2 rounded-lg text-sm font-medium transition-colors ${
            hasNext
              ? "text-white bg-blue-600 hover:bg-blue-700 shadow-sm"
              : "text-gray-400 bg-gray-100 cursor-not-allowed"
          }`}
        >
          Leçon suivante
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </article>
  );
}
