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
        is_completed: bool | None = None,
    ) -> tuple[LearningProgress, LearningPath]:
        """Marks or updates a section's learning progress and syncs parent course path.

        Distinguishes viewed/scrolled lessons from explicitly completed lessons.
        """
        course = section.course
        percent = max(0.0, min(100.0, float(completion_percent)))
        now = timezone.now()

        # Determine completion flag and percentage
        if is_completed is True or percent >= 100.0:
            flag_completed = True
            final_percent = 100.0
            comp_at = now
        elif is_completed is False:
            flag_completed = False
            final_percent = min(99.0, percent)
            comp_at = None
        else:
            flag_completed = percent >= 100.0
            final_percent = percent
            comp_at = now if flag_completed else None

        with transaction.atomic():
            # Ensure LearningPath exists
            learning_path, _ = LearningPath.objects.get_or_create(
                user=user,
                course=course,
                defaults={
                    "status": LearningPathStatus.IN_PROGRESS,
                    "started_at": now,
                },
            )

            # Get or create LearningProgress
            progress, created = LearningProgress.objects.get_or_create(
                user=user,
                section=section,
                defaults={
                    "course": course,
                    "completion_percent": final_percent,
                    "is_completed": flag_completed,
                    "completed_at": comp_at,
                    "last_viewed_at": now,
                    "last_position": max(0, int(last_position)),
                    "score": score,
                },
            )

            if not created:
                progress.last_viewed_at = now
                progress.last_position = max(0, int(last_position))

                if is_completed is True:
                    progress.is_completed = True
                    progress.completion_percent = 100.0
                    if not progress.completed_at:
                        progress.completed_at = now
                elif is_completed is False:
                    progress.is_completed = False
                    progress.completed_at = None
                    progress.completion_percent = max(progress.completion_percent, min(99.0, percent))
                else:
                    if percent >= 100.0:
                        progress.is_completed = True
                        progress.completion_percent = 100.0
                        if not progress.completed_at:
                            progress.completed_at = now
                    else:
                        progress.completion_percent = max(progress.completion_percent, percent)
                        if progress.completion_percent >= 100.0:
                            progress.is_completed = True
                            if not progress.completed_at:
                                progress.completed_at = now

                if score is not None:
                    progress.score = score

                progress.save(
                    update_fields=[
                        "completion_percent",
                        "is_completed",
                        "completed_at",
                        "last_viewed_at",
                        "last_position",
                        "score",
                        "updated_at",
                    ]
                )

            # Recalculate parent course progress
            learning_path.recalculate_progress()

            logger.info(
                "Recorded progress for user %s on section %s: %.1f%% (Completed: %s, Path: %.1f%%)",
                user.id,
                section.id,
                progress.completion_percent,
                progress.is_completed,
                learning_path.progress,
            )
            return progress, learning_path

    def start_study_session(self, user: Any, course: Course) -> StudySession:
        """Starts a new study session for tracking active study duration."""
        with transaction.atomic():
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
            is_comp = (p.is_completed or comp_pct >= 100.0) if p else False

            if is_comp:
                completed_count += 1

            is_weak = sc is not None and sc < 60.0
            sec_info = {
                "id": str(sec.id),
                "title": sec.title,
                "order": sec.order,
                "completion_percent": comp_pct,
                "last_position": pos,
                "score": sc,
                "is_completed": is_comp,
                "completed_at": p.completed_at.isoformat() if (p and p.completed_at) else None,
                "last_viewed_at": p.last_viewed_at.isoformat() if (p and p.last_viewed_at) else None,
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
            LearningPath.objects.filter(user=user, course__isnull=False)
            .select_related("course")
            .order_by("-updated_at")
        )
        total_enrolled = len(paths)
        in_progress_count = sum(1 for p in paths if p.status == LearningPathStatus.IN_PROGRESS)
        completed_count = sum(1 for p in paths if p.status == LearningPathStatus.COMPLETED)

        # 3. Average score calculation across QuizAttempts and LearningProgress
        quiz_avg = QuizAttempt.objects.filter(user=user, completed_at__isnull=False).aggregate(
            models.Avg("score")
        )["score__avg"]
        progress_avg = LearningProgress.objects.filter(user=user, score__isnull=False).aggregate(
            models.Avg("score")
        )["score__avg"]

        valid_scores = [s for s in (quiz_avg, progress_avg) if s is not None]
        overall_average_score = (
            round(sum(valid_scores) / len(valid_scores), 1) if valid_scores else None
        )

        # 4. Total completed sections count
        completed_sections_count = LearningProgress.objects.filter(
            user=user, is_completed=True
        ).count()
        if completed_sections_count == 0:
            completed_sections_count = LearningProgress.objects.filter(
                user=user, completion_percent__gte=100.0
            ).count()

        # 5. Continue Learning (Next / Most recent active chapter)
        continue_learning = self._find_continue_learning(user, paths)

        # 6. Weak Topics (Chapters/Quizzes with score < 60%)
        weak_topics = self._find_weak_topics(user)

        # 7. Recent Activity (Last 5 study sessions)
        recent_sessions = list(
            StudySession.objects.filter(user=user, course__isnull=False)
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

        # 8. Recent Quiz Results (Last 5 completed attempts)
        recent_quizzes = list(
            QuizAttempt.objects.filter(user=user, completed_at__isnull=False, quiz__isnull=False)
            .select_related("quiz", "quiz__course")
            .order_by("-completed_at")[:5]
        )
        recent_quiz_results = [
            {
                "id": str(att.id),
                "quiz_id": str(att.quiz.id),
                "quiz_title": att.quiz.title,
                "course_id": str(att.quiz.course.id) if att.quiz.course else None,
                "course_title": att.quiz.course.title if att.quiz.course else None,
                "score": att.score,
                "passed": att.passed,
                "total_questions": att.total_questions,
                "correct_answers_count": att.correct_answers_count,
                "completed_at": att.completed_at,
            }
            for att in recent_quizzes
        ]

        # 9. Recommended Revision
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
            "recent_quiz_results": recent_quiz_results,
            "recommended_revision": recommended_revision,
        }

    def _find_continue_learning(
        self, user: Any, paths: list[LearningPath]
    ) -> dict[str, Any] | None:
        """Determines the exact course and chapter the student should continue.

        Avoids looping endlessly on completed courses and properly handles deleted content.
        """
        valid_paths = [p for p in paths if p.course_id]
        if not valid_paths:
            return None

        # Check in-progress paths first, then not-started paths
        active_paths = [p for p in valid_paths if p.status == LearningPathStatus.IN_PROGRESS]
        candidate_paths = active_paths if active_paths else [
            p for p in valid_paths if p.status != LearningPathStatus.COMPLETED
        ]

        if not candidate_paths:
            # All courses are completed! Do not return an infinite loop of finished sections
            return None

        for path in candidate_paths:
            course = path.course
            if not course:
                continue

            all_sections = list(course.sections.all().order_by("order", "created_at"))
            if not all_sections:
                continue

            # Completed section IDs for this user & course
            completed_ids = set(
                LearningProgress.objects.filter(
                    user=user,
                    course=course,
                    is_completed=True,
                ).values_list("section_id", flat=True)
            )
            # Fallback to completion_percent >= 100 for legacy records
            if not completed_ids:
                completed_ids = set(
                    LearningProgress.objects.filter(
                        user=user,
                        course=course,
                        completion_percent__gte=100.0,
                    ).values_list("section_id", flat=True)
                )

            # Find first non-completed section
            next_section = next((s for s in all_sections if s.id not in completed_ids), None)

            if next_section:
                lp = LearningProgress.objects.filter(user=user, section=next_section).first()
                last_pos = lp.last_position if lp else 0
                comp_pct = lp.completion_percent if lp else 0.0

                return {
                    "course_id": str(course.id),
                    "course_title": course.title,
                    "section_id": str(next_section.id),
                    "section_title": next_section.title,
                    "section_order": next_section.order,
                    "progress": path.progress,
                    "section_completion_percent": comp_pct,
                    "last_position": last_pos,
                    "is_completed": False,
                }
            else:
                # All sections in this path are finished; ensure path is marked COMPLETED
                path.recalculate_progress()

        return None

    def _find_weak_topics(self, user: Any) -> list[dict[str, Any]]:
        """Identifies chapters and quizzes where learner struggled (score < 60%)."""
        weak_list = []
        seen_keys = set()

        # 1. From LearningProgress records with score < 60
        progress_weak = (
            LearningProgress.objects.filter(
                user=user,
                score__lt=60.0,
                score__isnull=False,
                course__isnull=False,
                section__isnull=False,
            )
            .select_related("course", "section")
            .order_by("score")
        )
        for p in progress_weak:
            key = f"sec_{p.section_id}"
            if key not in seen_keys:
                seen_keys.add(key)
                weak_list.append(
                    {
                        "section_id": str(p.section.id),
                        "section_title": p.section.title,
                        "course_id": str(p.course.id),
                        "course_title": p.course.title,
                        "score": round(p.score, 1),
                        "source": "section_score",
                        "learning_objective": f"Maîtrise du chapitre : {p.section.title}",
                    }
                )

        # 2. From QuizAttempts with score < 60%
        failed_attempts = (
            QuizAttempt.objects.filter(user=user, score__lt=60.0, quiz__isnull=False)
            .select_related("quiz", "quiz__course")
            .order_by("score")
        )
        for att in failed_attempts:
            key = f"quiz_{att.quiz.id}"
            if key not in seen_keys:
                seen_keys.add(key)
                weak_list.append(
                    {
                        "section_id": None,
                        "section_title": att.quiz.title,
                        "quiz_id": str(att.quiz.id),
                        "course_id": str(att.quiz.course.id) if att.quiz.course else None,
                        "course_title": att.quiz.course.title if att.quiz.course else None,
                        "score": round(att.score, 1),
                        "source": "quiz_attempt",
                        "learning_objective": f"Évaluation : {att.quiz.title}",
                    }
                )

        return weak_list[:6]

    def _build_recommended_revisions(
        self,
        user: Any,
        weak_topics: list[dict[str, Any]],
        paths: list[LearningPath],
    ) -> list[dict[str, Any]]:
        """Generates targeted, explainable revision recommendations."""
        recs = []

        # High priority: weak topics
        for item in weak_topics[:3]:
            recs.append(
                {
                    "type": "weak_topic",
                    "title": f"Révision prioritaire : {item['section_title']}",
                    "course_id": item.get("course_id"),
                    "course_title": item.get("course_title"),
                    "section_id": item.get("section_id"),
                    "quiz_id": item.get("quiz_id"),
                    "reason": f"Score inférieur au seuil de validation ({item['score']}%)",
                }
            )

        # Medium priority: in-progress courses awaiting completion
        for path in paths:
            if len(recs) >= 5:
                break
            if (
                path.course
                and path.status == LearningPathStatus.IN_PROGRESS
                and path.progress < 100.0
            ):
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

        # Low priority: enrolled courses not yet started
        for path in paths:
            if len(recs) >= 5:
                break
            if (
                path.course
                and path.status == LearningPathStatus.NOT_STARTED
                and path.progress == 0.0
            ):
                recs.append(
                    {
                        "type": "not_started",
                        "title": f"Démarrer : {path.course.title}",
                        "course_id": str(path.course.id),
                        "course_title": path.course.title,
                        "section_id": None,
                        "reason": "Nouveau cours inscrit au programme",
                    }
                )

        return recs
