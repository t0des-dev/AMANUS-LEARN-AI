export interface StudentAnalyticsSummary {
  total_study_time_seconds: number;
  completed_courses_count: number;
  in_progress_courses_count: number;
  enrolled_courses_count: number;
  overall_progress: number;
  total_quizzes_taken: number;
  passed_quizzes_count: number;
  success_rate: number;
  average_score: number | null;
}

export interface StudyTimeDayItem {
  date: string;
  day_label: string;
  duration_seconds: number;
  duration_minutes: number;
}

export interface ScoreHistoryItem {
  id: string;
  quiz_title: string;
  score: number;
  passed: boolean;
  date: string;
}

export interface CourseProgressItem {
  course_id: string;
  course_title: string;
  status: string;
  progress: number;
  updated_at: string;
}

export interface StudentAnalyticsResponse {
  summary: StudentAnalyticsSummary;
  study_time_by_day: StudyTimeDayItem[];
  scores_history: ScoreHistoryItem[];
  courses_progress: CourseProgressItem[];
}

export interface CourseAnalyticsSummary {
  total_students: number;
  completed_students: number;
  completion_rate: number;
  average_progress: number;
  total_study_time_seconds: number;
  average_score: number | null;
  pass_rate: number;
  total_quiz_attempts: number;
}

export interface ProblematicChapterItem {
  section_id: string;
  section_title: string;
  order: number;
  completion_rate: number;
  average_score: number | null;
  students_completed: number;
  total_students: number;
  is_problematic: boolean;
}

export interface CourseAnalyticsResponse {
  course_id: string;
  course_title: string;
  summary: CourseAnalyticsSummary;
  problematic_chapters: ProblematicChapterItem[];
}

export interface StudentPerformanceItem {
  student_id: string;
  full_name: string;
  email: string;
  status: string;
  progress: number;
  total_study_time_seconds: number;
  average_score: number | null;
  started_at: string | null;
  last_activity_at: string;
}

export interface DifficultQuestionItem {
  question_id: string;
  question_text: string;
  order: number;
  difficulty: string;
  total_answers: number;
  wrong_answers: number;
  error_rate_percent: number;
}

export interface QuizAnalyticsResponse {
  quiz_id: string;
  quiz_title: string;
  course_id: string | null;
  course_title: string | null;
  total_attempts: number;
  distinct_students_count: number;
  average_score: number;
  pass_rate: number;
  difficult_questions: DifficultQuestionItem[];
}
