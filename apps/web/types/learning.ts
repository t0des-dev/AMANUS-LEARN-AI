export type LearningPathStatus = "NOT_STARTED" | "IN_PROGRESS" | "COMPLETED";

export interface LearningStats {
  total_study_time_seconds: number;
  courses_in_progress: number;
  courses_completed: number;
  total_enrolled_courses: number;
  completed_sections_count: number;
  average_score: number | null;
}

export interface ContinueLearningItem {
  course_id: string;
  course_title: string;
  section_id: string | null;
  section_title: string | null;
  section_order?: number;
  progress: number;
  section_completion_percent?: number;
  last_position?: number;
}

export interface WeakTopicItem {
  section_id: string | null;
  section_title: string;
  course_id: string;
  course_title: string;
  score: number;
  source: string;
}

export interface RecentActivityItem {
  id: string;
  course_id: string;
  course_title: string;
  started_at: string;
  ended_at: string | null;
  duration: number;
}

export interface RecommendedRevisionItem {
  type: "weak_topic" | "in_progress";
  title: string;
  course_id: string;
  course_title: string;
  section_id: string | null;
  reason: string;
}

export interface RecentQuizResultItem {
  id: string;
  quiz_id: string;
  quiz_title: string;
  course_id: string | null;
  course_title: string | null;
  score: number;
  passed: boolean;
  total_questions: number;
  correct_answers_count: number;
  completed_at: string | null;
}

export interface StudentDashboardData {
  stats: LearningStats;
  continue_learning: ContinueLearningItem | null;
  weak_topics: WeakTopicItem[];
  recent_activity: RecentActivityItem[];
  recent_quiz_results?: RecentQuizResultItem[];
  recommended_revision: RecommendedRevisionItem[];
}

export interface CourseSectionProgress {
  id: string;
  title: string;
  order: number;
  completion_percent: number;
  last_position: number;
  score: number | null;
  is_completed: boolean;
  is_weak: boolean;
}

export interface CourseLearningProgressData {
  course_id: string;
  course_title: string;
  status: LearningPathStatus;
  progress: number;
  started_at: string | null;
  completed_at: string | null;
  total_sections: number;
  completed_sections_count: number;
  remaining_sections_count: number;
  sections: CourseSectionProgress[];
  weak_sections: CourseSectionProgress[];
}

export interface LearningPathItem {
  id: string;
  course: {
    id: string;
    title: string;
    level: string;
    status: string;
    organization_name: string;
  };
  status: LearningPathStatus;
  progress: number;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface SectionCompletePayload {
  completion_percent?: number;
  last_position?: number;
  score?: number;
  is_completed?: boolean;
}

export interface StudySessionItem {
  id: string;
  course: string;
  course_title: string;
  started_at: string;
  ended_at: string | null;
  duration: number;
  created_at: string;
}
