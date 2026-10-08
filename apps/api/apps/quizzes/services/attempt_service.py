import logging
from typing import Any

from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.quizzes.models import Quiz, QuizAttempt

User = get_user_model()
logger = logging.getLogger(__name__)


class QuizAttemptService:
    """Manages quiz sessions, scoring, time tracking, and attempt evaluations."""

    def start_attempt(self, quiz: Quiz, user: Any) -> QuizAttempt:
        """Initializes a new quiz attempt session."""
        attempt = QuizAttempt.objects.create(
            quiz=quiz,
            user=user,
            total_questions=quiz.questions.count(),
            started_at=timezone.now(),
        )
        logger.info("User %s started attempt %s on quiz %s", user.id, attempt.id, quiz.id)
        return attempt

    def submit_attempt(
        self,
        attempt: QuizAttempt,
        submitted_answers: dict[str, str],
    ) -> dict[str, Any]:
        """Evaluates submitted answers, calculates score, and records results.

        Args:
            attempt: The active QuizAttempt instance
            submitted_answers: Dict mapping question_id -> chosen_answer_id

        Returns:
            Dictionary containing evaluation summary and detailed question reviews.
        """
        quiz = attempt.quiz
        questions = quiz.questions.prefetch_related("answers").all()
        total_questions = len(questions)

        correct_count = 0
        questions_review: list[dict[str, Any]] = []

        now = timezone.now()
        time_spent_seconds = max(0, int((now - attempt.started_at).total_seconds()))

        for q in questions:
            q_id_str = str(q.id)
            chosen_ans_id = submitted_answers.get(q_id_str)

            # Find answers for this question
            all_answers = list(q.answers.all())
            correct_ans = next((a for a in all_answers if a.is_correct), None)
            chosen_ans = next(
                (a for a in all_answers if str(a.id) == str(chosen_ans_id)),
                None,
            )

            is_q_correct = bool(chosen_ans and chosen_ans.is_correct)
            if is_q_correct:
                correct_count += 1

            questions_review.append(
                {
                    "question_id": q_id_str,
                    "text": q.text,
                    "difficulty": q.difficulty,
                    "source": q.source,
                    "explanation": q.explanation,
                    "chosen_answer_id": (str(chosen_ans.id) if chosen_ans else None),
                    "chosen_answer_text": (chosen_ans.text if chosen_ans else None),
                    "correct_answer_id": (str(correct_ans.id) if correct_ans else None),
                    "correct_answer_text": (correct_ans.text if correct_ans else None),
                    "is_correct": is_q_correct,
                }
            )

        # Compute score percentage
        score = round((correct_count / total_questions) * 100, 1) if total_questions > 0 else 0.0
        passed = score >= quiz.passing_score_percentage

        # Update attempt
        attempt.score = score
        attempt.total_questions = total_questions
        attempt.correct_answers_count = correct_count
        attempt.passed = passed
        attempt.answers_data = submitted_answers
        attempt.completed_at = now
        attempt.time_spent_seconds = time_spent_seconds
        attempt.save()

        logger.info(
            "Attempt %s completed: score=%s%% (%s/%s correct), passed=%s",
            attempt.id,
            score,
            correct_count,
            total_questions,
            passed,
        )

        return {
            "attempt_id": str(attempt.id),
            "quiz_id": str(quiz.id),
            "quiz_title": quiz.title,
            "quiz_type": quiz.type,
            "score": score,
            "passing_score": quiz.passing_score_percentage,
            "passed": passed,
            "total_questions": total_questions,
            "correct_answers_count": correct_count,
            "time_spent_seconds": time_spent_seconds,
            "started_at": attempt.started_at.isoformat(),
            "completed_at": attempt.completed_at.isoformat(),
            "questions_review": questions_review,
        }
