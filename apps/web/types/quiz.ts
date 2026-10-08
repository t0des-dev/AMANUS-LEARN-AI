export type QuizType = "TRAINING" | "EXAM" | "REVISION";
export type QuizDifficulty = "EASY" | "MEDIUM" | "HARD";
export type DifficultyLevel = QuizDifficulty;

export type QuizStatus = "DRAFT" | "PUBLISHED" | "ARCHIVED";

export interface QuizAnswer {
  id: string;
  text: string;
  is_correct?: boolean;
  order: number;
}
export type QuizAnswerItem = QuizAnswer;

export interface QuizQuestion {
  id: string;
  question: string;
  text?: string;
  explanation: string;
  difficulty: QuizDifficulty;
  source: string;
  order: number;
  answers: QuizAnswer[];
  created_at: string;
}
export type QuizQuestionItem = QuizQuestion;

export interface Quiz {
  id: string;
  organization: string;
  organization_name?: string;
  course: string | null;
  course_title?: string;
  document?: string | null;
  title: string;
  description: string;
  quiz_type: QuizType;
  type?: QuizType;
  difficulty: QuizDifficulty;
  time_limit_minutes: number | null;
  passing_score: number;
  passing_score_percentage?: number;
  is_published?: boolean;
  status?: QuizStatus;
  question_count?: number;
  questions_count?: number;
  questions?: QuizQuestion[];
  created_at: string;
  updated_at: string;
}
export type QuizItem = Quiz;

export interface QuestionBreakdownItem {
  question_id: string;
  question_text: string;
  text?: string;
  selected_answer_id: string | null;
  correct_answer_id: string | null;
  is_correct: boolean;
  points_earned: number;
  explanation: string;
  difficulty?: QuizDifficulty;
  source?: string;
}
export type QuestionReviewItem = QuestionBreakdownItem;

export interface QuizAttempt {
  id: string;
  quiz: string;
  quiz_title?: string;
  quiz_type?: QuizType;
  quiz_passing_score?: number;
  user?: string;
  user_email?: string;
  score: number;
  is_passed: boolean;
  passed?: boolean;
  total_questions: number;
  correct_answers: number;
  correct_answers_count?: number;
  answers_data?: Record<string, string>;
  results_breakdown: QuestionBreakdownItem[];
  questions_review?: QuestionBreakdownItem[];
  started_at: string;
  completed_at: string | null;
  time_spent_seconds: number | null;
}
export type QuizAttemptItem = QuizAttempt;
export type QuizEvaluationResult = QuizAttempt;

export interface CreateQuizPayload {
  organization: string;
  course?: string | null;
  document?: string | null;
  title: string;
  description?: string;
  quiz_type?: QuizType;
  type?: QuizType;
  difficulty?: QuizDifficulty;
  time_limit_minutes?: number;
  passing_score?: number;
  passing_score_percentage?: number;
  status?: QuizStatus;
  generate_ai?: boolean;
  questions_count?: number;
}

export interface GenerateQuizPayload {
  document_id?: string;
  course_id?: string;
  count?: number;
  difficulty?: QuizDifficulty;
  prompt?: string;
  provider?: string;
  model?: string;
  focus?: string;
  top_k?: number;
}

export interface SubmitQuizAnswer {
  question_id: string;
  selected_answer_id: string;
}

export interface SubmitQuizPayload {
  attempt_id?: string;
  answers: SubmitQuizAnswer[] | Record<string, string>;
}

export interface QuizResultsResponse {
  quiz_id?: string;
  quiz_title?: string;
  passing_score?: number;
  best_score?: number;
  has_passed?: boolean;
  total_attempts?: number;
  attempts: QuizAttempt[];
}
