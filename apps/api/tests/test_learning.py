import time
import uuid
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.courses.models import Course, CourseLevel, CourseSection, CourseStatus
from apps.learning.models import (
    LearningPath,
    LearningPathStatus,
    LearningProgress,
    StudySession,
)
from apps.learning.services.learning_engine import LearningEngine
from apps.organizations.models import Organization, OrganizationMember, RoleChoices
from apps.quizzes.models import Quiz, QuizAttempt, QuizType

User = get_user_model()


class LearningEngineUnitTests(APITestCase):
    """Unit tests for the LearningEngine service and calculations."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="learner@amanus.test",
            password="testpassword123",
            first_name="Jean",
            last_name="Dupont",
        )
        self.org = Organization.objects.create(name="Sorbonne IA", slug="sorbonne-ia")
        OrganizationMember.objects.create(
            organization=self.org,
            user=self.user,
            role=RoleChoices.STUDENT,
        )
        self.course = Course.objects.create(
            organization=self.org,
            created_by=self.user,
            title="Mathématiques pour l'Apprentissage Automatique",
            level=CourseLevel.BEGINNER,
            status=CourseStatus.PUBLISHED,
        )
        self.sec1 = CourseSection.objects.create(
            course=self.course,
            title="Algèbre Linéaire et Espaces Vectoriels",
            order=1,
        )
        self.sec2 = CourseSection.objects.create(
            course=self.course,
            title="Calcul Différentiel et Gradients",
            order=2,
        )
        self.engine = LearningEngine()

    def test_record_section_progress_and_recalculate_course_path(self):
        # Complete first section (50% of the course of 2 sections)
        prog1, path = self.engine.record_section_progress(
            user=self.user,
            section=self.sec1,
            completion_percent=100.0,
            last_position=450,
            score=85.0,
        )
        self.assertEqual(prog1.completion_percent, 100.0)
        self.assertEqual(prog1.last_position, 450)
        self.assertEqual(prog1.score, 85.0)
        self.assertEqual(path.status, LearningPathStatus.IN_PROGRESS)
        self.assertEqual(path.progress, 50.0)
        self.assertIsNotNone(path.started_at)
        self.assertIsNone(path.completed_at)

        # Complete second section (100% course completion)
        prog2, path = self.engine.record_section_progress(
            user=self.user,
            section=self.sec2,
            completion_percent=100.0,
            last_position=800,
            score=90.0,
        )
        self.assertEqual(path.status, LearningPathStatus.COMPLETED)
        self.assertEqual(path.progress, 100.0)
        self.assertIsNotNone(path.completed_at)

    def test_study_session_tracking_duration(self):
        session = self.engine.start_study_session(user=self.user, course=self.course)
        self.assertIsInstance(session, StudySession)
        self.assertEqual(session.duration, 0)
        self.assertIsNone(session.ended_at)

        # Simulate 120 seconds passed
        session.started_at = timezone.now() - timedelta(seconds=120)
        session.save(update_fields=["started_at"])

        finished = self.engine.finish_study_session(user=self.user, session_id=session.id)
        self.assertGreaterEqual(finished.duration, 119)
        self.assertIsNotNone(finished.ended_at)

    def test_dashboard_genuine_metrics_and_weak_topics(self):
        # 1. Study session duration
        StudySession.objects.create(
            user=self.user,
            course=self.course,
            started_at=timezone.now() - timedelta(minutes=30),
            ended_at=timezone.now(),
            duration=1800,
        )

        # 2. Section progress with low score (weak topic)
        self.engine.record_section_progress(
            user=self.user,
            section=self.sec1,
            completion_percent=100.0,
            score=45.0,  # Weak topic!
        )

        # 3. Quiz attempt with score
        quiz = Quiz.objects.create(
            organization=self.org,
            course=self.course,
            title="Quiz Algèbre",
            type=QuizType.TRAINING,
        )
        QuizAttempt.objects.create(
            user=self.user,
            quiz=quiz,
            score=50.0,
            passed=False,
        )

        dashboard = self.engine.get_student_dashboard(self.user)

        self.assertEqual(dashboard["stats"]["total_study_time_seconds"], 1800)
        self.assertEqual(dashboard["stats"]["completed_sections_count"], 1)
        self.assertIsNotNone(dashboard["stats"]["average_score"])
        # Weak topics detected
        self.assertGreaterEqual(len(dashboard["weak_topics"]), 1)
        weak_titles = [w["section_title"] for w in dashboard["weak_topics"]]
        self.assertTrue(any(self.sec1.title in t or "Quiz Algèbre" in t for t in weak_titles))

        # Recommended revision present
        self.assertGreaterEqual(len(dashboard["recommended_revision"]), 1)

        # Continue learning points to sec2 (the uncompleted one)
        self.assertIsNotNone(dashboard["continue_learning"])
        self.assertEqual(dashboard["continue_learning"]["section_id"], str(self.sec2.id))


class LearningAPITests(APITestCase):
    """Integration tests for all /learning endpoints."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="student@amanus.test",
            password="testpassword123",
            first_name="Sophie",
            last_name="Martin",
        )
        self.stranger = User.objects.create_user(
            email="stranger@amanus.test",
            password="testpassword123",
        )
        self.org = Organization.objects.create(name="Tech Institute", slug="tech-inst")
        OrganizationMember.objects.create(
            organization=self.org,
            user=self.user,
            role=RoleChoices.STUDENT,
        )

        self.course = Course.objects.create(
            organization=self.org,
            created_by=self.user,
            title="Systèmes Distribués et Consensus",
            level=CourseLevel.ADVANCED,
        )
        self.sec1 = CourseSection.objects.create(
            course=self.course,
            title="Le Problème des Généraux Byzantins",
            order=1,
        )
        self.sec2 = CourseSection.objects.create(
            course=self.course,
            title="Algorithme Raft et Paxos",
            order=2,
        )

        token = RefreshToken.for_user(self.user)
        self.auth_headers = {"HTTP_AUTHORIZATION": f"Bearer {token.access_token}"}

        stranger_token = RefreshToken.for_user(self.stranger)
        self.stranger_headers = {"HTTP_AUTHORIZATION": f"Bearer {stranger_token.access_token}"}

    def test_get_dashboard_authenticated(self):
        res = self.client.get("/api/v1/learning/dashboard/", **self.auth_headers)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("stats", res.data)
        self.assertIn("continue_learning", res.data)
        self.assertIn("weak_topics", res.data)
        self.assertIn("recent_activity", res.data)
        self.assertIn("recommended_revision", res.data)

    def test_get_dashboard_unauthenticated_returns_401(self):
        res = self.client.get("/api/v1/learning/dashboard/")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_complete_section_and_check_progress(self):
        url = f"/api/v1/learning/sections/{self.sec1.id}/complete/"
        payload = {
            "completion_percent": 100.0,
            "last_position": 1200,
            "score": 92.5,
        }
        res = self.client.post(url, payload, format="json", **self.auth_headers)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["progress"]["completion_percent"], 100.0)
        self.assertEqual(res.data["progress"]["last_position"], 1200)
        self.assertEqual(res.data["progress"]["score"], 92.5)
        # 1 section out of 2 completed = 50%
        self.assertEqual(res.data["course_progress"], 50.0)
        self.assertEqual(res.data["course_status"], LearningPathStatus.IN_PROGRESS)

    def test_get_course_learning_progress(self):
        # Complete section 1
        engine = LearningEngine()
        engine.record_section_progress(self.user, self.sec1, completion_percent=100.0, score=85.0)

        url = f"/api/v1/learning/courses/{self.course.id}/progress/"
        res = self.client.get(url, **self.auth_headers)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["course_id"], str(self.course.id))
        self.assertEqual(res.data["total_sections"], 2)
        self.assertEqual(res.data["completed_sections_count"], 1)
        self.assertEqual(res.data["remaining_sections_count"], 1)
        self.assertEqual(len(res.data["sections"]), 2)

    def test_course_progress_permission_denied_for_stranger(self):
        url = f"/api/v1/learning/courses/{self.course.id}/progress/"
        res = self.client.get(url, **self.stranger_headers)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_start_and_finish_study_session(self):
        # Start session
        start_url = "/api/v1/learning/sessions/start/"
        res_start = self.client.post(
            start_url,
            {"course_id": str(self.course.id)},
            format="json",
            **self.auth_headers,
        )
        self.assertEqual(res_start.status_code, status.HTTP_201_CREATED)
        session_id = res_start.data["id"]
        self.assertIsNotNone(session_id)
        self.assertEqual(res_start.data["duration"], 0)

        # Finish session
        finish_url = f"/api/v1/learning/sessions/{session_id}/finish/"
        res_finish = self.client.post(finish_url, {}, format="json", **self.auth_headers)
        self.assertEqual(res_finish.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(res_finish.data["ended_at"])
        self.assertGreaterEqual(res_finish.data["duration"], 0)

    def test_list_learning_courses(self):
        # Enroll user by recording some progress
        engine = LearningEngine()
        engine.record_section_progress(self.user, self.sec1, completion_percent=40.0)

        url = "/api/v1/learning/courses/"
        res = self.client.get(url, **self.auth_headers)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data.get("results", res.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["course"]["id"], str(self.course.id))
        self.assertEqual(results[0]["status"], LearningPathStatus.IN_PROGRESS)
