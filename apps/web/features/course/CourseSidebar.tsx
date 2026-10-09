"use client";

import React, { useState, useMemo } from "react";
import Link from "next/link";
import {
  ChevronDown,
  ChevronRight,
  BookOpen,
  CheckCircle2,
  Circle,
  ArrowLeft,
  Edit3,
  Search,
  Maximize2,
  Minimize2,
} from "lucide-react";
import { CourseItem, CourseSectionItem } from "../../types/course";
import { CourseProgress } from "./CourseProgress";
import { useTranslation } from "../../lib/i18n/LanguageContext";

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
  const { t, isRTL } = useTranslation();
  const rootChapters = useMemo(() => course.sections || [], [course.sections]);

  // Sidebar search & collapse states
  const [searchQuery, setSearchQuery] = useState("");
  const [collapsedChapters, setCollapsedChapters] = useState<Record<string, boolean>>({});

  const toggleChapter = (chapterId: string) => {
    setCollapsedChapters((prev) => ({
      ...prev,
      [chapterId]: !prev[chapterId],
    }));
  };

  const handleExpandAll = () => {
    setCollapsedChapters({});
  };

  const handleCollapseAll = () => {
    const collapsed: Record<string, boolean> = {};
    for (const c of rootChapters) {
      collapsed[c.id] = true;
    }
    setCollapsedChapters(collapsed);
  };

  // Collect all leaf lessons for global progress
  const allLessons = useMemo(() => {
    const list: CourseSectionItem[] = [];
    const collect = (sections: CourseSectionItem[]) => {
      for (const sec of sections) {
        if (!sec.children || sec.children.length === 0) {
          list.push(sec);
        } else {
          collect(sec.children);
        }
      }
    };
    collect(rootChapters);
    return list;
  }, [rootChapters]);

  const completedCount = allLessons.filter((l) => completedSectionIds.has(l.id)).length;

  // Filter chapters based on search query
  const filteredChapters = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    if (!q) return rootChapters;

    return rootChapters.filter((chapter) => {
      const matchTitle = chapter.title.toLowerCase().includes(q);
      const matchChildren = chapter.children?.some(
        (sec) =>
          sec.title.toLowerCase().includes(q) ||
          sec.children?.some((l) => l.title.toLowerCase().includes(q))
      );
      return matchTitle || matchChildren;
    });
  }, [rootChapters, searchQuery]);

  return (
    <aside className="w-80 bg-slate-950 border-r border-slate-800 flex flex-col h-full shrink-0 text-slate-200">
      {/* Header */}
      <div className="p-4 border-b border-slate-850 flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <Link
            href={`/courses/${course.id}`}
            className="flex items-center gap-1.5 text-xs font-medium text-slate-400 hover:text-white transition-colors"
          >
            <ArrowLeft className={`w-3.5 h-3.5 ${isRTL ? "rotate-180" : ""}`} />
            <span>{t("courses.backToOverview", "Retour à l'aperçu")}</span>
          </Link>
          {isTeacher && (
            <Link
              href={`/courses/${course.id}/edit`}
              className="flex items-center gap-1 text-xs text-indigo-400 hover:text-indigo-300 font-semibold"
            >
              <Edit3 className="w-3 h-3" />
              <span>{t("courses.editCourse", "Modifier")}</span>
            </Link>
          )}
        </div>

        <div>
          <h2 className="text-sm font-bold text-white line-clamp-1">{course.title}</h2>
          <p className="text-[11px] text-slate-400 truncate">{course.organization_name || "Amanus Learn AI"}</p>
        </div>

        <CourseProgress
          totalLessons={allLessons.length}
          completedLessons={completedCount}
          totalMinutes={course.total_estimated_minutes || 0}
        />

        {/* Quick Search & Expand/Collapse Toolbar */}
        <div className="space-y-2 pt-1">
          <div className="relative">
            <Search className={`w-3.5 h-3.5 text-slate-500 absolute top-1/2 -translate-y-1/2 ${isRTL ? "right-2.5" : "left-2.5"}`} />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={t("courses.searchChapterOrLesson")}
              className={`w-full rounded-xl border border-slate-800 bg-slate-900/80 py-1.5 text-xs text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none ${
                isRTL ? "pr-8 pl-2.5" : "pl-8 pr-2.5"
              }`}
            />
          </div>

          <div className="flex items-center justify-between text-[11px] text-slate-400 px-1">
            <span>{rootChapters.length} {t("courses.chapters")}</span>
            <div className="flex items-center gap-1.5">
              <button
                type="button"
                onClick={handleExpandAll}
                className="hover:text-indigo-400 transition"
                title={t("courses.expandAll")}
              >
                <Maximize2 className="w-3 h-3" />
              </button>
              <button
                type="button"
                onClick={handleCollapseAll}
                className="hover:text-indigo-400 transition"
                title={t("courses.collapseAll")}
              >
                <Minimize2 className="w-3 h-3" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Chapters & Lessons Tree */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2 custom-scrollbar">
        {filteredChapters.length === 0 ? (
          <div className="text-center py-8 text-xs text-slate-500">
            {t("courses.noStructuredContent")}
          </div>
        ) : (
          filteredChapters.map((chapter, cIdx) => {
            const isCollapsed = !!collapsedChapters[chapter.id];
            const hasSubsections = chapter.children && chapter.children.length > 0;

            return (
              <div
                key={chapter.id}
                className="rounded-xl border border-slate-800/80 bg-slate-900/40 overflow-hidden transition hover:border-slate-700"
              >
                {/* Chapter header */}
                <button
                  type="button"
                  onClick={() => toggleChapter(chapter.id)}
                  className="w-full flex items-center justify-between p-2.5 text-left text-xs font-semibold text-slate-200 hover:bg-slate-850 transition"
                >
                  <div className="flex items-center gap-2 truncate pr-2">
                    {hasSubsections ? (
                      isCollapsed ? (
                        <ChevronRight className={`w-3.5 h-3.5 text-slate-400 shrink-0 ${isRTL ? "rotate-180" : ""}`} />
                      ) : (
                        <ChevronDown className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                      )
                    ) : (
                      <BookOpen className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                    )}
                    <span className="truncate">
                      {chapter.title || `${t("courses.chapter")} ${cIdx + 1}`}
                    </span>
                  </div>
                  {chapter.estimated_minutes > 0 && (
                    <span className="text-[10px] text-slate-500 shrink-0 font-mono">
                      {chapter.estimated_minutes}m
                    </span>
                  )}
                </button>

                {/* Subsections & Lessons */}
                {!isCollapsed && hasSubsections && (
                  <div className="pl-3 pr-2 py-1 space-y-1 bg-slate-950/70 border-t border-slate-800/80">
                    {chapter.children!.map((sec) => {
                      const hasLessons = sec.children && sec.children.length > 0;

                      return (
                        <div key={sec.id} className="space-y-1">
                          {/* Section Title */}
                          <div className="text-[11px] font-medium text-slate-400 pt-1 pb-0.5 px-2 truncate">
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
                                  className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs transition-all text-left ${
                                    isActive
                                      ? "bg-indigo-600 text-white font-semibold shadow-md shadow-indigo-950"
                                      : "text-slate-300 hover:bg-slate-800/60 hover:text-white"
                                  }`}
                                >
                                  <div className="flex items-center gap-2 truncate pr-1">
                                    {isCompleted ? (
                                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                                    ) : (
                                      <Circle
                                        className={`w-3.5 h-3.5 shrink-0 ${
                                          isActive ? "text-indigo-200" : "text-slate-600"
                                        }`}
                                      />
                                    )}
                                    <span className="truncate">{lesson.title}</span>
                                  </div>
                                  <span className="text-[10px] font-mono text-slate-400 shrink-0">
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
                              className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs transition-all text-left ${
                                sec.id === activeSectionId
                                  ? "bg-indigo-600 text-white font-semibold shadow-md shadow-indigo-950"
                                  : "text-slate-300 hover:bg-slate-800/60 hover:text-white"
                              }`}
                            >
                              <div className="flex items-center gap-2 truncate pr-1">
                                {completedSectionIds.has(sec.id) ? (
                                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                                ) : (
                                  <Circle className="w-3.5 h-3.5 text-slate-600 shrink-0" />
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
