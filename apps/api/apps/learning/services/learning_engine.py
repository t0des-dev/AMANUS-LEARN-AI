import logging
from typing import Any
from uuid import UUID

from django.contrib.auth import get_user_model
from django.db import models, transaction
from django.utils import timezone

from apps.courses.models import Course, CourseSection
from apps.learning.models import (
    LearningPath,
    LearningPathStatus,
    LearningProgress,
    StudySession,
)
from apps.quizzes.models import QuizAttempt

logger = logging.getLogger(__name__)
User = get_user_model()


class LearningEngine:
    """Core pedagogical learning engine.

    Computes genuine learner analytics, tracks study sessions,
    evaluates granular chapter progress and identifies weak topics for remediation.
    """

    def record_section_progress(
        self,
        user: Any,
        section: CourseSection,
        completion_percent: float = 100.0,
        last_position: int = 0,
        score: float | None = None,
    ) -> tuple[LearningProgress, LearningPath]:
        """Marks or updates a section's learning progress and syncs parent course path."""
        course = section.course
        percent = max(0.0, min(100.0, float(completion_percent)))

        with transaction.atomic():
            # Ensure LearningPath exists
            learning_path, _ = LearningPath.objects.get_or_create(
                user=user,
                course=course,
                defaults={
                    "status": LearningPathStatus.IN_PROGRESS,
                    "started_at": timezone.now(),
                },
            )

            # Get or create LearningProgress
            progress, created = LearningProgress.objects.get_or_create(
                user=user,
                section=section,
                defaults={
                    "course": course,
                    "completion_percent": percent,
                    "last_position": last_position,
                    "score": score,
                },
            )

            if not created:
                # Update with latest / max values
                progress.completion_percent = max(progress.completion_percent, percent)
                progress.last_position = last_position
                if score is not None:
                    progress.score = score
                progress.save(
                    update_fields=["completion_percent", "last_position", "score", "updated_at"]
                )

            # Recalculate parent course progress
            learning_path.recalculate_progress()

            logger.info(
                "Recorded progress for user %s on section %s: %.1f%% (Path: %.1f%%)",
                user.id,
                section.id,
                progress.completion_percent,
                learning_path.progress,
            )
            return progress, learning_path

    def start_study_session(self, user: Any, course: Course) -> StudySession:
        """Starts a new study session for tracking active study duration."""
        with transaction.atomic():
            # Ensure learning path is marked as in progress
            path, _ = LearningPath.objects.get_or_create(
                user=user,
                course=course,
                defaults={
                    "status": LearningPathStatus.IN_PROGRESS,
                    "started_at": timezone.now(),
                },
            )
            if path.status == LearningPathStatus.NOT_STARTED:
                path.status = LearningPathStatus.IN_PROGRESS
                path.started_at = timezone.now()
                path.save(update_fields=["status", "started_at", "updated_at"])

            session = StudySession.objects.create(
                user=user,
                course=course,
                started_at=timezone.now(),
            )
            logger.info(
                "Started study session %s for user %s on course %s", session.id, user.id, course.id
            )
            return session

    def finish_study_session(self, user: Any, session_id: UUID | str) -> StudySession:
        """Closes an active study session and computes final duration in seconds."""
        session = StudySession.objects.get(id=session_id, user=user)
        duration = session.finish()
        logger.info("Finished study session %s (duration: %ds)", session.id, duration)
        return session

    def get_course_progress(self, user: Any, course: Course) -> dict[str, Any]:
        """Returns exhaustive progress breakdown for a single course."""
        path, _ = LearningPath.objects.get_or_create(
            user=user,
            course=course,
            defaults={"status": LearningPathStatus.NOT_STARTED, "progress": 0.0},
        )

        all_sections = list(course.sections.all().order_by("order", "created_at"))
        total_sections = len(all_sections)

        progresses = {
            p.section_id: p for p in LearningProgress.objects.filter(user=user, course=course)
        }

        sections_data = []
        completed_count = 0
        weak_sections = []

        for sec in all_sections:
            p = progresses.get(sec.id)
            comp_pct = p.completion_percent if p else 0.0
            pos = p.last_position if p else 0
            sc = p.score if p else None

            if comp_pct >= 100.0:
                completed_count += 1

            is_weak = sc is not None and sc < 60.0
            sec_info = {
                "id": str(sec.id),
                "title": sec.title,
                "order": sec.order,
                "completion_percent": comp_pct,
                "last_position": pos,
                "score": sc,
                "is_completed": comp_pct >= 100.0,
                "is_weak": is_weak,
            }
            sections_data.append(sec_info)
            if is_weak:
                weak_sections.append(sec_info)

        return {
            "course_id": str(course.id),
            "course_title": course.title,
            "status": path.status,
            "progress": path.progress,
            "started_at": path.started_at,
            "completed_at": path.completed_at,
            "total_sections": total_sections,
            "completed_sections_count": completed_count,
            "remaining_sections_count": max(0, total_sections - completed_count),
            "sections": sections_data,
            "weak_sections": weak_sections,
        }

    def get_student_dashboard(self, user: Any) -> dict[str, Any]:
        """Aggregates authentic dashboard metrics calculated from actual user activity."""
        # 1. Total study time in seconds
        total_duration = (
            StudySession.objects.filter(user=user).aggregate(models.Sum("duration"))[
                "duration__sum"
            ]
            or 0
        )

        # 2. Enrolled / In-progress / Completed paths
        paths = list(
            LearningPath.objects.filter(user=user).select_related("course").order_by("-updated_at")
        )
        total_enrolled = len(paths)
        in_progress_count = sum(1 for p in paths if p.status == LearningPathStatus.IN_PROGRESS)
        completed_count = sum(1 for p in paths if p.status == LearningPathStatus.COMPLETED)

        # 3. Average score calculation across QuizAttempts and LearningProgress
        quiz_avg = QuizAttempt.objects.filter(user=user).aggregate(models.Avg("score"))[
            "score__avg"
        ]
        progress_avg = LearningProgress.objects.filter(user=user, score__isnull=False).aggregate(
            models.Avg("score")
        )["score__avg"]

        valid_scores = [s for s in (quiz_avg, progress_avg) if s is not None]
        overall_average_score = (
            round(sum(valid_scores) / len(valid_scores), 1) if valid_scores else None
        )

        # 4. Total completed sections count
        completed_sections_count = LearningProgress.objects.filter(
            user=user, completion_percent__gte=100.0
        ).count()

        # 5. Continue Learning (Next / Most recent active chapter)
        continue_learning = self._find_continue_learning(user, paths)

        # 6. Weak Topics (Chapters with score < 60%)
        weak_topics = self._find_weak_topics(user)

        # 7. Recent Activity (Last 5 study sessions)
        recent_sessions = list(
            StudySession.objects.filter(user=user)
            .select_related("course")
            .order_by("-started_at")[:5]
        )
        recent_activity = [
            {
                "id": str(s.id),
                "course_id": str(s.course.id),
                "course_title": s.course.title,
                "started_at": s.started_at,
                "ended_at": s.ended_at,
                "duration": s.duration,
            }
            for s in recent_sessions
        ]

        # 8. Recommended Revision
        recommended_revision = self._build_recommended_revisions(user, weak_topics, paths)

        return {
            "stats": {
                "total_study_time_seconds": total_duration,
                "courses_in_progress": in_progress_count,
                "courses_completed": completed_count,
                "total_enrolled_courses": total_enrolled,
                "completed_sections_count": completed_sections_count,
                "average_score": overall_average_score,
            },
            "continue_learning": continue_learning,
            "weak_topics": weak_topics,
            "recent_activity": recent_activity,
            "recommended_revision": recommended_revision,
        }

    def _find_continue_learning(
        self, user: Any, paths: list[LearningPath]
    ) -> dict[str, Any] | None:
        """Determines the exact course and chapter the student should continue."""
        # Check active paths first
        active_paths = [p for p in paths if p.status == LearningPathStatus.IN_PROGRESS] or paths
        if not active_paths:
            return None

        target_path = active_paths[0]
        course = target_path.course
        all_sections = list(course.sections.all().order_by("order", "created_at"))
        if not all_sections:
            return {
                "course_id": str(course.id),
                "course_title": course.title,
                "section_id": None,
                "section_title": None,
                "progress": target_path.progress,
                "last_position": 0,
            }

        # Check section progresses
        completed_ids = set(
            LearningProgress.objects.filter(
                user=user, course=course, completion_percent__gte=100.0
            ).values_list("section_id", flat=True)
        )

        # Find first non-completed section
        next_section = next((s for s in all_sections if s.id not in completed_ids), None)
        if not next_section:
            next_section = all_sections[-1]

        # Fetch last known position
        lp = LearningProgress.objects.filter(user=user, section=next_section).first()
        last_pos = lp.last_position if lp else 0
        comp_pct = lp.completion_percent if lp else 0.0

        return {
            "course_id": str(course.id),
            "course_title": course.title,
            "section_id": str(next_section.id),
            "section_title": next_section.title,
            "section_order": next_section.order,
            "progress": target_path.progress,
            "section_completion_percent": comp_pct,
            "last_position": last_pos,
        }

    def _find_weak_topics(self, user: Any) -> list[dict[str, Any]]:
        """Identifies chapters where learner struggled (score < 60%)."""
        weak_list = []
        seen_sections = set()

        # 1. From LearningProgress records with score < 60
        progress_weak = (
            LearningProgress.objects.filter(user=user, score__lt=60.0, score__isnull=False)
            .select_related("course", "section")
            .order_by("score")
        )
        for p in progress_weak:
            if p.section_id not in seen_sections:
                seen_sections.add(p.section_id)
                weak_list.append(
                    {
                        "section_id": str(p.section.id),
                        "section_title": p.section.title,
                        "course_id": str(p.course.id),
                        "course_title": p.course.title,
                        "score": round(p.score, 1),
                        "source": "section_score",
                    }
                )

        # 2. From QuizAttempts with score < 60% linked to courses
        failed_attempts = (
            QuizAttempt.objects.filter(user=user, score__lt=60.0)
            .select_related("quiz", "quiz__course")
            .order_by("score")
        )
        for att in failed_attempts:
            if att.quiz.course and att.quiz.course.id not in seen_sections:
                seen_sections.add(att.quiz.course.id)
                weak_list.append(
                    {
                        "section_id": None,
                        "section_title": att.quiz.title,
                        "course_id": str(att.quiz.course.id),
                        "course_title": att.quiz.course.title,
                        "score": round(att.score, 1),
                        "source": "quiz_attempt",
                    }
                )

        return weak_list[:6]

    def _build_recommended_revisions(
        self,
        user: Any,
        weak_topics: list[dict[str, Any]],
        paths: list[LearningPath],
    ) -> list[dict[str, Any]]:
        """Generates targeted revision recommendations."""
        recs = []

        # High priority: weak topics
        for item in weak_topics[:3]:
            recs.append(
                {
                    "type": "weak_topic",
                    "title": f"Révision prioritaire : {item['section_title']}",
                    "course_id": item["course_id"],
                    "course_title": item["course_title"],
                    "section_id": item.get("section_id"),
                    "reason": f"Score inférieur au seuil de maîtrise ({item['score']}%)",
                }
            )

        # Medium priority: in-progress courses awaiting completion
        for path in paths:
            if len(recs) >= 5:
                break
            if path.status == LearningPathStatus.IN_PROGRESS and path.progress < 100.0:
                recs.append(
                    {
                        "type": "in_progress",
                        "title": f"Continuer : {path.course.title}",
                        "course_id": str(path.course.id),
                        "course_title": path.course.title,
                        "section_id": None,
                        "reason": f"Cours complété à {path.progress:.0f}%",
                    }
                )

        return recs
