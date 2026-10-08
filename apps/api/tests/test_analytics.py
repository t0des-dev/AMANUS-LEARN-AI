from datetime import timedelta
import uuid

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.analytics.services.analytics_service import AnalyticsService
from apps.courses.models import Course, CourseLevel, CourseSection, CourseStatus
from apps.learning.models import (
    LearningPath,
    LearningPathStatus,
    LearningProgress,
    StudySession,
)
from apps.organizations.models import Organization, OrganizationMember, RoleChoices
from apps.quizzes.models import (
    DifficultyLevel,
    Quiz,
    QuizAttempt,
    QuizQuestion,
    QuizType,
)

User = get_user_model()


class AnalyticsAggregationUnitTests(APITestCase):
    """Unit tests for calculating real student and instructor analytics."""

    def setUp(self):
        self.teacher = User.objects.create_user(
            email="prof@univ.test",
            password="testpassword123",
            first_name="Prof",
            last_name="Turing",
        )
        self.student1 = User.objects.create_user(
            email="student1@univ.test",
            password="testpassword123",
            first_name="Alice",
            last_name="Lovelace",
        )
        self.student2 = User.objects.create_user(
            email="student2@univ.test",
            password="testpassword123",
            first_name="Bob",
            last_name="Babbage",
        )

        self.org = Organization.objects.create(name="Univ Informatique", slug="univ-info")
        OrganizationMember.objects.create(organization=self.org, user=self.teacher, role=RoleChoices.TEACHER)
        OrganizationMember.objects.create(organization=self.org, user=self.student1, role=RoleChoices.STUDENT)
        OrganizationMember.objects.create(organization=self.org, user=self.student2, role=RoleChoices.STUDENT)

        self.course = Course.objects.create(
            organization=self.org,
            created_by=self.teacher,
            title="Théorie de la Calculabilité",
            level=CourseLevel.ADVANCED,
            status=CourseStatus.PUBLISHED,
        )
        self.sec1 = CourseSection.objects.create(
            course=self.course,
            title="Machines de Turing",
            order=1,
        )
        self.sec2 = CourseSection.objects.create(
            course=self.course,
            title="Problème de l'Arrêt et Indécidabilité",
            order=2,
        )

        self.quiz = Quiz.objects.create(
            organization=self.org,
            course=self.course,
            title="Quiz Calculabilité",
            type=QuizType.EXAM,
            passing_score_percentage=70.0,
        )
        self.q1 = QuizQuestion.objects.create(
            quiz=self.quiz,
            text="Une machine de Turing universelle peut-elle simuler n'importe quelle machine ?",
            order=1,
        )
        self.q2 = QuizQuestion.objects.create(
            quiz=self.quiz,
            text="Le problème de l'arrêt est-il décidable sur un ensemble dénombrable ?",
            order=2,
        )

        self.service = AnalyticsService()

    def test_student_analytics_calculation(self):
        # 1. Add study sessions
        StudySession.objects.create(
            user=self.student1,
            course=self.course,
            started_at=timezone.now() - timedelta(minutes=45),
            ended_at=timezone.now(),
            duration=2700,
        )
        # 2. Add course learning path
        LearningPath.objects.create(
            user=self.student1,
            course=self.course,
            status=LearningPathStatus.IN_PROGRESS,
            progress=50.0,
        )
        # 3. Add quiz attempts
        QuizAttempt.objects.create(
            user=self.student1,
            quiz=self.quiz,
            score=80.0,
            passed=True,
        )
        QuizAttempt.objects.create(
            user=self.student1,
            quiz=self.quiz,
            score=60.0,
            passed=False,
        )

        res = self.service.get_student_analytics(self.student1)

        self.assertEqual(res["summary"]["total_study_time_seconds"], 2700)
        self.assertEqual(res["summary"]["enrolled_courses_count"], 1)
        self.assertEqual(res["summary"]["in_progress_courses_count"], 1)
        self.assertEqual(res["summary"]["total_quizzes_taken"], 2)
        self.assertEqual(res["summary"]["passed_quizzes_count"], 1)
        self.assertEqual(res["summary"]["success_rate"], 50.0)
        self.assertEqual(res["summary"]["average_score"], 70.0)
        self.assertEqual(len(res["study_time_by_day"]), 7)
        self.assertEqual(len(res["scores_history"]), 2)

    def test_course_analytics_and_problematic_chapters(self):
        # Student 1: completed sec1, struggling on sec2
        LearningPath.objects.create(
            user=self.student1,
            course=self.course,
            status=LearningPathStatus.IN_PROGRESS,
            progress=50.0,
        )
        LearningProgress.objects.create(
            user=self.student1,
            course=self.course,
            section=self.sec1,
            completion_percent=100.0,
            score=95.0,
        )
        LearningProgress.objects.create(
            user=self.student1,
            course=self.course,
            section=self.sec2,
            completion_percent=30.0,
            score=40.0,  # low score!
        )

        # Student 2: also struggling on sec2
        LearningPath.objects.create(
            user=self.student2,
            course=self.course,
            status=LearningPathStatus.IN_PROGRESS,
            progress=50.0,
        )
        LearningProgress.objects.create(
            user=self.student2,
            course=self.course,
            section=self.sec1,
            completion_percent=100.0,
            score=90.0,
        )
        LearningProgress.objects.create(
            user=self.student2,
            course=self.course,
            section=self.sec2,
            completion_percent=20.0,
            score=50.0,
        )

        res = self.service.get_course_analytics(self.course)

        self.assertEqual(res["summary"]["total_students"], 2)
        self.assertEqual(res["summary"]["average_progress"], 50.0)
        # Check problematic chapters: sec2 should be flagged as problematic
        problematic = res["problematic_chapters"]
        self.assertGreaterEqual(len(problematic), 1)
        sec2_item = next(p for p in problematic if p["section_id"] == str(self.sec2.id))
        self.assertTrue(sec2_item["is_problematic"])
        self.assertEqual(sec2_item["average_score"], 45.0)

    def test_quiz_difficult_questions_analytics(self):
        # Attempt 1: answered q1 correctly, q2 wrong
        QuizAttempt.objects.create(
            user=self.student1,
            quiz=self.quiz,
            score=50.0,
            passed=False,
            answers_data=[
                {"question_id": str(self.q1.id), "is_correct": True},
                {"question_id": str(self.q2.id), "is_correct": False},
            ],
        )
        # Attempt 2: answered q1 correctly, q2 wrong again
        QuizAttempt.objects.create(
            user=self.student2,
            quiz=self.quiz,
            score=50.0,
            passed=False,
            answers_data=[
                {"question_id": str(self.q1.id), "is_correct": True},
                {"question_id": str(self.q2.id), "is_correct": False},
            ],
        )

        res = self.service.get_quiz_analytics(self.quiz)

        self.assertEqual(res["total_attempts"], 2)
        self.assertEqual(res["distinct_students_count"], 2)
        self.assertEqual(res["average_score"], 50.0)
        self.assertEqual(res["pass_rate"], 0.0)

        # q2 should have 100% error rate and be ranked first
        diff_questions = res["difficult_questions"]
        self.assertEqual(len(diff_questions), 2)
        self.assertEqual(diff_questions[0]["question_id"], str(self.q2.id))
        self.assertEqual(diff_questions[0]["error_rate_percent"], 100.0)
        self.assertEqual(diff_questions[1]["question_id"], str(self.q1.id))
        self.assertEqual(diff_questions[1]["error_rate_percent"], 0.0)


class AnalyticsAPIPermissionsTests(APITestCase):
    """Integration tests verifying multi-tenant isolation and role-based permissions."""

    def setUp(self):
        # Org 1
        self.org1 = Organization.objects.create(name="Polytechnique", slug="polytech")
        self.teacher1 = User.objects.create_user(email="teacher1@poly.test", password="testpassword123")
        self.student1 = User.objects.create_user(email="student1@poly.test", password="testpassword123")
        OrganizationMember.objects.create(organization=self.org1, user=self.teacher1, role=RoleChoices.TEACHER)
        OrganizationMember.objects.create(organization=self.org1, user=self.student1, role=RoleChoices.STUDENT)

        # Org 2 (separate tenant)
        self.org2 = Organization.objects.create(name="Centrale", slug="centrale")
        self.teacher2 = User.objects.create_user(email="teacher2@centrale.test", password="testpassword123")
        OrganizationMember.objects.create(organization=self.org2, user=self.teacher2, role=RoleChoices.TEACHER)

        self.course1 = Course.objects.create(
            organization=self.org1,
            created_by=self.teacher1,
            title="Optimisation Convexe",
        )
        self.quiz1 = Quiz.objects.create(
            organization=self.org1,
            course=self.course1,
            title="Quiz Optimisation",
        )

        # Tokens
        t1_tok = RefreshToken.for_user(self.teacher1)
        self.teacher1_headers = {"HTTP_AUTHORIZATION": f"Bearer {t1_tok.access_token}"}

        s1_tok = RefreshToken.for_user(self.student1)
        self.student1_headers = {"HTTP_AUTHORIZATION": f"Bearer {s1_tok.access_token}"}

        t2_tok = RefreshToken.for_user(self.teacher2)
        self.teacher2_headers = {"HTTP_AUTHORIZATION": f"Bearer {t2_tok.access_token}"}

    def test_student_analytics_endpoint(self):
        res = self.client.get("/api/v1/analytics/student/", **self.student1_headers)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("summary", res.data)
        self.assertIn("study_time_by_day", res.data)

    def test_course_analytics_access_for_authorized_teacher(self):
        url = f"/api/v1/analytics/courses/{self.course1.id}/"
        res = self.client.get(url, **self.teacher1_headers)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["course_id"], str(self.course1.id))

    def test_course_analytics_forbidden_for_student(self):
        url = f"/api/v1/analytics/courses/{self.course1.id}/"
        res = self.client.get(url, **self.student1_headers)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_course_analytics_tenant_isolation_forbidden_for_other_org_teacher(self):
        # Teacher from org2 cannot access course of org1
        url = f"/api/v1/analytics/courses/{self.course1.id}/"
        res = self.client.get(url, **self.teacher2_headers)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_course_students_performance_endpoint(self):
        url = f"/api/v1/analytics/courses/{self.course1.id}/students/"
        # Authorized teacher
        res = self.client.get(url, **self.teacher1_headers)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIsInstance(res.data, list)

        # Student forbidden
        res_stud = self.client.get(url, **self.student1_headers)
        self.assertEqual(res_stud.status_code, status.HTTP_403_FORBIDDEN)

    def test_quiz_analytics_endpoint(self):
        url = f"/api/v1/analytics/quizzes/{self.quiz1.id}/"
        # Authorized teacher
        res = self.client.get(url, **self.teacher1_headers)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("difficult_questions", res.data)

        # Student forbidden
        res_stud = self.client.get(url, **self.student1_headers)
        self.assertEqual(res_stud.status_code, status.HTTP_403_FORBIDDEN)

        # Other tenant teacher forbidden
        res_t2 = self.client.get(url, **self.teacher2_headers)
        self.assertEqual(res_t2.status_code, status.HTTP_403_FORBIDDEN)
