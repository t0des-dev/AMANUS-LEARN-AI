import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { SourceCitation } from "../components/chat/SourceCitation";
import { ChatInput } from "../components/chat/ChatInput";
import { TypingIndicator } from "../components/chat/TypingIndicator";
import { SourceCitation as SourceCitationType } from "../types/chat";

describe("Chat & RAG Components", () => {
  describe("SourceCitation", () => {
    const mockSources: SourceCitationType[] = [
      {
        citation_id: 1,
        document_id: "doc-1",
        document_title: "Biologie Cellulaire.pdf",
        page: 12,
        chapter: "Structure Membranaire",
        snippet: "La double couche phospholipidique est imperméable aux ions.",
        score: 0.95,
      },
      {
        citation_id: 2,
        document_id: "doc-2",
        document_title: "Génétique Médicale.pdf",
        page: 84,
        snippet: "Les mutations homozygotes récessives causent la perte de fonction.",
        score: 0.88,
      },
    ];

    it("renders citation summary count", () => {
      render(<SourceCitation sources={mockSources} />);
      expect(
        screen.getByText("2 sources documentaires citées")
      ).toBeInTheDocument();
    });

    it("expands citations when clicked to reveal excerpts", () => {
      render(<SourceCitation sources={mockSources} activeCitationId={1} />);
      const expandBtn = screen.getByText("2 sources documentaires citées");
      fireEvent.click(expandBtn);

      expect(screen.getByText("Biologie Cellulaire.pdf")).toBeInTheDocument();
      expect(screen.getByText("Génétique Médicale.pdf")).toBeInTheDocument();
      expect(screen.getByText("Page 12")).toBeInTheDocument();
      expect(screen.getByText(/La double couche phospholipidique/)).toBeInTheDocument();
    });

    it("returns null if sources list is empty", () => {
      const { container } = render(<SourceCitation sources={[]} />);
      expect(container.firstChild).toBeNull();
    });
  });

  describe("ChatInput", () => {
    it("submits message content when clicking send", () => {
      const handleSend = vi.fn();
      render(<ChatInput onSendMessage={handleSend} />);

      const textarea = screen.getByPlaceholderText(
        "Posez une question ou tapez une commande (ex: Explique-moi, Simplifie, Résume...)"
      );
      fireEvent.change(textarea, { target: { value: "Explique la mitose" } });

      const form = textarea.closest("form");
      if (form) {
        fireEvent.submit(form);
      }
      expect(handleSend).toHaveBeenCalledWith("Explique la mitose", undefined);
    });
  });

  describe("TypingIndicator", () => {
    it("renders waiting / generation indicator", () => {
      render(<TypingIndicator label="Génération RAG en cours..." />);
      expect(screen.getByText("Génération RAG en cours...")).toBeInTheDocument();
    });
  });
});
