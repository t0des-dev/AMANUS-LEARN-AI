"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import {
  ArrowLeft,
  Save,
  Plus,
  Trash2,
  Sparkles,
  Layers,
  FileText,
  Eye,
  Settings,
  AlertCircle,
  Check,
} from "lucide-react";
import { ProtectedRoute } from "../../../../components/auth/ProtectedRoute";
import { useAuth } from "../../../../components/auth/AuthProvider";
import { courseService } from "../../../../services/courseService";
import {
  CourseItem,
  CourseLevel,
  CourseSectionItem,
  CourseStatus,
  UpdateCoursePayload,
  UpdateSectionPayload,
} from "../../../../types/course";
import { LessonEditor } from "../../../../features/course/LessonEditor";

function findSectionById(
  sections: CourseSectionItem[],
  id: string
): CourseSectionItem | null {
  for (const sec of sections) {
    if (sec.id === id) return sec;
    if (sec.children && sec.children.length > 0) {
      const res = findSectionById(sec.children, id);
      if (res) return res;
    }
  }
  return null;
}

function findFirstLeafSection(
  sections: CourseSectionItem[]
): CourseSectionItem | null {
  for (const sec of sections) {
    if (sec.children && sec.children.length > 0) {
      const leaf = findFirstLeafSection(sec.children);
      if (leaf) return leaf;
    }
    return sec;
  }
  return null;
}

function CourseEditPageContent() {
  const params = useParams();
  const searchParams = useSearchParams();
  const courseId = params?.id as string;
  const initialSectionId = searchParams?.get("section");
  const router = useRouter();
  const { token } = useAuth();

  const [course, setCourse] = useState<CourseItem | null>(null);
  const [selectedSection, setSelectedSection] =
    useState<CourseSectionItem | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isGeneratingAI, setIsGeneratingAI] = useState(false);

  // Course general settings state
  const [courseTitle, setCourseTitle] = useState("");
  const [courseDesc, setCourseDesc] = useState("");
  const [courseLevel, setCourseLevel] = useState<CourseLevel>("BEGINNER");
  const [courseStatus, setCourseStatus] = useState<CourseStatus>("DRAFT");
  const [isSavingCourse, setIsSavingCourse] = useState(false);
  const [courseSaveSuccess, setCourseSaveSuccess] = useState(false);

  // New chapter modal
  const [showAddChapter, setShowAddChapter] = useState(false);
  const [newChapterTitle, setNewChapterTitle] = useState("");
  const [newChapterMinutes, setNewChapterMinutes] = useState(30);

  const fetchCourse = useCallback(async () => {
    if (!token || !courseId) return;
    setIsLoading(true);
    setError(null);

    try {
      const data = await courseService.get(token, courseId);
      setCourse(data);
      setCourseTitle(data.title);
      setCourseDesc(data.description || "");
      setCourseLevel(data.level);
      setCourseStatus(data.status);

      // Select requested or first section
      if (initialSectionId) {
        const found = findSectionById(data.sections || [], initialSectionId);
        if (found) setSelectedSection(found);
      } else if (data.sections && data.sections.length > 0) {
        const firstLeaf = findFirstLeafSection(data.sections);
        if (firstLeaf) setSelectedSection(firstLeaf);
      }
    } catch (err: any) {
      setError(err.message || "Impossible de charger le cours pour édition.");
    } finally {
      setIsLoading(false);
    }
  }, [token, courseId, initialSectionId]);

  useEffect(() => {
    fetchCourse();
  }, [fetchCourse]);

  const handleSaveCourseSettings = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !course) return;

    setIsSavingCourse(true);
    try {
      const updated = await courseService.update(token, course.id, {
        title: courseTitle,
        description: courseDesc,
        level: courseLevel,
        status: courseStatus,
      });
      setCourse(updated);
      setCourseSaveSuccess(true);
      setTimeout(() => setCourseSaveSuccess(false), 3000);
    } catch (err: any) {
      alert(err.message || "Erreur de mise à jour.");
    } finally {
      setIsSavingCourse(false);
    }
  };

  const handleSaveSection = async (payload: UpdateSectionPayload) => {
    if (!token || !selectedSection) return;
    const updated = await courseService.updateSection(
      token,
      selectedSection.id,
      payload
    );
    setSelectedSection(updated);
    // Refresh course hierarchy in background
    const refreshed = await courseService.get(token, courseId);
    setCourse(refreshed);
  };

  const handleDeleteSection = async (sectionId: string) => {
    if (!token) return;
    if (!confirm("Voulez-vous supprimer cette section et son sous-contenu ?"))
      return;

    try {
      await courseService.deleteSection(token, sectionId);
      if (selectedSection?.id === sectionId) {
        setSelectedSection(null);
      }
      await fetchCourse();
    } catch (err: any) {
      alert(err.message || "Erreur lors de la suppression.");
    }
  };

  const handleAddChapterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !course || !newChapterTitle.trim()) return;

    try {
      await courseService.createSection(token, course.id, {
        parent: null,
        title: newChapterTitle,
        estimated_minutes: newChapterMinutes,
      });
      setShowAddChapter(false);
      setNewChapterTitle("");
      await fetchCourse();
    } catch (err: any) {
      alert(err.message || "Erreur lors de l'ajout du chapitre.");
    }
  };

  const handleTriggerAIGenerate = async () => {
    if (!token || !course) return;
    if (
      !confirm(
        "Régénérer le cours via l'IA va restructurer les chapitres à partir du document. Continuer ?"
      )
    )
      return;

    setIsGeneratingAI(true);
    try {
      const updated = await courseService.generate(token, course.id);
      setCourse(updated);
      const firstLeaf = findFirstLeafSection(updated.sections || []);
      if (firstLeaf) setSelectedSection(firstLeaf);
    } catch (err: any) {
      alert(err.message || "Échec de la génération IA.");
    } finally {
      setIsGeneratingAI(false);
    }
  };

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-12">
        <div className="h-20 bg-gray-100 rounded-xl animate-pulse mb-6" />
        <div className="h-96 bg-gray-100 rounded-xl animate-pulse" />
      </div>
    );
  }

  if (!course) {
    return (
      <div className="max-w-md mx-auto py-12 text-center text-red-600">
        Cours introuvable.
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      {/* Top action header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-gray-200 pb-4">
        <div className="flex items-center gap-3">
          <Link
            href={`/courses/${course.id}`}
            className="p-2 text-gray-500 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-xl font-extrabold text-gray-900">
              Éditeur de cours : {course.title}
            </h1>
            <p className="text-xs text-gray-500">
              Modifiez librement le contenu IA, ajoutez vos propres leçons et ajustez les objectifs.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 self-end sm:self-auto">
          {course.document && (
            <button
              type="button"
              onClick={handleTriggerAIGenerate}
              disabled={isGeneratingAI}
              className="inline-flex items-center gap-1.5 px-3 py-2 border border-indigo-200 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 rounded-lg text-xs font-semibold transition-colors"
            >
              <Sparkles className="w-3.5 h-3.5" />
              {isGeneratingAI ? "Génération..." : "Régénérer avec IA"}
            </button>
          )}

          <Link
            href={`/courses/${course.id}/learn`}
            className="inline-flex items-center gap-1.5 px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-800 rounded-lg text-xs font-bold transition-colors"
          >
            <Eye className="w-3.5 h-3.5" />
            Aperçu Apprenant
          </Link>
        </div>
      </div>

      {/* Editor Two-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Outline Tree & Structure Navigation (5 cols) */}
        <div className="lg:col-span-4 bg-white rounded-xl border border-gray-200 p-4 space-y-4 shadow-sm">
          <div className="flex items-center justify-between border-b border-gray-100 pb-3">
            <h2 className="text-sm font-bold text-gray-900 flex items-center gap-2">
              <Layers className="w-4 h-4 text-blue-600" />
              Structure du cours
            </h2>
            <button
              type="button"
              onClick={() => setShowAddChapter(true)}
              className="inline-flex items-center gap-1 text-xs text-blue-600 hover:text-blue-700 font-semibold"
            >
              <Plus className="w-3.5 h-3.5" />
              Chapitre
            </button>
          </div>

          {/* Quick link to General Settings */}
          <button
            type="button"
            onClick={() => setSelectedSection(null)}
            className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-semibold transition-colors ${
              selectedSection === null
                ? "bg-blue-50 text-blue-700"
                : "text-gray-600 hover:bg-gray-50"
            }`}
          >
            <span className="flex items-center gap-2">
              <Settings className="w-3.5 h-3.5" />
              Paramètres généraux du cours
            </span>
          </button>

          {/* Chapters & Lessons Tree */}
          <div className="space-y-3 pt-2">
            {(course.sections || []).map((chapter, cIdx) => (
              <div
                key={chapter.id}
                className="border border-gray-200 rounded-lg overflow-hidden bg-gray-50/40"
              >
                {/* Chapter bar */}
                <div className="p-2.5 flex items-center justify-between bg-gray-100/60 text-xs font-bold text-gray-800">
                  <span className="truncate pr-2">
                    {cIdx + 1}. {chapter.title}
                  </span>
                  <div className="flex items-center gap-1">
                    <button
                      type="button"
                      onClick={() => setSelectedSection(chapter)}
                      className="p-1 text-gray-500 hover:text-blue-600 rounded"
                      title="Éditer chapitre"
                    >
                      <Settings className="w-3 h-3" />
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDeleteSection(chapter.id)}
                      className="p-1 text-gray-400 hover:text-red-600 rounded"
                      title="Supprimer"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                </div>

                {/* Subsections & Lessons */}
                <div className="p-1.5 space-y-1 bg-white">
                  {(chapter.children || []).map((sec) => (
                    <div key={sec.id} className="space-y-1 pl-2">
                      <div className="text-[11px] font-semibold text-gray-500 pt-1 flex items-center justify-between">
                        <span className="truncate">{sec.title}</span>
                        <button
                          type="button"
                          onClick={() => handleDeleteSection(sec.id)}
                          className="p-0.5 text-gray-300 hover:text-red-500"
                        >
                          <Trash2 className="w-2.5 h-2.5" />
                        </button>
                      </div>

                      {/* Lessons inside Section */}
                      {(sec.children || []).map((lesson) => {
                        const isSelected = selectedSection?.id === lesson.id;
                        return (
                          <div
                            key={lesson.id}
                            className={`flex items-center justify-between px-2.5 py-1.5 rounded-md text-xs cursor-pointer transition-colors ${
                              isSelected
                                ? "bg-blue-50 text-blue-700 font-semibold"
                                : "text-gray-700 hover:bg-gray-50"
                            }`}
                            onClick={() => setSelectedSection(lesson)}
                          >
                            <span className="flex items-center gap-1.5 truncate pr-2">
                              <FileText className="w-3 h-3 shrink-0 text-blue-500" />
                              <span className="truncate">{lesson.title}</span>
                            </span>
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDeleteSection(lesson.id);
                              }}
                              className="text-gray-300 hover:text-red-500 p-0.5"
                            >
                              <Trash2 className="w-3 h-3" />
                            </button>
                          </div>
                        );
                      })}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Column: Editor Panel (7 cols) */}
        <div className="lg:col-span-8">
          {selectedSection ? (
            <div>
              <div className="mb-4 flex items-center justify-between">
                <div>
                  <span className="text-xs font-semibold text-blue-600 uppercase tracking-wider">
                    Édition de contenu
                  </span>
                  <h2 className="text-lg font-bold text-gray-900">
                    {selectedSection.title}
                  </h2>
                </div>
                <span className="text-xs text-gray-400">
                  ID : {selectedSection.id.slice(0, 8)}...
                </span>
              </div>

              <LessonEditor
                key={selectedSection.id}
                lesson={selectedSection}
                onSave={handleSaveSection}
              />
            </div>
          ) : (
            /* Course General Settings Editor */
            <form
              onSubmit={handleSaveCourseSettings}
              className="bg-white rounded-xl border border-gray-200 p-6 lg:p-8 space-y-6 shadow-sm"
            >
              <div>
                <h2 className="text-lg font-bold text-gray-900 mb-1">
                  Paramètres généraux du cours
                </h2>
                <p className="text-xs text-gray-500">
                  Modifiez le titre, le résumé, le niveau et le statut de publication du cours.
                </p>
              </div>

              {courseSaveSuccess && (
                <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-sm text-emerald-700 flex items-center gap-2">
                  <Check className="w-4 h-4 shrink-0" />
                  <span>Paramètres du cours mis à jour avec succès !</span>
                </div>
              )}

              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                    Titre du cours *
                  </label>
                  <input
                    type="text"
                    required
                    value={courseTitle}
                    onChange={(e) => setCourseTitle(e.target.value)}
                    className="w-full px-3.5 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                    Description
                  </label>
                  <textarea
                    rows={4}
                    value={courseDesc}
                    onChange={(e) => setCourseDesc(e.target.value)}
                    className="w-full px-3.5 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                      Niveau
                    </label>
                    <select
                      value={courseLevel}
                      onChange={(e) =>
                        setCourseLevel(e.target.value as CourseLevel)
                      }
                      className="w-full px-3.5 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="BEGINNER">Débutant</option>
                      <option value="INTERMEDIATE">Intermédiaire</option>
                      <option value="ADVANCED">Avancé</option>
                      <option value="EXPERT">Expert</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                      Statut de publication
                    </label>
                    <select
                      value={courseStatus}
                      onChange={(e) =>
                        setCourseStatus(e.target.value as CourseStatus)
                      }
                      className="w-full px-3.5 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="DRAFT">Brouillon</option>
                      <option value="PUBLISHED">Publié (visible étudiants)</option>
                      <option value="ARCHIVED">Archivé</option>
                    </select>
                  </div>
                </div>
              </div>

              <div className="pt-4 border-t border-gray-100 flex justify-end">
                <button
                  type="submit"
                  disabled={isSavingCourse}
                  className="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg text-sm font-semibold shadow-sm"
                >
                  <Save className="w-4 h-4" />
                  {isSavingCourse ? "Sauvegarde..." : "Enregistrer les modifications"}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>

      {/* Add Chapter Modal */}
      {showAddChapter && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 space-y-4 shadow-xl">
            <h3 className="text-base font-bold text-gray-900">
              Ajouter un nouveau chapitre
            </h3>
            <form onSubmit={handleAddChapterSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                  Titre du chapitre
                </label>
                <input
                  type="text"
                  required
                  value={newChapterTitle}
                  onChange={(e) => setNewChapterTitle(e.target.value)}
                  placeholder="Ex : Chapitre 3 : Traitement du Langage Naturel"
                  className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                  Durée estimée (minutes)
                </label>
                <input
                  type="number"
                  min={5}
                  value={newChapterMinutes}
                  onChange={(e) => setNewChapterMinutes(Number(e.target.value))}
                  className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddChapter(false)}
                  className="px-3.5 py-1.5 border border-gray-200 rounded-lg text-xs font-medium text-gray-700 hover:bg-gray-50"
                >
                  Annuler
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold"
                >
                  Ajouter
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default function CourseEditPage() {
  return (
    <ProtectedRoute>
      <CourseEditPageContent />
    </ProtectedRoute>
  );
}
