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
} from "lucide-react";
import { ProtectedRoute } from "../../components/auth/ProtectedRoute";
import { useAuth } from "../../components/auth/AuthProvider";
import { useOrganization } from "../../components/organization/OrganizationContext";
import { courseService } from "../../services/courseService";
import { documentService } from "../../services/documentService";
import { CourseItem, CourseLevel } from "../../types/course";
import { DocumentItem } from "../../types/document";

function CoursesPageContent() {
  const { token, user } = useAuth();
  const { currentOrg } = useOrganization();

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
      setError(err.message || "Impossible de charger les cours.");
    } finally {
      setIsLoading(false);
    }
  }, [token, currentOrg]);

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
      setError(err.message || "Erreur lors de la création du cours.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteCourse = async (courseId: string) => {
    if (!token) return;
    if (!confirm("Êtes-vous sûr de vouloir supprimer ce cours ?")) return;

    try {
      await courseService.delete(token, courseId);
      setCourses((prev) => prev.filter((c) => c.id !== courseId));
    } catch (err: any) {
      alert(err.message || "Erreur lors de la suppression.");
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-blue-700 via-indigo-700 to-purple-800 rounded-2xl p-6 sm:p-8 text-white shadow-md flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-2 mb-2 text-blue-200 text-xs font-semibold uppercase tracking-wider">
            <GraduationCap className="w-4 h-4" />
            <span>Moteur Pédagogique & Course Builder</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
            Cours & Modules d&apos;Apprentissage
          </h1>
          <p className="mt-2 text-sm sm:text-base text-blue-100 max-w-2xl">
            Transformez vos documents et synthèses analysés en véritables cours structurés (Chapitres, Sections, Leçons). Le contenu généré par l&apos;IA est entièrement éditable par les enseignants.
          </p>
        </div>

        <button
          type="button"
          onClick={() => setShowCreateModal(true)}
          className="inline-flex items-center gap-2 px-5 py-3 bg-white text-blue-700 hover:bg-blue-50 font-bold rounded-xl text-sm transition-all shadow-sm shrink-0"
        >
          <PlusCircle className="w-4 h-4" />
          Créer un cours
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Courses List Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map((n) => (
            <div
              key={n}
              className="h-64 bg-gray-100 rounded-2xl animate-pulse"
            />
          ))}
        </div>
      ) : courses.length === 0 ? (
        <div className="bg-white rounded-2xl border border-dashed border-gray-300 p-12 text-center">
          <div className="w-14 h-14 bg-blue-50 text-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <BookOpen className="w-7 h-7" />
          </div>
          <h3 className="text-lg font-bold text-gray-900 mb-1">
            Aucun cours disponible dans cette organisation
          </h3>
          <p className="text-sm text-gray-500 max-w-md mx-auto mb-6">
            Créez votre premier cours ou transformez un document PDF/DOCX en parcours d&apos;apprentissage complet grâce à l&apos;IA.
          </p>
          <button
            type="button"
            onClick={() => setShowCreateModal(true)}
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl text-sm transition-colors"
          >
            <PlusCircle className="w-4 h-4" />
            Créer un cours
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {courses.map((course) => (
            <div
              key={course.id}
              className="bg-white rounded-2xl border border-gray-200 hover:border-blue-300 hover:shadow-md transition-all flex flex-col overflow-hidden"
            >
              <div className="p-6 flex-1 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <span
                      className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                        course.status === "PUBLISHED"
                          ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                          : "bg-amber-50 text-amber-700 border border-amber-200"
                      }`}
                    >
                      {course.status === "PUBLISHED" ? "Publié" : "Brouillon"}
                    </span>

                    <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">
                      {course.level}
                    </span>
                  </div>

                  <h3 className="text-lg font-bold text-gray-900 mb-2 line-clamp-1">
                    {course.title}
                  </h3>

                  <p className="text-xs sm:text-sm text-gray-500 line-clamp-3 mb-4 leading-relaxed">
                    {course.description || "Aucune description renseignée."}
                  </p>
                </div>

                <div className="pt-4 border-t border-gray-100 flex items-center justify-between text-xs text-gray-500">
                  <div className="flex items-center gap-1.5">
                    <Layers className="w-3.5 h-3.5 text-blue-500" />
                    <span>{course.sections_count} sections</span>
                  </div>

                  <div className="flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5 text-purple-500" />
                    <span>~{course.total_estimated_minutes} min</span>
                  </div>
                </div>
              </div>

              {/* Bottom Actions */}
              <div className="bg-gray-50 px-6 py-3 border-t border-gray-100 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Link
                    href={`/courses/${course.id}/edit`}
                    className="p-1.5 text-gray-500 hover:text-blue-600 hover:bg-white rounded-lg transition-colors"
                    title="Éditer le cours"
                  >
                    <Edit className="w-4 h-4" />
                  </Link>

                  <button
                    type="button"
                    onClick={() => handleDeleteCourse(course.id)}
                    className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-white rounded-lg transition-colors"
                    title="Supprimer"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>

                <Link
                  href={`/courses/${course.id}`}
                  className="inline-flex items-center gap-1.5 text-xs font-bold text-blue-600 hover:text-blue-700"
                >
                  Voir le cours
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Course Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 sm:p-8 space-y-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-gray-100 pb-4">
              <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                <GraduationCap className="w-5 h-5 text-blue-600" />
                Créer un nouveau cours
              </h3>
              <button
                type="button"
                onClick={() => setShowCreateModal(false)}
                className="text-gray-400 hover:text-gray-600 text-lg font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateCourse} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">
                  Titre du cours *
                </label>
                <input
                  type="text"
                  required
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="Ex : Apprentissage Profond & Réseaux Convolutifs"
                  className="w-full px-3.5 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">
                  Description
                </label>
                <textarea
                  rows={3}
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  placeholder="Objectifs et public visé pour ce cours..."
                  className="w-full px-3.5 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">
                    Niveau
                  </label>
                  <select
                    value={newLevel}
                    onChange={(e) => setNewLevel(e.target.value as CourseLevel)}
                    className="w-full px-3.5 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="BEGINNER">Débutant</option>
                    <option value="INTERMEDIATE">Intermédiaire</option>
                    <option value="ADVANCED">Avancé</option>
                    <option value="EXPERT">Expert</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1 flex items-center gap-1">
                    <Sparkles className="w-3.5 h-3.5 text-indigo-500" />
                    Document source (RAG)
                  </label>
                  <select
                    value={selectedDocId}
                    onChange={(e) => setSelectedDocId(e.target.value)}
                    className="w-full px-3.5 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">-- Aucun (cours manuel) --</option>
                    {documents.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.title}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {selectedDocId && (
                <div className="p-3 bg-indigo-50 border border-indigo-200 rounded-lg text-xs text-indigo-900 flex items-start gap-2">
                  <Sparkles className="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />
                  <span>
                    La structure hiérarchique (Chapitres, Sections, Leçons) sera automatiquement générée à partir des extraits RAG de ce document. Vous pourrez ensuite l&apos;éditer librement.
                  </span>
                </div>
              )}

              <div className="pt-4 border-t border-gray-100 flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 border border-gray-200 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  Annuler
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg text-sm font-semibold shadow-sm"
                >
                  {isSubmitting ? "Création en cours..." : "Créer le cours"}
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
