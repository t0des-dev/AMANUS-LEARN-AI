"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { Loader2, AlertCircle, CheckCircle2 } from "lucide-react";
import { ProtectedRoute } from "../../../components/auth/ProtectedRoute";
import { useAuth } from "../../../components/auth/AuthProvider";
import { presentationService } from "../../../services/presentationService";
import {
  Presentation,
  PresentationSlide,
  UpdatePresentationPayload,
  UpdateSlidePayload,
} from "../../../types/presentation";
import { SlideNavigator } from "../../../components/slides/SlideNavigator";
import { SlidePreview } from "../../../components/slides/SlidePreview";
import { SlideEditor } from "../../../components/slides/SlideEditor";
import { PresentationToolbar } from "../../../components/slides/PresentationToolbar";

function PresentationWorkspaceContent() {
  const params = useParams();
  const router = useRouter();
  const { token } = useAuth();
  const presentationId = params?.id as string;

  const [presentation, setPresentation] = useState<Presentation | null>(null);
  const [activeSlideId, setActiveSlideId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSavingSlide, setIsSavingSlide] = useState(false);
  const [isSavingMeta, setIsSavingMeta] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [toastMsg, setToastMsg] = useState<{ text: string; type: "success" | "error" } | null>(null);

  const showToast = (text: string, type: "success" | "error" = "success") => {
    setToastMsg({ text, type });
    setTimeout(() => setToastMsg(null), 3500);
  };

  const loadPresentation = useCallback(async () => {
    if (!token || !presentationId) return;
    try {
      setIsLoading(true);
      setErrorMsg(null);
      const data = await presentationService.getPresentation(token, presentationId);
      setPresentation(data);
      if (data.slides.length > 0) {
        setActiveSlideId((prev) => (prev && data.slides.some((s) => s.id === prev) ? prev : data.slides[0].id));
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Impossible de charger la présentation.");
    } finally {
      setIsLoading(false);
    }
  }, [token, presentationId]);

  useEffect(() => {
    loadPresentation();
  }, [loadPresentation]);

  const activeSlide = presentation?.slides.find((s) => s.id === activeSlideId) || null;
  const activeSlideIndex = presentation?.slides.findIndex((s) => s.id === activeSlideId) ?? 0;

  // Handle slide title/content update
  const handleSaveSlide = async (slideId: string, payload: UpdateSlidePayload) => {
    if (!token || !presentation) return;
    setIsSavingSlide(true);
    try {
      const updatedSlide = await presentationService.updateSlide(token, presentation.id, slideId, payload);
      setPresentation((prev) => {
        if (!prev) return prev;
        const newSlides = prev.slides.map((s) => (s.id === slideId ? updatedSlide : s));
        return { ...prev, slides: newSlides };
      });
      showToast("Diapositive mise à jour avec succès.");
    } catch (err: any) {
      showToast(err.message || "Erreur lors de la sauvegarde de la slide.", "error");
      throw err;
    } finally {
      setIsSavingSlide(false);
    }
  };

  // Handle presentation title/theme update
  const handleUpdateMetadata = async (payload: UpdatePresentationPayload) => {
    if (!token || !presentation) return;
    setIsSavingMeta(true);
    try {
      const updated = await presentationService.updatePresentation(token, presentation.id, payload);
      setPresentation(updated);
      showToast("Présentation mise à jour.");
    } catch (err: any) {
      showToast(err.message || "Erreur lors de la mise à jour.", "error");
    } finally {
      setIsSavingMeta(false);
    }
  };

  // Handle adding a new slide
  const handleAddSlide = async () => {
    if (!token || !presentation) return;
    try {
      const nextNum = (presentation.slides.length || 0) + 1;
      const created = await presentationService.addSlide(token, presentation.id, {
        title: `Nouvelle Notion #${nextNum}`,
        content: "• Point pédagogique principal\n• Deuxième notion clé",
        speaker_notes: "Explication orale pour cette diapositive...",
      });
      setPresentation((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          slides: [...prev.slides, created],
          slides_count: prev.slides_count + 1,
        };
      });
      setActiveSlideId(created.id);
      showToast(`Slide #${created.slide_number} ajoutée.`);
    } catch (err: any) {
      showToast(err.message || "Erreur lors de l'ajout de la slide.", "error");
    }
  };

  // Handle deleting a slide
  const handleDeleteSlide = async (slideId: string) => {
    if (!token || !presentation) return;
    try {
      await presentationService.deleteSlide(token, presentation.id, slideId);
      // Reload presentation to ensure sequential numbering
      await loadPresentation();
      showToast("Diapositive supprimée.");
    } catch (err: any) {
      showToast(err.message || "Erreur lors de la suppression.", "error");
    }
  };

  // Handle reordering a slide up/down
  const handleMoveSlide = async (slideId: string, direction: "up" | "down") => {
    if (!token || !presentation) return;
    const slides = [...presentation.slides];
    const currentIndex = slides.findIndex((s) => s.id === slideId);
    if (currentIndex === -1) return;

    const targetIndex = direction === "up" ? currentIndex - 1 : currentIndex + 1;
    if (targetIndex < 0 || targetIndex >= slides.length) return;

    // Swap elements in array
    const temp = slides[currentIndex];
    slides[currentIndex] = slides[targetIndex];
    slides[targetIndex] = temp;

    // Compute updated slide numbers
    const payloadOrders = slides.map((slide, idx) => ({
      id: slide.id,
      slide_number: idx + 1,
    }));

    try {
      const reordered = await presentationService.reorderSlides(token, presentation.id, payloadOrders);
      setPresentation(reordered);
    } catch (err: any) {
      showToast(err.message || "Erreur lors du réordonnancement.", "error");
    }
  };

  // Handle PPTX export
  const handleExport = async (asyncMode = false) => {
    if (!token || !presentation) return;
    setIsExporting(true);
    try {
      const response = await presentationService.exportPresentation(token, presentation.id, asyncMode);
      if (response.export_url) {
        showToast("Exportation PPTX réussie ! Téléchargement en cours...");
        window.open(response.export_url, "_blank");
      } else if (response.task_id) {
        showToast("Exportation asynchrone lancée en arrière-plan.");
      }
      await loadPresentation();
    } catch (err: any) {
      showToast(err.message || "Erreur lors de l'exportation PPTX.", "error");
    } finally {
      setIsExporting(false);
    }
  };

  // Navigation handlers for preview
  const handlePrevSlide = () => {
    if (!presentation || activeSlideIndex <= 0) return;
    setActiveSlideId(presentation.slides[activeSlideIndex - 1].id);
  };

  const handleNextSlide = () => {
    if (!presentation || activeSlideIndex >= presentation.slides.length - 1) return;
    setActiveSlideId(presentation.slides[activeSlideIndex + 1].id);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center text-slate-300">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-500 mb-3" />
        <p className="text-sm">Génération & chargement de la présentation...</p>
      </div>
    );
  }

  if (errorMsg || !presentation) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-6 text-center">
        <AlertCircle className="w-12 h-12 text-rose-500 mb-4" />
        <h2 className="text-xl font-bold text-white mb-2">Impossible d&apos;accéder aux diapositives</h2>
        <p className="text-sm text-slate-400 max-w-md mb-6">{errorMsg}</p>
        <button
          onClick={() => router.back()}
          className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-xl text-sm transition"
        >
          Retourner au cours
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col overflow-hidden">
      {/* Toast Notification */}
      {toastMsg && (
        <div
          className={`fixed top-4 right-4 z-50 flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-medium shadow-2xl backdrop-blur-md animate-in fade-in slide-in-from-top-4 ${
            toastMsg.type === "success"
              ? "bg-emerald-950/90 text-emerald-200 border border-emerald-800"
              : "bg-rose-950/90 text-rose-200 border border-rose-800"
          }`}
        >
          {toastMsg.type === "success" ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          ) : (
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
          )}
          <span>{toastMsg.text}</span>
        </div>
      )}

      {/* Top Application Toolbar */}
      <PresentationToolbar
        presentation={presentation}
        onUpdateMetadata={handleUpdateMetadata}
        onExport={handleExport}
        isExporting={isExporting}
        isSavingMeta={isSavingMeta}
      />

      {/* Main Studio Body: Navigator | Preview | Editor */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Navigator (Thumbnails & Order) */}
        <SlideNavigator
          slides={presentation.slides}
          activeSlideId={activeSlideId}
          onSelectSlide={setActiveSlideId}
          onAddSlide={handleAddSlide}
          onDeleteSlide={handleDeleteSlide}
          onMoveSlide={handleMoveSlide}
          isSaving={isSavingSlide || isSavingMeta}
        />

        {/* Center Stage (16:9 Canvas & Interactive Controls) */}
        <SlidePreview
          presentation={presentation}
          currentSlide={activeSlide}
          currentIndex={activeSlideIndex}
          totalSlides={presentation.slides.length}
          onPrev={handlePrevSlide}
          onNext={handleNextSlide}
        />

        {/* Right Editor (Title, Content, Notes, Prompts) */}
        <SlideEditor
          slide={activeSlide}
          onSave={handleSaveSlide}
          isSaving={isSavingSlide}
        />
      </div>
    </div>
  );
}

export default function PresentationPage() {
  return (
    <ProtectedRoute>
      <PresentationWorkspaceContent />
    </ProtectedRoute>
  );
}
