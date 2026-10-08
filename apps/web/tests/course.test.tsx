import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { CourseProgress } from "../features/course/CourseProgress";
import { CourseOutline } from "../features/course/CourseOutline";
import { CourseItem } from "../types/course";

describe("Course Components", () => {
  describe("CourseProgress", () => {
    it("renders percentage and completion numbers correctly", () => {
      render(
        <CourseProgress
          totalLessons={10}
          completedLessons={4}
          totalMinutes={60}
        />
      );

      expect(screen.getByText("Progression du cours")).toBeInTheDocument();
      expect(screen.getByText("40%")).toBeInTheDocument();
      expect(screen.getByText("4 / 10 terminées")).toBeInTheDocument();
      expect(screen.getByText("6 restantes")).toBeInTheDocument();
      expect(screen.getByText("~60 min")).toBeInTheDocument();
    });

    it("handles 0 total lessons gracefully", () => {
      render(
        <CourseProgress
          totalLessons={0}
          completedLessons={0}
          totalMinutes={0}
        />
      );

      expect(screen.getByText("0%")).toBeInTheDocument();
      expect(screen.getByText("0 / 0 terminées")).toBeInTheDocument();
    });
  });

  describe("CourseOutline", () => {
    it("renders empty state when course has no sections", () => {
      const mockCourse: CourseItem = {
        id: "c-1",
        organization: "org-1",
        document: null,
        created_by: "u-1",
        title: "Introduction à la Biologie",
        description: "Cours introductif",
        language: "fr",
        level: "BEGINNER",
        status: "DRAFT",
        sections_count: 0,
        total_estimated_minutes: 30,
        sections: [],
        created_at: "2026-01-01",
        updated_at: "2026-01-01",
      };

      render(<CourseOutline course={mockCourse} isTeacher={false} />);
      expect(
        screen.getByText("Aucun contenu structuré pour le moment")
      ).toBeInTheDocument();
    });

    it("renders chapters and child lessons", () => {
      const mockCourse: CourseItem = {
        id: "c-1",
        organization: "org-1",
        document: null,
        created_by: "u-1",
        title: "Introduction à la Biologie",
        description: "Cours introductif",
        language: "fr",
        level: "BEGINNER",
        status: "PUBLISHED",
        sections_count: 2,
        total_estimated_minutes: 45,
        sections: [
          {
            id: "sec-1",
            course: "c-1",
            parent: null,
            title: "Chapitre 1 : La Cellule",
            order: 1,
            content: "Introduction aux cellules",
            summary: "Structure",
            objectives: [],
            estimated_minutes: 30,
            level_depth: 0,
            created_at: "2026-01-01",
            updated_at: "2026-01-01",
            children: [
              {
                id: "sec-1-1",
                course: "c-1",
                parent: "sec-1",
                title: "Leçon 1.1 : Membrane plasmique",
                order: 1,
                content: "Détails de la membrane",
                summary: "Membrane",
                objectives: [],
                estimated_minutes: 15,
                level_depth: 1,
                created_at: "2026-01-01",
                updated_at: "2026-01-01",
                children: [],
              },
            ],
          },
        ],
        created_at: "2026-01-01",
        updated_at: "2026-01-01",
      };

      render(<CourseOutline course={mockCourse} isTeacher={false} />);
      expect(screen.getByText("Chapitre 1 : La Cellule")).toBeInTheDocument();
      expect(screen.getByText("Leçon 1.1 : Membrane plasmique")).toBeInTheDocument();
      expect(screen.getByText("15 min")).toBeInTheDocument();
    });
  });
});
