import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { LearningStatsGrid } from "../components/learning/LearningStatsGrid";
import { WeakTopicsList } from "../components/learning/WeakTopicsList";
import { LearningStats, WeakTopicItem } from "../types/learning";

describe("Learning Analytics & Progress Components", () => {
  describe("LearningStatsGrid", () => {
    it("renders formatted duration, section count, enrolled courses and average score", () => {
      const stats: LearningStats = {
        total_study_time_seconds: 7320, // 2h 2m
        completed_sections_count: 14,
        total_enrolled_courses: 3,
        courses_in_progress: 2,
        courses_completed: 1,
        average_score: 87.5,
      };

      render(<LearningStatsGrid stats={stats} />);

      expect(screen.getByText("Temps d'étude effectif")).toBeInTheDocument();
      expect(screen.getByText("2h 2m")).toBeInTheDocument();
      expect(screen.getByText("14")).toBeInTheDocument();
      expect(screen.getByText("2 / 3")).toBeInTheDocument();
      expect(screen.getByText("88%")).toBeInTheDocument();
    });
  });

  describe("WeakTopicsList", () => {
    it("renders congratulatory state when no weak topics exist", () => {
      render(<WeakTopicsList topics={[]} />);
      expect(screen.getByText("Excellente maîtrise générale !")).toBeInTheDocument();
    });

    it("renders weak topic items with score indicators", () => {
      const topics: WeakTopicItem[] = [
        {
          section_id: "sec-1",
          section_title: "Mitose et Méiose",
          course_id: "c-1",
          course_title: "Génétique",
          score: 42.0,
          source: "QCM Chapitre 1",
        },
      ];

      render(<WeakTopicsList topics={topics} />);
      expect(screen.getByText("Mitose et Méiose")).toBeInTheDocument();
      expect(screen.getByText(/Génétique/)).toBeInTheDocument();
      expect(screen.getByText(/42/)).toBeInTheDocument();
    });
  });
});
