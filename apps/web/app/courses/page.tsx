"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  GraduationCap,
  PlusCircle,
  Clock,
  Layers,
  Sparkles,
  BookOpen,
  ArrowRight,
  Trash2,
  Edit,
  AlertCircle,
  FileText,
  X,
} from "lucide-react";
import { ProtectedRoute } from "../../components/auth/ProtectedRoute";
import { useAuth } from "../../components/auth/AuthProvider";
import { useOrganization } from "../../components/organization/OrganizationContext";
import { useTranslation } from "../../lib/i18n/LanguageContext";
import { courseService } from "../../services/courseService";
import { documentService } from "../../services/documentService";
import { CourseItem, CourseLevel } from "../../types/course";
import { DocumentItem } from "../../types/document";

function CoursesPageContent() {
  const { token } = useAuth();
  const { currentOrg } = useOrganization();
  const { t, isRTL } = useTranslation();

  const [courses, setCourses] = useState<CourseItem[]>([]);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal states
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [newLevel, setNewLevel] = useState<CourseLevel>("BEGINNER");
  const [selectedDocId, setSelectedDocId] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchCourses = useCallback(async () => {
    if (!token) return;
    setIsLoading(true);
    setError(null);

    try {
      const data = await courseService.list(token, {
        organization_id: currentOrg?.id || undefined,
      });
      setCourses(data);
    } catch (err: any) {
      setError(err.message || t("common.error"));
    } finally {
      setIsLoading(false);
    }
  }, [token, currentOrg, t]);

  const fetchDocuments = useCallback(async () => {
    if (!token) return;
    try {
      const docs = await documentService.list(token, {
        organization_id: currentOrg?.id || undefined,
      });
      setDocuments(docs);
    } catch {
      // Ignore background errors
    }
  }, [token, currentOrg]);

  useEffect(() => {
    fetchCourses();
    fetchDocuments();
  }, [fetchCourses, fetchDocuments]);

  const handleCreateCourse = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !currentOrg) return;

    setIsSubmitting(true);
    setError(null);

    try {
      const newCourse = await courseService.create(token, {
        organization: currentOrg.id,
        title: newTitle,
        description: newDesc,
        level: newLevel,
        document: selectedDocId || null,
      });

      // If document was selected, generate structure immediately
      if (selectedDocId) {
        try {
          await courseService.generate(token, newCourse.id, {
            document_id: selectedDocId,
          });
        } catch {
          // Continue to list, user can regenerate in editor
        }
      }

      setShowCreateModal(false);
      setNewTitle("");
      setNewDesc("");
      setSelectedDocId("");
      await fetchCourses();
    } catch (err: any) {
      setError(err.message || t("common.error"));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteCourse = async (courseId: string) => {
    if (!token) return;
    if (!confirm(t("courses.confirmDelete"))) return;

    try {
      await courseService.delete(token, courseId);
      setCourses((prev) => prev.filter((c) => c.id !== courseId));
    } catch (err: any) {
      alert(err.message || t("common.error"));
    }
  };

  const getLevelLabel = (level: string) => {
    switch (level) {
      case "BEGINNER":
        return t("courses.levelBeginner");
      case "INTERMEDIATE":
        return t("courses.levelIntermediate");
      case "ADVANCED":
        return t("courses.levelAdvanced");
      default:
        return level;
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Top Banner */}
      <div className="rounded-3xl border border-indigo-500/20 bg-gradient-to-r from-indigo-950/80 via-slate-900 to-slate-900 p-6 sm:p-8 text-white shadow-xl backdrop-blur-md flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-2 mb-2 text-indigo-400 text-xs font-semibold uppercase tracking-wider">
            <GraduationCap className="w-4 h-4" />
            <span>{t("home.cap3Title")}</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
            {t("courses.title")}
          </h1>
          <p className="mt-2 text-xs sm:text-sm text-slate-300 max-w-2xl leading-relaxed">
            {t("courses.subtitle")}
          </p>
        </div>

        <button
          type="button"
          onClick={() => setShowCreateModal(true)}
          className="inline-flex items-center gap-2 px-5 py-3 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-xl text-xs sm:text-sm shadow-lg shadow-indigo-950 transition active:scale-95 shrink-0"
        >
          <PlusCircle className="w-4 h-4" />
          <span>{t("courses.createBtn")}</span>
        </button>
      </div>

      {error && (
        <div className="p-4 bg-rose-950/20 border border-rose-500/30 rounded-xl text-xs text-rose-300 flex items-center gap-3">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
          <span>{error}</span>
        </div>
      )}

      {/* Courses List Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map((n) => (
            <div
              key={n}
              className="h-64 bg-slate-900/40 border border-slate-800 rounded-2xl animate-pulse"
            />
          ))}
        </div>
      ) : courses.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-800 bg-slate-900/40 p-12 text-center backdrop-blur-sm">
          <div className="w-14 h-14 bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <BookOpen className="w-7 h-7" />
          </div>
          <h3 className="text-base font-bold text-white mb-1">
            {t("courses.noCourses")}
          </h3>
          <p className="text-xs sm:text-sm text-slate-400 max-w-md mx-auto mb-6 leading-relaxed">
            {t("courses.noCoursesDesc")}
          </p>
          <button
            type="button"
            onClick={() => setShowCreateModal(true)}
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-xl text-xs transition shadow-md shadow-indigo-950"
          >
            <PlusCircle className="w-4 h-4" />
            <span>{t("courses.createBtn")}</span>
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {courses.map((course) => (
            <div
              key={course.id}
              className="rounded-2xl border border-slate-800 bg-slate-900/60 hover:border-indigo-500/50 hover:bg-slate-900/90 shadow-xl backdrop-blur-sm transition-all flex flex-col justify-between overflow-hidden group"
            >
              <div className="p-6 flex-1 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <span
                      className={`px-2.5 py-0.5 rounded-full text-[11px] font-semibold ${
                        course.status === "PUBLISHED"
                          ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                          : "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                      }`}
                    >
                      {course.status === "PUBLISHED" ? t("courses.statusPublished") : t("courses.statusDraft")}
                    </span>

                    <span className="text-[11px] font-medium text-slate-400 font-mono">
                      {getLevelLabel(course.level)}
                    </span>
                  </div>

                  <h3 className="text-base font-bold text-white mb-2 line-clamp-1 group-hover:text-indigo-300 transition">
                    {course.title}
                  </h3>

                  <p className="text-xs text-slate-400 line-clamp-3 mb-4 leading-relaxed">
                    {course.description || t("courses.noDesc")}
                  </p>
                </div>

                <div className="pt-4 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400 font-mono">
                  <div className="flex items-center gap-1.5">
                    <Layers className="w-3.5 h-3.5 text-indigo-400" />
                    <span>{course.sections_count} {t("courses.chaptersCount")}</span>
                  </div>

                  <div className="flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5 text-purple-400" />
                    <span>~{course.total_estimated_minutes}m</span>
                  </div>
                </div>
              </div>

              {/* Bottom Actions */}
              <div className="bg-slate-950/70 px-6 py-3 border-t border-slate-800 flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <Link
                    href={`/courses/${course.id}/edit`}
                    className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition"
                    title={t("courses.editCourseTitle")}
                  >
                    <Edit className="w-4 h-4" />
                  </Link>

                  <button
                    type="button"
                    onClick={() => handleDeleteCourse(course.id)}
                    className="p-1.5 text-slate-500 hover:text-rose-400 hover:bg-rose-950/30 rounded-lg transition"
                    title={t("courses.deleteCourse")}
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>

                <Link
                  href={`/courses/${course.id}`}
                  className="inline-flex items-center gap-1.5 text-xs font-bold text-indigo-400 hover:text-indigo-300 transition"
                >
                  <span>{t("courses.viewCourse")}</span>
                  <ArrowRight className={`w-3.5 h-3.5 ${isRTL ? "rotate-180" : ""}`} />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Course Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md">
          <div className="bg-slate-950 border border-slate-800 rounded-3xl max-w-lg w-full p-6 sm:p-8 space-y-6 shadow-2xl text-white">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <GraduationCap className="w-5 h-5 text-indigo-400" />
                <span>{t("courses.createModalTitle")}</span>
              </h3>
              <button
                type="button"
                onClick={() => setShowCreateModal(false)}
                className="text-slate-400 hover:text-white transition p-1"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateCourse} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                  {t("courses.courseTitle")} *
                </label>
                <input
                  type="text"
                  required
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder={t("courses.courseTitlePlaceholder")}
                  className="w-full px-3.5 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                  {t("courses.courseDesc")}
                </label>
                <textarea
                  rows={3}
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  placeholder={t("courses.courseDescPlaceholder")}
                  className="w-full px-3.5 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                    {t("courses.level")}
                  </label>
                  <select
                    value={newLevel}
                    onChange={(e) => setNewLevel(e.target.value as CourseLevel)}
                    className="w-full px-3.5 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white focus:border-indigo-500 focus:outline-none"
                  >
                    <option value="BEGINNER">{t("courses.levelBeginner")}</option>
                    <option value="INTERMEDIATE">{t("courses.levelIntermediate")}</option>
                    <option value="ADVANCED">{t("courses.levelAdvanced")}</option>
                    <option value="EXPERT">Expert</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5 flex items-center gap-1">
                    <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                    <span>{t("courses.sourceDoc")}</span>
                  </label>
                  <select
                    value={selectedDocId}
                    onChange={(e) => setSelectedDocId(e.target.value)}
                    className="w-full px-3.5 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white focus:border-indigo-500 focus:outline-none"
                  >
                    <option value="">-- {t("courses.noDoc")} --</option>
                    {documents.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.title}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {selectedDocId && (
                <div className="p-3 bg-indigo-950/30 border border-indigo-500/30 rounded-xl text-xs text-indigo-300 flex items-start gap-2">
                  <Sparkles className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
                  <span>
                    La structure hiérarchique (Chapitres, Sections, Leçons) sera automatiquement générée à partir des extraits RAG de ce document.
                  </span>
                </div>
              )}

              <div className="pt-4 border-t border-slate-800 flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 border border-slate-800 rounded-xl text-xs font-medium text-slate-300 hover:bg-slate-900 transition"
                >
                  {t("common.cancel")}
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-xl text-xs font-semibold shadow-md shadow-indigo-950 transition"
                >
                  {isSubmitting ? t("common.loading") : t("courses.createBtn")}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default function CoursesPage() {
  return (
    <ProtectedRoute>
      <CoursesPageContent />
    </ProtectedRoute>
  );
}
