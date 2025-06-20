from django.test import TestCase, Client
from django.urls import reverse
from ..models import MyUser, Course, Enrollment
from datetime import date

class EnrollmentReportTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.student1 = MyUser.objects.create(
            fullName="Alice Wonderland",name="Alice", email="a@example.com", password="pass", role="student")
        self.student2 = MyUser.objects.create(fullName="Bob Boulder" ,name="Bob", email="b@example.com", password="pass", role="student")
        self.instructor = MyUser.objects.create(name="Dr. Josh", email="drsmith@example.com", password="teach123",
                                                role="instructor")

        self.course1 = Course.objects.create(
            code="CS101",
            title="Intro to Computer Science",
            instructor=self.instructor,
            seat_limit=30
        )

        self.course2 = Course.objects.create(
            code="CS102",
            title="Data Structures",
            instructor=self.instructor,
            seat_limit=30
        )

        Enrollment.objects.create(student=self.student1, course=self.course1, date_enrolled=date(2024, 1, 10))
        Enrollment.objects.create(student=self.student1, course=self.course2, date_enrolled=date(2024, 2, 5))
        Enrollment.objects.create(student=self.student2, course=self.course1, date_enrolled=date(2024, 2, 15))
        # log in administrator
        session = self.client.session
        session['name'] = 'Josh'
        session['role'] = 'administrator'
        session.save()

    def test_enrollment_report_get(self):
        response = self.client.get(reverse('enrollment_report_generator'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Enrollment Report")

    def test_enrollment_report_context_data(self):
        response = self.client.get(reverse('enrollment_report_generator'))

        self.assertEqual(response.context['total_students'], 2)
        self.assertEqual(response.context['total_enrollments'], 3)

        top_course = response.context['top_course']
        self.assertEqual(top_course.code, "CS101")
        self.assertEqual(top_course.title, "Intro to Computer Science")

    def test_top_course_displayed(self):
        response = self.client.get(reverse('enrollment_report_generator'))
        self.assertContains(response, "Most Popular Course: CS101")

    def test_enrollment_by_course_rendered(self):
        response = self.client.get(reverse('enrollment_report_generator'))
        self.assertContains(response, "<ol>")
        self.assertContains(response, "Intro to Computer Science")
        self.assertContains(response, "Data Structures")

    def test_enrollment_by_month_rendered(self):
        response = self.client.get(reverse('enrollment_report_generator'))
        self.assertContains(response, "<table>")
        self.assertContains(response, "2024-01")
        self.assertContains(response, "2024-02")

    def test_post_request_returns_page(self):
        response = self.client.post(reverse('enrollment_report_generator'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Enrollment Report")
