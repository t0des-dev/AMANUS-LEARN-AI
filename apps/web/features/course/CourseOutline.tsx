"use client";

import React, { useState, useMemo } from "react";
import Link from "next/link";
import {
  BookOpen,
  Clock,
  Target,
  Edit,
  PlayCircle,
  FileText,
  ChevronRight,
  ChevronDown,
  Layers,
  Search,
  CheckCircle2,
  ListFilter,
  Maximize2,
  Minimize2,
} from "lucide-react";
import { CourseItem, CourseSectionItem } from "../../types/course";
import { useTranslation } from "../../lib/i18n/LanguageContext";

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
  const { t, isRTL } = useTranslation();
  const rootChapters = useMemo(() => course.sections || [], [course.sections]);

  // Search & filter state
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

  // Filter chapters based on search query
  const filteredChapters = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    if (!q) return rootChapters;

    return rootChapters.filter((chapter) => {
      const matchTitle = chapter.title.toLowerCase().includes(q);
      const matchSummary = chapter.summary?.toLowerCase().includes(q);
      const matchChildren = chapter.children?.some(
        (sec) =>
          sec.title.toLowerCase().includes(q) ||
          sec.summary?.toLowerCase().includes(q) ||
          sec.children?.some(
            (l) =>
              l.title.toLowerCase().includes(q) ||
              l.objectives?.some((o) => o.toLowerCase().includes(q))
          )
      );
      return matchTitle || matchSummary || matchChildren;
    });
  }, [rootChapters, searchQuery]);

  // Compute total lessons count
  const totalLessonsCount = useMemo(() => {
    let count = 0;
    const countLeafs = (secs: CourseSectionItem[]) => {
      for (const s of secs) {
        if (!s.children || s.children.length === 0) {
          count++;
        } else {
          countLeafs(s.children);
        }
      }
    };
    countLeafs(rootChapters);
    return count;
  }, [rootChapters]);

  if (rootChapters.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-slate-800 bg-slate-900/40 p-12 text-center backdrop-blur-sm">
        <div className="w-14 h-14 bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 rounded-2xl flex items-center justify-center mx-auto mb-4">
          <Layers className="w-7 h-7" />
        </div>
        <h3 className="text-base font-bold text-white mb-1">
          {t("courses.noStructuredContent")}
        </h3>
        <p className="text-xs sm:text-sm text-slate-400 max-w-md mx-auto mb-6 leading-relaxed">
          {t("courses.noCoursesDesc")}
        </p>
        {isTeacher && (
          <Link
            href={`/courses/${course.id}/edit`}
            className="inline-flex items-center gap-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold shadow-md shadow-indigo-950 transition"
          >
            <Edit className="w-3.5 h-3.5" />
            <span>{t("courses.openEditor")}</span>
          </Link>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Search & Bulk Expand/Collapse Toolbar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 p-3.5 rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm">
        <div className="relative flex-1">
          <Search className={`w-4 h-4 text-slate-400 absolute top-1/2 -translate-y-1/2 ${isRTL ? "right-3" : "left-3"}`} />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder={t("courses.searchChapterOrLesson")}
            className={`w-full rounded-xl border border-slate-800 bg-slate-950/70 py-2 text-xs text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 transition ${
              isRTL ? "pr-9 pl-3" : "pl-9 pr-3"
            }`}
          />
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <span className="text-[11px] font-mono text-slate-400 px-2 py-1 rounded-lg bg-slate-950/80 border border-slate-800 hidden md:inline-block">
            {rootChapters.length} {t("courses.chapters")} • {totalLessonsCount} {t("courses.lessons")}
          </span>

          <button
            type="button"
            onClick={handleExpandAll}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-slate-800 bg-slate-950/60 text-slate-300 hover:text-white hover:bg-slate-800 text-xs font-medium transition"
            title={t("courses.expandAll")}
          >
            <Maximize2 className="w-3 h-3 text-indigo-400" />
            <span className="hidden sm:inline">{t("courses.expandAll")}</span>
          </button>

          <button
            type="button"
            onClick={handleCollapseAll}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-slate-800 bg-slate-950/60 text-slate-300 hover:text-white hover:bg-slate-800 text-xs font-medium transition"
            title={t("courses.collapseAll")}
          >
            <Minimize2 className="w-3 h-3 text-slate-400" />
            <span className="hidden sm:inline">{t("courses.collapseAll")}</span>
          </button>
        </div>
      </div>

      {/* Chapters Accordion List */}
      <div className="space-y-4">
        {filteredChapters.map((chapter, cIdx) => {
          const isCollapsed = !!collapsedChapters[chapter.id];
          const hasSubsections = chapter.children && chapter.children.length > 0;

          // Count lessons in this chapter
          let chapterLessonCount = 0;
          if (hasSubsections) {
            for (const s of chapter.children!) {
              chapterLessonCount += s.children && s.children.length > 0 ? s.children.length : 1;
            }
          }

          return (
            <div
              key={chapter.id}
              className="rounded-2xl border border-slate-800 bg-slate-900/60 overflow-hidden shadow-lg backdrop-blur-sm transition hover:border-slate-700"
            >
              {/* Chapter Header / Toggle */}
              <div
                onClick={() => toggleChapter(chapter.id)}
                className="p-5 border-b border-slate-800/80 bg-slate-950/60 cursor-pointer flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition hover:bg-slate-950/90"
              >
                <div className="flex items-start gap-3 min-w-0">
                  <button
                    type="button"
                    className="p-1 rounded-lg bg-slate-800/60 text-slate-400 hover:text-white shrink-0 mt-0.5 transition"
                  >
                    {isCollapsed ? (
                      <ChevronRight className={`w-4 h-4 transition ${isRTL ? "rotate-180" : ""}`} />
                    ) : (
                      <ChevronDown className="w-4 h-4 transition" />
                    )}
                  </button>

                  <div className="min-w-0">
                    <div className="flex items-center gap-2 mb-1.5">
                      <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 font-mono">
                        {t("courses.chapter")} #{cIdx + 1}
                      </span>
                      {chapterLessonCount > 0 && (
                        <span className="text-[11px] text-slate-400 font-mono">
                          {chapterLessonCount} {t("courses.lessons")}
                        </span>
                      )}
                    </div>
                    <h3 className="text-base font-bold text-white tracking-tight truncate">
                      {chapter.title}
                    </h3>
                    {chapter.summary && (
                      <p className="text-xs text-slate-400 mt-1 line-clamp-2 leading-relaxed">
                        {chapter.summary}
                      </p>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <div className="flex items-center gap-1.5 text-xs text-slate-300 bg-slate-900 border border-slate-800 px-3 py-1 rounded-xl font-mono">
                    <Clock className="w-3.5 h-3.5 text-indigo-400" />
                    <span>~{chapter.estimated_minutes} {t("dashboard.minutes")}</span>
                  </div>
                </div>
              </div>

              {/* Sections & Lessons inside Chapter */}
              {!isCollapsed && (
                <div className="p-4 space-y-3.5 bg-slate-950/20">
                  {hasSubsections ? (
                    chapter.children!.map((section, sIdx) => (
                      <div
                        key={section.id}
                        className="rounded-xl border border-slate-800/80 bg-slate-900/40 p-4 space-y-3"
                      >
                        <div className="flex items-center justify-between gap-2">
                          <h4 className="text-xs font-semibold text-slate-200 flex items-center gap-2">
                            <span className="text-indigo-400 font-mono text-[11px]">
                              {cIdx + 1}.{sIdx + 1}
                            </span>
                            <span>{section.title}</span>
                          </h4>
                          {section.estimated_minutes > 0 && (
                            <span className="text-[11px] text-slate-500 font-mono">
                              {section.estimated_minutes} {t("dashboard.minutes")}
                            </span>
                          )}
                        </div>

                        {section.summary && (
                          <p className="text-xs text-slate-400 pl-4 border-l border-slate-800">
                            {section.summary}
                          </p>
                        )}

                        {/* Lessons list */}
                        {section.children && section.children.length > 0 && (
                          <div className="space-y-2 pt-1">
                            {section.children.map((lesson, lIdx) => (
                              <div
                                key={lesson.id}
                                className="rounded-xl border border-slate-800/60 bg-slate-950/50 p-3 hover:border-indigo-500/40 hover:bg-slate-900/60 transition-all flex items-center justify-between gap-3 group"
                              >
                                <div className="flex items-start gap-3 min-w-0">
                                  <div className="w-7 h-7 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 flex items-center justify-center shrink-0 mt-0.5 group-hover:bg-indigo-500 group-hover:text-white transition">
                                    <FileText className="w-3.5 h-3.5" />
                                  </div>
                                  <div className="min-w-0">
                                    <div className="flex items-center gap-2">
                                      <span className="text-[11px] text-slate-500 font-mono">
                                        {cIdx + 1}.{sIdx + 1}.{lIdx + 1}
                                      </span>
                                      <h5 className="text-xs font-semibold text-white group-hover:text-indigo-300 transition truncate">
                                        {lesson.title}
                                      </h5>
                                    </div>
                                    {lesson.objectives && lesson.objectives.length > 0 && (
                                      <div className="flex items-center gap-1.5 text-[11px] text-slate-400 mt-1">
                                        <Target className="w-3 h-3 text-emerald-400 shrink-0" />
                                        <span className="truncate">
                                          {lesson.objectives[0]}
                                        </span>
                                      </div>
                                    )}
                                  </div>
                                </div>

                                <div className="flex items-center gap-2 shrink-0">
                                  <span className="text-[11px] font-mono text-slate-500">
                                    {lesson.estimated_minutes}m
                                  </span>

                                  {onSelectLesson ? (
                                    <button
                                      type="button"
                                      onClick={() => onSelectLesson(lesson)}
                                      className="p-1.5 text-indigo-400 hover:text-white hover:bg-indigo-600 rounded-lg text-xs font-medium flex items-center gap-1 transition"
                                    >
                                      <PlayCircle className="w-4 h-4" />
                                      <span className="hidden sm:inline">{t("courses.read")}</span>
                                    </button>
                                  ) : (
                                    <Link
                                      href={`/courses/${course.id}/learn?lesson=${lesson.id}`}
                                      className="p-1.5 text-indigo-400 hover:text-white hover:bg-indigo-600 rounded-lg text-xs font-medium flex items-center gap-1 transition"
                                    >
                                      <PlayCircle className="w-4 h-4" />
                                      <span className="hidden sm:inline">{t("courses.read")}</span>
                                    </Link>
                                  )}

                                  {isTeacher && (
                                    <Link
                                      href={`/courses/${course.id}/edit?section=${lesson.id}`}
                                      className="p-1.5 text-slate-500 hover:text-slate-300 hover:bg-slate-800 rounded-lg transition"
                                      title={t("courses.editCourse")}
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
                    <div className="text-xs text-slate-500 italic py-2 pl-2">
                      {t("courses.noSubsections")}
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
