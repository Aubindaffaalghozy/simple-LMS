from django.contrib.auth.models import User
from django.test import RequestFactory, SimpleTestCase, TestCase

from courses.models import Category, Course, Enrollment

from .cache_utils import build_course_cache_key
from .views import dashboard_summary


class CacheUtilsTests(SimpleTestCase):
    def test_build_course_cache_key_uses_prefix_and_identifier(self):
        key = build_course_cache_key("list", "page:1")

        self.assertEqual(key, "simple_lms:course:list:page:1")


class DashboardSummaryTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.instructor = User.objects.create_user(username="instructor", password="123456")
        self.student = User.objects.create_user(username="student", password="123456")
        self.category = Category.objects.create(name="Programming")
        self.course = Course.objects.create(
            name="Django Basics",
            description="Intro to Django",
            category=self.category,
            instructor=self.instructor,
            is_published=True,
        )
        Enrollment.objects.create(course=self.course, student=self.student, role="student", is_active=True)

    def test_dashboard_summary_returns_expected_metrics(self):
        request = self.factory.get("/api/dashboard/summary")
        response = dashboard_summary(request)

        self.assertEqual(response["total_courses"], 1)
        self.assertEqual(response["published_courses"], 1)
        self.assertEqual(response["active_enrollments"], 1)
        self.assertEqual(response["active_students"], 1)
