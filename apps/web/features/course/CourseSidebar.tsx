"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  ChevronDown,
  ChevronRight,
  BookOpen,
  CheckCircle2,
  Circle,
  ArrowLeft,
  Edit3,
} from "lucide-react";
import { CourseItem, CourseSectionItem } from "../../types/course";
import { CourseProgress } from "./CourseProgress";

interface CourseSidebarProps {
  course: CourseItem;
  activeSectionId?: string;
  onSelectSection: (section: CourseSectionItem) => void;
  completedSectionIds?: Set<string>;
  isTeacher?: boolean;
}

export function CourseSidebar({
  course,
  activeSectionId,
  onSelectSection,
  completedSectionIds = new Set(),
  isTeacher = false,
}: CourseSidebarProps) {
  // Collapsed state for chapters
  const [collapsedChapters, setCollapsedChapters] = useState<Record<string, boolean>>({});

  const toggleChapter = (chapterId: string) => {
    setCollapsedChapters((prev) => ({
      ...prev,
      [chapterId]: !prev[chapterId],
    }));
  };

  const rootChapters = course.sections || [];

  // Count lessons for progress
  const allLessons: CourseSectionItem[] = [];
  const collectLessons = (sections: CourseSectionItem[]) => {
    for (const sec of sections) {
      if (!sec.children || sec.children.length === 0) {
        allLessons.push(sec);
      } else {
        collectLessons(sec.children);
      }
    }
  };
  collectLessons(rootChapters);

  const completedCount = allLessons.filter((l) => completedSectionIds.has(l.id)).length;

  return (
    <aside className="w-80 bg-white border-r border-gray-200 flex flex-col h-full shrink-0">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <Link
            href={`/courses/${course.id}`}
            className="flex items-center gap-1.5 text-xs font-medium text-gray-500 hover:text-gray-900 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Retour à l'aperçu
          </Link>
          {isTeacher && (
            <Link
              href={`/courses/${course.id}/edit`}
              className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-700 font-medium"
            >
              <Edit3 className="w-3 h-3" />
              Éditer
            </Link>
          )}
        </div>

        <div>
          <h2 className="text-sm font-bold text-gray-900 line-clamp-1">{course.title}</h2>
          <p className="text-xs text-gray-500">{course.organization_name || "Amanus Learn AI"}</p>
        </div>

        <CourseProgress
          totalLessons={allLessons.length}
          completedLessons={completedCount}
          totalMinutes={course.total_estimated_minutes || 0}
        />
      </div>

      {/* Chapters & Lessons Tree */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {rootChapters.length === 0 ? (
          <div className="text-center py-8 text-xs text-gray-400">
            Aucun contenu structuré dans ce cours.
          </div>
        ) : (
          rootChapters.map((chapter, cIdx) => {
            const isCollapsed = !!collapsedChapters[chapter.id];
            const hasSubsections = chapter.children && chapter.children.length > 0;

            return (
              <div key={chapter.id} className="rounded-lg border border-gray-100 bg-gray-50/50 overflow-hidden">
                {/* Chapter header */}
                <button
                  type="button"
                  onClick={() => toggleChapter(chapter.id)}
                  className="w-full flex items-center justify-between p-2.5 text-left text-xs font-semibold text-gray-800 hover:bg-gray-100/70 transition-colors"
                >
                  <div className="flex items-center gap-2 truncate pr-2">
                    {hasSubsections ? (
                      isCollapsed ? (
                        <ChevronRight className="w-3.5 h-3.5 text-gray-400 shrink-0" />
                      ) : (
                        <ChevronDown className="w-3.5 h-3.5 text-gray-400 shrink-0" />
                      )
                    ) : (
                      <BookOpen className="w-3.5 h-3.5 text-blue-500 shrink-0" />
                    )}
                    <span className="truncate">
                      {chapter.title || `Chapitre ${cIdx + 1}`}
                    </span>
                  </div>
                  {chapter.estimated_minutes > 0 && (
                    <span className="text-[10px] text-gray-400 shrink-0 font-normal">
                      {chapter.estimated_minutes} min
                    </span>
                  )}
                </button>

                {/* Subsections & Lessons */}
                {!isCollapsed && hasSubsections && (
                  <div className="pl-3 pr-2 py-1 space-y-1 bg-white border-t border-gray-100">
                    {chapter.children!.map((sec) => {
                      const hasLessons = sec.children && sec.children.length > 0;

                      return (
                        <div key={sec.id} className="space-y-1">
                          {/* Section Title */}
                          <div className="text-[11px] font-medium text-gray-500 pt-1 pb-0.5 px-2">
                            {sec.title}
                          </div>

                          {/* Lessons inside Section */}
                          {hasLessons ? (
                            sec.children!.map((lesson) => {
                              const isActive = lesson.id === activeSectionId;
                              const isCompleted = completedSectionIds.has(lesson.id);

                              return (
                                <button
                                  key={lesson.id}
                                  type="button"
                                  onClick={() => onSelectSection(lesson)}
                                  className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-md text-xs transition-colors text-left ${
                                    isActive
                                      ? "bg-blue-50 text-blue-700 font-semibold"
                                      : "text-gray-700 hover:bg-gray-50"
                                  }`}
                                >
                                  <div className="flex items-center gap-2 truncate pr-1">
                                    {isCompleted ? (
                                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
                                    ) : (
                                      <Circle
                                        className={`w-3.5 h-3.5 shrink-0 ${
                                          isActive ? "text-blue-500" : "text-gray-300"
                                        }`}
                                      />
                                    )}
                                    <span className="truncate">{lesson.title}</span>
                                  </div>
                                  <span className="text-[10px] text-gray-400 shrink-0">
                                    {lesson.estimated_minutes}m
                                  </span>
                                </button>
                              );
                            })
                          ) : (
                            /* Direct lesson under chapter */
                            <button
                              type="button"
                              onClick={() => onSelectSection(sec)}
                              className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-md text-xs transition-colors text-left ${
                                sec.id === activeSectionId
                                  ? "bg-blue-50 text-blue-700 font-semibold"
                                  : "text-gray-700 hover:bg-gray-50"
                              }`}
                            >
                              <div className="flex items-center gap-2 truncate pr-1">
                                {completedSectionIds.has(sec.id) ? (
                                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
                                ) : (
                                  <Circle className="w-3.5 h-3.5 text-gray-300 shrink-0" />
                                )}
                                <span className="truncate">{sec.title}</span>
                              </div>
                            </button>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </aside>
  );
}
