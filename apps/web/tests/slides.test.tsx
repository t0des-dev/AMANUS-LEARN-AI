import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, act } from "@testing-library/react";
import { SlideEditor } from "../components/slides/SlideEditor";
import { SlidePreview } from "../components/slides/SlidePreview";
import { PresentationSlide } from "../types/presentation";

describe("Slides Components", () => {
  describe("SlideEditor", () => {
    it("renders fallback message when no slide is selected", () => {
      render(
        <SlideEditor
          slide={null}
          onSave={vi.fn()}
          isSaving={false}
        />
      );

      expect(
        screen.getByText("Sélectionnez une diapositive pour commencer l'édition.")
      ).toBeInTheDocument();
    });

    it("populates inputs with slide details and handles edits", () => {
      const mockSlide: PresentationSlide = {
        id: "slide-1",
        presentation: "pres-1",
        slide_number: 1,
        title: "Introduction aux Réseaux",
        content: "- Modèle OSI\n- Protocoles TCP/IP",
        speaker_notes: "Expliquer les 7 couches",
        image_prompt: "Schéma réseau moderne",
        image_url: "",
        created_at: "2026-01-01",
        updated_at: "2026-01-01",
      };

      const handleSave = vi.fn().mockResolvedValue(undefined);

      render(
        <SlideEditor
          slide={mockSlide}
          onSave={handleSave}
          isSaving={false}
        />
      );

      expect(screen.getByDisplayValue("Introduction aux Réseaux")).toBeInTheDocument();
      expect(screen.getByDisplayValue("Schéma réseau moderne")).toBeInTheDocument();

      const titleInput = screen.getByDisplayValue("Introduction aux Réseaux");
      act(() => {
        fireEvent.change(titleInput, { target: { value: "Titre Modifié" } });
      });

      const saveBtn = screen.getByRole("button", { name: /enregistrer/i });
      expect(saveBtn).not.toBeDisabled();
      act(() => {
        fireEvent.click(saveBtn);
      });

      expect(handleSave).toHaveBeenCalledWith("slide-1", expect.objectContaining({
        title: "Titre Modifié",
      }));
    });
  });

  describe("SlidePreview", () => {
    const mockPresentation = {
      id: "pres-1",
      course: "c-1",
      course_title: "Cours Python",
      title: "Présentation Test",
      theme: "modern_dark" as const,
      status: "READY" as const,
      storage_key: "",
      export_url: null,
      slides_count: 3,
      slides: [],
      created_at: "2026-01-01",
      updated_at: "2026-01-01",
    };

    it("renders slide content and navigation info", () => {
      const mockSlide: PresentationSlide = {
        id: "s-1",
        presentation: "pres-1",
        slide_number: 2,
        title: "Architecture & Principes",
        content: "• Point 1 : Notions de base\n• Point 2 : Cas pratiques",
        speaker_notes: "Notes pour le présentateur",
        image_prompt: "Schéma d'architecture",
        image_url: "",
        created_at: "2026-01-01",
        updated_at: "2026-01-01",
      };

      render(
        <SlidePreview
          presentation={mockPresentation}
          currentSlide={mockSlide}
          currentIndex={1}
          totalSlides={3}
          onPrev={vi.fn()}
          onNext={vi.fn()}
        />
      );

      expect(screen.getByText("Architecture & Principes")).toBeInTheDocument();
      expect(screen.getByText("Point 1 : Notions de base")).toBeInTheDocument();
      expect(screen.getByText("Diapositive 2 / 3")).toBeInTheDocument();
    });

    it("renders Arabic RTL layout when slide contains Arabic text", () => {
      const mockSlide: PresentationSlide = {
        id: "s-2",
        presentation: "pres-1",
        slide_number: 1,
        title: "المفاهيم الجوهرية للذكاء الاصطناعي",
        content: "• النقطة الأولى : المبادئ الأساسية\n• النقطة الثانية : التطبيقات الميدانية",
        speaker_notes: "",
        image_prompt: "",
        image_url: "",
        created_at: "2026-01-01",
        updated_at: "2026-01-01",
      };

      const { container } = render(
        <SlidePreview
          presentation={mockPresentation}
          currentSlide={mockSlide}
          currentIndex={0}
          totalSlides={3}
          onPrev={vi.fn()}
          onNext={vi.fn()}
        />
      );

      expect(screen.getByText("المفاهيم الجوهرية للذكاء الاصطناعي")).toBeInTheDocument();
      const rtlDiv = container.querySelector('[dir="rtl"]');
      expect(rtlDiv).not.toBeNull();
      expect(screen.getByText("الشريحة 1 / 3")).toBeInTheDocument();
    });

    it("renders two-column layout when content contains delimiter", () => {
      const mockSlide: PresentationSlide = {
        id: "s-3",
        presentation: "pres-1",
        slide_number: 2,
        title: "Comparaison Méthodes",
        content: "• Approche A : Théorie\n || \n• Approche B : Pratique",
        speaker_notes: "",
        image_prompt: "",
        image_url: "",
        created_at: "2026-01-01",
        updated_at: "2026-01-01",
      };

      render(
        <SlidePreview
          presentation={mockPresentation}
          currentSlide={mockSlide}
          currentIndex={1}
          totalSlides={3}
          onPrev={vi.fn()}
          onNext={vi.fn()}
        />
      );

      expect(screen.getByText("Approche A : Théorie")).toBeInTheDocument();
      expect(screen.getByText("Approche B : Pratique")).toBeInTheDocument();
    });
  });
});
