import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { CourseAnalytics } from "../components/analytics/CourseAnalytics";
import { StudentPerformance } from "../components/analytics/StudentPerformance";
import { CourseAnalyticsResponse, StudentPerformanceItem } from "../types/analytics";

describe("Dashboard & Analytics Components", () => {
  describe("CourseAnalytics", () => {
    const mockData: CourseAnalyticsResponse = {
      course_id: "c-1",
      course_title: "Physiologie Cardiovasculaire",
      summary: {
        total_students: 48,
        completed_students: 12,
        completion_rate: 25.0,
        average_progress: 62.4,
        average_score: 78.1,
        pass_rate: 85.0,
        total_quiz_attempts: 100,
        total_study_time_seconds: 14400,
      },
      problematic_chapters: [],
    };

    it("renders KPIs (total enrolled, progress, completion rate)", () => {
      render(<CourseAnalytics data={mockData} />);

      expect(screen.getByText("Étudiants inscrits")).toBeInTheDocument();
      expect(screen.getByText("48")).toBeInTheDocument();
      expect(screen.getByText("Progression moyenne")).toBeInTheDocument();
      expect(screen.getByText("62%")).toBeInTheDocument();
      expect(screen.getByText("Taux de complétion : 25%")).toBeInTheDocument();
    });
  });

  describe("StudentPerformance", () => {
    const mockStudents: StudentPerformanceItem[] = [
      {
        student_id: "s-1",
        full_name: "Jean Dupont",
        email: "jean.dupont@etu.univ.fr",
        progress: 85.0,
        status: "COMPLETED",
        average_score: 92.0,
        total_study_time_seconds: 3600,
        started_at: "2026-01-01T00:00:00Z",
        last_activity_at: "2026-03-01T10:00:00Z",
      },
      {
        student_id: "s-2",
        full_name: "Sarah Connor",
        email: "sarah.connor@etu.univ.fr",
        progress: 30.0,
        status: "IN_PROGRESS",
        average_score: 45.0,
        total_study_time_seconds: 1200,
        started_at: "2026-01-01T00:00:00Z",
        last_activity_at: "2026-03-02T14:00:00Z",
      },
    ];

    it("renders students list with progress and scores", () => {
      render(<StudentPerformance students={mockStudents} />);

      expect(screen.getByText("Jean Dupont")).toBeInTheDocument();
      expect(screen.getByText("Sarah Connor")).toBeInTheDocument();
      expect(screen.getByText("85%")).toBeInTheDocument();
      expect(screen.getByText("92%")).toBeInTheDocument();
    });

    it("filters student list based on search term", () => {
      render(<StudentPerformance students={mockStudents} />);

      const searchInput = screen.getByPlaceholderText(
        "Rechercher un apprenant..."
      );
      fireEvent.change(searchInput, { target: { value: "Sarah" } });

      expect(screen.queryByText("Jean Dupont")).not.toBeInTheDocument();
      expect(screen.getByText("Sarah Connor")).toBeInTheDocument();
    });
  });
});
