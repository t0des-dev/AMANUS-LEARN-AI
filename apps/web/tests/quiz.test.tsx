import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { QuestionCard } from "../features/quiz/QuestionCard";
import { AnswerOption } from "../features/quiz/AnswerOption";
import { QuizProgress } from "../features/quiz/QuizProgress";
import { QuizQuestion } from "../types/quiz";

describe("Quiz Components", () => {
  const sampleQuestion: QuizQuestion = {
    id: "q-1",
    question: "Quelle est la principale fonction des mitochondries ?",
    order: 1,
    difficulty: "MEDIUM",
    source: "Manuel de Biologie p.42",
    explanation: "Les mitochondries produisent la majorité de l'ATP cellulaire.",
    created_at: "2026-01-01",
    answers: [
      { id: "a-1", text: "Production d'ATP", is_correct: true, order: 1 },
      { id: "a-2", text: "Synthèse de lipides", is_correct: false, order: 2 },
      { id: "a-3", text: "Dégradation des protéines", is_correct: false, order: 3 },
      { id: "a-4", text: "Stockage de calcium", is_correct: false, order: 4 },
    ],
  };

  describe("QuestionCard", () => {
    it("renders question text, options and source", () => {
      render(
        <QuestionCard
          question={sampleQuestion}
          questionIndex={0}
          totalQuestions={5}
        />
      );

      expect(screen.getByText("Question 1 / 5")).toBeInTheDocument();
      expect(
        screen.getByText("Quelle est la principale fonction des mitochondries ?")
      ).toBeInTheDocument();
      expect(screen.getByText("Production d'ATP")).toBeInTheDocument();
      expect(screen.getByText("Synthèse de lipides")).toBeInTheDocument();
      expect(screen.getByText("Source : Manuel de Biologie p.42")).toBeInTheDocument();
    });

    it("triggers onSelectAnswer when an option is clicked", () => {
      const handleSelect = vi.fn();
      render(
        <QuestionCard
          question={sampleQuestion}
          questionIndex={0}
          totalQuestions={5}
          onSelectAnswer={handleSelect}
        />
      );

      fireEvent.click(screen.getByText("Production d'ATP"));
      expect(handleSelect).toHaveBeenCalledWith("a-1");
    });

    it("displays pedagogical explanation in reviewMode", () => {
      render(
        <QuestionCard
          question={sampleQuestion}
          questionIndex={0}
          totalQuestions={5}
          reviewMode={true}
        />
      );

      expect(screen.getByText("Explication pédagogique")).toBeInTheDocument();
      expect(
        screen.getByText("Les mitochondries produisent la majorité de l'ATP cellulaire.")
      ).toBeInTheDocument();
    });
  });

  describe("AnswerOption", () => {
    it("renders label and text with selection style", () => {
      render(
        <AnswerOption
          label="A"
          text="Choix optionnel"
          selected={true}
          onClick={vi.fn()}
        />
      );

      expect(screen.getByText("A")).toBeInTheDocument();
      expect(screen.getByText("Choix optionnel")).toBeInTheDocument();
    });
  });

  describe("QuizProgress", () => {
    it("displays correct answered fraction and percentage", () => {
      render(
        <QuizProgress
          currentIndex={2}
          totalQuestions={10}
          answeredCount={3}
        />
      );

      expect(screen.getByText("Question 3")).toBeInTheDocument();
      expect(screen.getByText("sur 10")).toBeInTheDocument();
      expect(screen.getByText("répondues (30%)")).toBeInTheDocument();
    });
  });
});
