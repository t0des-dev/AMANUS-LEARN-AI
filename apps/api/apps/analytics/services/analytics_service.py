import logging
from datetime import timedelta
from typing import Any

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

from apps.courses.models import Course
from apps.learning.models import (
    LearningPath,
    LearningPathStatus,
    LearningProgress,
    StudySession,
)
from apps.quizzes.models import Quiz, QuizAttempt

logger = logging.getLogger(__name__)
User = get_user_model()


class AnalyticsService:
    """Core analytics engine computing student and instructor insights from real metrics."""

    def get_student_analytics(self, user: Any) -> dict[str, Any]:
        """Calculates exhaustive individual student analytics."""
        # 1. Total study duration
        total_study_time = (
            StudySession.objects.filter(user=user).aggregate(models.Sum("duration"))["duration__sum"]
            or 0
        )

        # 2. Courses metrics
        paths = list(
            LearningPath.objects.filter(user=user)
            .select_related("course")
            .order_by("-updated_at")
        )
        enrolled_count = len(paths)
        completed_courses = sum(1 for p in paths if p.status == LearningPathStatus.COMPLETED)
        in_progress_courses = sum(1 for p in paths if p.status == LearningPathStatus.IN_PROGRESS)

        overall_progress = (
            round(sum(p.progress for p in paths) / enrolled_count, 1) if enrolled_count > 0 else 0.0
        )

        # 3. Quiz & Assessment metrics
        attempts = list(
            QuizAttempt.objects.filter(user=user)
            .select_related("quiz")
            .order_by("-started_at")
        )
        quizzes_taken = len(attempts)
        passed_quizzes = sum(1 for a in attempts if a.passed)
        success_rate = (
            round((passed_quizzes / quizzes_taken) * 100, 1) if quizzes_taken > 0 else 0.0
        )
        avg_score = (
            round(sum(a.score for a in attempts) / quizzes_taken, 1) if quizzes_taken > 0 else None
        )

        # 4. Study time breakdown over last 7 days
        today = timezone.now().date()
        study_time_by_day = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            day_sessions = StudySession.objects.filter(
                user=user,
                started_at__date=day,
            ).aggregate(models.Sum("duration"))["duration__sum"] or 0
            study_time_by_day.append(
                {
                    "date": day.strftime("%Y-%m-%d"),
                    "day_label": day.strftime("%a"),
                    "duration_seconds": day_sessions,
                    "duration_minutes": round(day_sessions / 60, 1),
                }
            )

        # 5. Score progression history (last 10 attempts)
        scores_history = [
            {
                "id": str(a.id),
                "quiz_title": a.quiz.title,
                "score": round(a.score, 1),
                "passed": a.passed,
                "date": a.started_at.strftime("%Y-%m-%d") if a.started_at else "",
            }
            for a in attempts[:10]
        ]
        scores_history.reverse()

        # 6. Detailed per-course progress
        courses_progress = [
            {
                "course_id": str(p.course.id),
                "course_title": p.course.title,
                "status": p.status,
                "progress": p.progress,
                "updated_at": p.updated_at,
            }
            for p in paths
        ]

        return {
            "summary": {
                "total_study_time_seconds": total_study_time,
                "completed_courses_count": completed_courses,
                "in_progress_courses_count": in_progress_courses,
                "enrolled_courses_count": enrolled_count,
                "overall_progress": overall_progress,
                "total_quizzes_taken": quizzes_taken,
                "passed_quizzes_count": passed_quizzes,
                "success_rate": success_rate,
                "average_score": avg_score,
            },
            "study_time_by_day": study_time_by_day,
            "scores_history": scores_history,
            "courses_progress": courses_progress,
        }

    def get_course_analytics(self, course: Course) -> dict[str, Any]:
        """Calculates cohort performance analytics for an instructor."""
        # 1. Enrolled students and progress
        paths = list(LearningPath.objects.filter(course=course).select_related("user"))
        total_students = len(paths)
        completed_students = sum(1 for p in paths if p.status == LearningPathStatus.COMPLETED)
        completion_rate = (
            round((completed_students / total_students) * 100, 1) if total_students > 0 else 0.0
        )
        avg_progress = (
            round(sum(p.progress for p in paths) / total_students, 1) if total_students > 0 else 0.0
        )

        # 2. Total study duration on this course
        total_study_time = (
            StudySession.objects.filter(course=course).aggregate(models.Sum("duration"))["duration__sum"]
            or 0
        )

        # 3. Quiz performance across the course
        course_attempts = list(QuizAttempt.objects.filter(quiz__course=course))
        total_attempts = len(course_attempts)
        avg_quiz_score = (
            round(sum(a.score for a in course_attempts) / total_attempts, 1)
            if total_attempts > 0
            else None
        )
        pass_rate = (
            round((sum(1 for a in course_attempts if a.passed) / total_attempts) * 100, 1)
            if total_attempts > 0
            else 0.0
        )

        # 4. Problematic chapters (Chapitres problématiques)
        sections = list(course.sections.all().order_by("order", "created_at"))
        problematic_chapters = []

        for sec in sections:
            sec_progresses = list(LearningProgress.objects.filter(section=sec))
            completed_sec_count = sum(1 for p in sec_progresses if p.completion_percent >= 100.0)

            comp_rate = (
                round((completed_sec_count / total_students) * 100, 1) if total_students > 0 else 0.0
            )

            scores = [p.score for p in sec_progresses if p.score is not None]
            avg_sec_score = round(sum(scores) / len(scores), 1) if scores else None

            # Mark as problematic if low completion rate (< 50%) or low score (< 60%)
            is_problematic = (
                (comp_rate < 50.0 and total_students > 0)
                or (avg_sec_score is not None and avg_sec_score < 60.0)
            )

            chapter_data = {
                "section_id": str(sec.id),
                "section_title": sec.title,
                "order": sec.order,
                "completion_rate": comp_rate,
                "average_score": avg_sec_score,
                "students_completed": completed_sec_count,
                "total_students": total_students,
                "is_problematic": is_problematic,
            }
            if is_problematic or len(problematic_chapters) < 3:
                problematic_chapters.append(chapter_data)

        # Sort with highest concern first
        problematic_chapters.sort(
            key=lambda x: (x["average_score"] if x["average_score"] is not None else 100.0, x["completion_rate"])
        )

        return {
            "course_id": str(course.id),
            "course_title": course.title,
            "summary": {
                "total_students": total_students,
                "completed_students": completed_students,
                "completion_rate": completion_rate,
                "average_progress": avg_progress,
                "total_study_time_seconds": total_study_time,
                "average_score": avg_quiz_score,
                "pass_rate": pass_rate,
                "total_quiz_attempts": total_attempts,
            },
            "problematic_chapters": problematic_chapters,
        }

    def get_course_students_performance(self, course: Course) -> list[dict[str, Any]]:
        """Returns individual student progress for a course."""
        paths = list(
            LearningPath.objects.filter(course=course)
            .select_related("user")
            .order_by("-updated_at")
        )

        students_perf = []
        for p in paths:
            u = p.user
            # Total study time for this student on this course
            u_duration = (
                StudySession.objects.filter(user=u, course=course).aggregate(models.Sum("duration"))[
                    "duration__sum"
                ]
                or 0
            )

            # Quiz scores for this course
            u_attempts = list(QuizAttempt.objects.filter(user=u, quiz__course=course))
            u_score = (
                round(sum(a.score for a in u_attempts) / len(u_attempts), 1)
                if u_attempts
                else None
            )

            students_perf.append(
                {
                    "student_id": str(u.id),
                    "full_name": f"{u.first_name} {u.last_name}".strip() or u.email,
                    "email": u.email,
                    "status": p.status,
                    "progress": p.progress,
                    "total_study_time_seconds": u_duration,
                    "average_score": u_score,
                    "started_at": p.started_at,
                    "last_activity_at": p.updated_at,
                }
            )

        return students_perf

    def get_quiz_analytics(self, quiz: Quiz) -> dict[str, Any]:
        """Evaluates quiz performance and detects questions with high failure rates."""
        attempts = list(quiz.attempts.all().select_related("user"))
        total_attempts = len(attempts)
        distinct_students = len(set(a.user_id for a in attempts))

        avg_score = (
            round(sum(a.score for a in attempts) / total_attempts, 1) if total_attempts > 0 else 0.0
        )
        passed_count = sum(1 for a in attempts if a.passed)
        pass_rate = (
            round((passed_count / total_attempts) * 100, 1) if total_attempts > 0 else 0.0
        )

        # Compute question difficulties from answers_data
        questions = list(quiz.questions.all().order_by("order"))
        question_stats: dict[str, dict[str, Any]] = {
            str(q.id): {
                "question_id": str(q.id),
                "question_text": q.text,
                "order": q.order,
                "difficulty": q.difficulty,
                "total_answers": 0,
                "wrong_answers": 0,
                "error_rate_percent": 0.0,
            }
            for q in questions
        }

        for att in attempts:
            raw_answers = att.answers_data
            if isinstance(raw_answers, list):
                for ans_item in raw_answers:
                    q_id = str(ans_item.get("question_id"))
                    if q_id in question_stats:
                        question_stats[q_id]["total_answers"] += 1
                        if not ans_item.get("is_correct"):
                            question_stats[q_id]["wrong_answers"] += 1

        # Calculate error rates
        difficult_questions = []
        for q_id, stat in question_stats.items():
            tot = stat["total_answers"]
            wrg = stat["wrong_answers"]
            stat["error_rate_percent"] = round((wrg / tot) * 100, 1) if tot > 0 else 0.0
            difficult_questions.append(stat)

        # Sort by error rate descending (hardest questions first)
        difficult_questions.sort(key=lambda x: x["error_rate_percent"], reverse=True)

        return {
            "quiz_id": str(quiz.id),
            "quiz_title": quiz.title,
            "course_id": str(quiz.course.id) if quiz.course else None,
            "course_title": quiz.course.title if quiz.course else None,
            "total_attempts": total_attempts,
            "distinct_students_count": distinct_students,
            "average_score": avg_score,
            "pass_rate": pass_rate,
            "difficult_questions": difficult_questions,
        }
