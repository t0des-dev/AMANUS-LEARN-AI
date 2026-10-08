import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { SlideEditor } from "../components/slides/SlideEditor";
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
      fireEvent.change(titleInput, { target: { value: "Titre Modifié" } });

      const saveBtn = screen.getByRole("button", { name: /enregistrer/i });
      expect(saveBtn).not.toBeDisabled();
      fireEvent.click(saveBtn);

      expect(handleSave).toHaveBeenCalledWith("slide-1", expect.objectContaining({
        title: "Titre Modifié",
      }));
    });
  });
});
