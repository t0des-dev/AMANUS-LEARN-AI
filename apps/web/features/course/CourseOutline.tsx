"use client";

import React from "react";
import Link from "next/link";
import {
  BookOpen,
  Clock,
  Target,
  Edit,
  PlayCircle,
  FileText,
  ChevronRight,
  Layers,
} from "lucide-react";
import { CourseItem, CourseSectionItem } from "../../types/course";

interface CourseOutlineProps {
  course: CourseItem;
  isTeacher?: boolean;
  onSelectLesson?: (lesson: CourseSectionItem) => void;
}

export function CourseOutline({
  course,
  isTeacher = false,
  onSelectLesson,
}: CourseOutlineProps) {
  const rootChapters = course.sections || [];

  if (rootChapters.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-dashed border-gray-300 p-12 text-center">
        <div className="w-12 h-12 bg-blue-50 text-blue-600 rounded-full flex items-center justify-center mx-auto mb-3">
          <Layers className="w-6 h-6" />
        </div>
        <h3 className="text-base font-semibold text-gray-900 mb-1">
          Aucun contenu structuré pour le moment
        </h3>
        <p className="text-sm text-gray-500 max-w-md mx-auto mb-5">
          Ce cours ne contient pas encore de chapitres ni de leçons. Vous pouvez générer automatiquement la structure à partir d&apos;un document ou créer vos sections manuellement.
        </p>
        {isTeacher && (
          <Link
            href={`/courses/${course.id}/edit`}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors"
          >
            <Edit className="w-4 h-4" />
            Ouvrir l'éditeur de cours
          </Link>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {rootChapters.map((chapter, cIdx) => (
        <div
          key={chapter.id}
          className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm"
        >
          {/* Chapter Banner */}
          <div className="bg-gradient-to-r from-gray-50 to-white p-5 border-b border-gray-200">
            <div className="flex items-start justify-between gap-4">
              <div>
                <span className="inline-block px-2.5 py-0.5 rounded text-xs font-semibold bg-blue-100 text-blue-800 mb-2">
                  Chapitre {cIdx + 1}
                </span>
                <h3 className="text-lg font-bold text-gray-900">{chapter.title}</h3>
                {chapter.summary && (
                  <p className="text-sm text-gray-600 mt-1 line-clamp-2">{chapter.summary}</p>
                )}
              </div>
              <div className="flex items-center gap-1.5 text-xs text-gray-500 bg-white border border-gray-200 px-2.5 py-1 rounded-full shrink-0">
                <Clock className="w-3.5 h-3.5 text-purple-500" />
                <span>~{chapter.estimated_minutes} min</span>
              </div>
            </div>
          </div>

          {/* Sections & Lessons inside Chapter */}
          <div className="p-4 space-y-4">
            {chapter.children && chapter.children.length > 0 ? (
              chapter.children.map((section, sIdx) => (
                <div
                  key={section.id}
                  className="rounded-lg border border-gray-100 bg-gray-50/50 p-4 space-y-3"
                >
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm font-semibold text-gray-800 flex items-center gap-2">
                      <span className="text-gray-400 font-mono text-xs">
                        {cIdx + 1}.{sIdx + 1}
                      </span>
                      {section.title}
                    </h4>
                    {section.estimated_minutes > 0 && (
                      <span className="text-xs text-gray-400">
                        {section.estimated_minutes} min
                      </span>
                    )}
                  </div>

                  {section.summary && (
                    <p className="text-xs text-gray-500 pl-5">{section.summary}</p>
                  )}

                  {/* Lessons list */}
                  {section.children && section.children.length > 0 && (
                    <div className="space-y-2 pt-1 pl-2">
                      {section.children.map((lesson, lIdx) => (
                        <div
                          key={lesson.id}
                          className="bg-white rounded-lg border border-gray-200 p-3 hover:border-blue-300 transition-colors flex items-center justify-between gap-3"
                        >
                          <div className="flex items-start gap-3 min-w-0">
                            <div className="w-7 h-7 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center shrink-0 mt-0.5">
                              <FileText className="w-4 h-4" />
                            </div>
                            <div className="min-w-0">
                              <div className="flex items-center gap-2">
                                <span className="text-xs text-gray-400 font-mono">
                                  {cIdx + 1}.{sIdx + 1}.{lIdx + 1}
                                </span>
                                <h5 className="text-sm font-medium text-gray-900 truncate">
                                  {lesson.title}
                                </h5>
                              </div>
                              {lesson.objectives && lesson.objectives.length > 0 && (
                                <div className="flex items-center gap-1.5 text-xs text-gray-500 mt-1">
                                  <Target className="w-3 h-3 text-emerald-500 shrink-0" />
                                  <span className="truncate">
                                    {lesson.objectives[0]}
                                  </span>
                                </div>
                              )}
                            </div>
                          </div>

                          <div className="flex items-center gap-2 shrink-0">
                            <span className="text-xs text-gray-400 font-normal">
                              {lesson.estimated_minutes} min
                            </span>
                            {onSelectLesson ? (
                              <button
                                type="button"
                                onClick={() => onSelectLesson(lesson)}
                                className="p-1.5 text-blue-600 hover:bg-blue-50 rounded-lg text-xs font-medium flex items-center gap-1 transition-colors"
                              >
                                <PlayCircle className="w-4 h-4" />
                                <span className="hidden sm:inline">Lire</span>
                              </button>
                            ) : (
                              <Link
                                href={`/courses/${course.id}/learn?lesson=${lesson.id}`}
                                className="p-1.5 text-blue-600 hover:bg-blue-50 rounded-lg text-xs font-medium flex items-center gap-1 transition-colors"
                              >
                                <PlayCircle className="w-4 h-4" />
                                <span className="hidden sm:inline">Lire</span>
                              </Link>
                            )}
                            {isTeacher && (
                              <Link
                                href={`/courses/${course.id}/edit?section=${lesson.id}`}
                                className="p-1.5 text-gray-400 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                                title="Modifier cette leçon"
                              >
                                <Edit className="w-3.5 h-3.5" />
                              </Link>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))
            ) : (
              <div className="text-xs text-gray-400 italic py-2 pl-2">
                Aucune sous-section dans ce chapitre.
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
