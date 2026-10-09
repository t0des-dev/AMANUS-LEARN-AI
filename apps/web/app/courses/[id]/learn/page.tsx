"use client";

import React, { useState, useEffect, useCallback, useMemo } from "react";
import Link from "next/link";
import { useParams, useSearchParams, useRouter } from "next/navigation";
import { Menu, X, ArrowLeft, BookOpen, AlertCircle } from "lucide-react";
import { ProtectedRoute } from "../../../../components/auth/ProtectedRoute";
import { useAuth } from "../../../../components/auth/AuthProvider";
import { courseService } from "../../../../services/courseService";
import { CourseItem, CourseSectionItem } from "../../../../types/course";
import { CourseSidebar } from "../../../../features/course/CourseSidebar";
import { LessonViewer } from "../../../../features/course/LessonViewer";
import { useTranslation } from "../../../../lib/i18n/LanguageContext";

function flattenLessons(sections: CourseSectionItem[]): CourseSectionItem[] {
  const list: CourseSectionItem[] = [];
  for (const sec of sections) {
    if (!sec.children || sec.children.length === 0) {
      list.push(sec);
    } else {
      list.push(...flattenLessons(sec.children));
    }
  }
  return list;
}

function CourseLearnPageContent() {
  const { t } = useTranslation();
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();
  const courseId = params?.id as string;
  const urlLessonId = searchParams?.get("lesson");

  const { token, user } = useAuth();

  const [course, setCourse] = useState<CourseItem | null>(null);
  const [activeLesson, setActiveLesson] = useState<CourseSectionItem | null>(
    null
  );
  const [completedIds, setCompletedIds] = useState<Set<string>>(new Set());
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load completion states from localStorage
  useEffect(() => {
    if (!courseId) return;
    try {
      const saved = localStorage.getItem(`course_${courseId}_completed`);
      if (saved) {
        setCompletedIds(new Set(JSON.parse(saved)));
      }
    } catch {
      // Ignore storage errors
    }
  }, [courseId]);

  const toggleLessonComplete = (lessonId: string) => {
    setCompletedIds((prev) => {
      const updated = new Set(prev);
      if (updated.has(lessonId)) {
        updated.delete(lessonId);
      } else {
        updated.add(lessonId);
      }
      try {
        localStorage.setItem(
          `course_${courseId}_completed`,
          JSON.stringify(Array.from(updated))
        );
      } catch {
        // Ignore
      }
      return updated;
    });
  };

  const fetchCourse = useCallback(async () => {
    if (!token || !courseId) return;
    setIsLoading(true);
    setError(null);

    try {
      const data = await courseService.get(token, courseId);
      setCourse(data);

      const flat = flattenLessons(data.sections || []);
      if (urlLessonId) {
        const found = flat.find((l) => l.id === urlLessonId);
        if (found) {
          setActiveLesson(found);
          return;
        }
      }

      // Default to first lesson if not set
      if (flat.length > 0) {
        setActiveLesson(flat[0]);
      }
    } catch (err: any) {
      setError(err.message || "Impossible de charger le cours.");
    } finally {
      setIsLoading(false);
    }
  }, [token, courseId, urlLessonId]);

  useEffect(() => {
    fetchCourse();
  }, [fetchCourse]);

  const allLessons = useMemo(() => {
    return flattenLessons(course?.sections || []);
  }, [course]);

  const currentIdx = activeLesson
    ? allLessons.findIndex((l) => l.id === activeLesson.id)
    : -1;

  const handleNextLesson = () => {
    if (currentIdx >= 0 && currentIdx < allLessons.length - 1) {
      const next = allLessons[currentIdx + 1];
      setActiveLesson(next);
      router.push(`/courses/${courseId}/learn?lesson=${next.id}`);
    }
  };

  const handlePrevLesson = () => {
    if (currentIdx > 0) {
      const prev = allLessons[currentIdx - 1];
      setActiveLesson(prev);
      router.push(`/courses/${courseId}/learn?lesson=${prev.id}`);
    }
  };

  const handleSelectLesson = (lesson: CourseSectionItem) => {
    setActiveLesson(lesson);
    setIsSidebarOpen(false);
    router.push(`/courses/${courseId}/learn?lesson=${lesson.id}`);
  };

  if (isLoading) {
    return (
      <div className="flex h-screen bg-slate-950">
        <div className="w-80 h-full bg-slate-900/60 border-r border-slate-800 animate-pulse hidden md:block" />
        <div className="flex-1 p-10 space-y-6">
          <div className="h-10 bg-slate-900 border border-slate-800 rounded-2xl animate-pulse w-2/3" />
          <div className="h-40 bg-slate-900 border border-slate-800 rounded-2xl animate-pulse" />
          <div className="h-64 bg-slate-900 border border-slate-800 rounded-2xl animate-pulse" />
        </div>
      </div>
    );
  }

  if (error || !course) {
    return (
      <div className="max-w-md mx-auto py-16 text-center space-y-4">
        <div className="p-4 bg-rose-950/20 text-rose-300 text-xs rounded-2xl border border-rose-500/30">
          {error || t("courses.noCourses")}
        </div>
        <Link
          href="/courses"
          className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 transition"
        >
          {t("courses.backToCourses")}
        </Link>
      </div>
    );
  }

  return (
    <div className="flex h-[calc(100vh-4rem)] overflow-hidden bg-slate-950 text-slate-200">
      {/* Mobile Sidebar Backdrop */}
      {isSidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm md:hidden"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      {/* Course Sidebar */}
      <div
        className={`fixed inset-y-0 left-0 z-50 transform md:relative md:translate-x-0 transition-transform duration-300 ease-in-out ${
          isSidebarOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
        }`}
      >
        <CourseSidebar
          course={course}
          activeSectionId={activeLesson?.id}
          onSelectSection={handleSelectLesson}
          completedSectionIds={completedIds}
          isTeacher={true}
        />
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col h-full overflow-hidden bg-slate-950">
        {/* Mobile top toggle */}
        <div className="md:hidden border-b border-slate-800 p-3 bg-slate-900/60 flex items-center justify-between">
          <button
            type="button"
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="p-1.5 rounded-xl border border-slate-800 text-slate-300 hover:text-white hover:bg-slate-800 flex items-center gap-1.5 text-xs font-medium transition"
          >
            {isSidebarOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
            <span>{t("courses.outline")}</span>
          </button>
          <span className="text-xs font-semibold text-white truncate px-2">
            {activeLesson?.title || course.title}
          </span>
        </div>

        {/* Scrollable Lesson Viewer */}
        <main className="flex-1 overflow-y-auto custom-scrollbar">
          {activeLesson ? (
            <LessonViewer
              courseId={course.id}
              lesson={activeLesson}
              isCompleted={completedIds.has(activeLesson.id)}
              onToggleComplete={() => toggleLessonComplete(activeLesson.id)}
              onNext={handleNextLesson}
              onPrev={handlePrevLesson}
              hasNext={currentIdx < allLessons.length - 1}
              hasPrev={currentIdx > 0}
              isTeacher={true}
            />
          ) : (
            <div className="max-w-md mx-auto py-24 text-center text-slate-500 text-xs">
              {t("courses.noStructuredContent")}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

export default function CourseLearnPage() {
  return (
    <ProtectedRoute>
      <CourseLearnPageContent />
    </ProtectedRoute>
  );
}
