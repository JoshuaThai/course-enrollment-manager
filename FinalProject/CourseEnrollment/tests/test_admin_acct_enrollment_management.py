from django.test import TestCase, Client
from django.urls import reverse
from ..models import MyUser, Course, Enrollment
from datetime import date

class AdminEditEnrollmentTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Create instructor user
        self.instructor = MyUser.objects.create(
            name="Dr. Instructor",
            email="instructor@example.com",
            password="teachpass",
            role="instructor"
        )

        # Create student user
        self.student = MyUser.objects.create(
            name="Test Student",
            email="student@example.com",
            password="pass123",
            role="student"
        )

        # Create course with instructor
        self.course = Course.objects.create(
            code="CS101",
            title="Intro to Computer Science",
            instructor=self.instructor
        )

        # Create enrollment
        self.enrollment = Enrollment.objects.create(
            student=self.student,
            course=self.course,
            date_enrolled=date(2024, 5, 1),
            final_grade="B"
        )

    def test_edit_enrollment_form_loads(self):
        response = self.client.post(reverse('admin_edit_enrollment'), {
            'student_id': self.student.id
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Edit Enrollments for")
        self.assertContains(response, self.course.title)
        self.assertContains(response, 'name="grade_{}"'.format(self.enrollment.id))

    def test_edit_enrollment_submission_updates_data(self):
        new_grade = "A"
        new_date = "2024-09-15"

        response = self.client.post(reverse('admin_edit_enrollment'), {
            'student_id': self.student.id,
            f'grade_{self.enrollment.id}': new_grade,
            f'date_{self.enrollment.id}': new_date
        })

        # Should redirect back to history page
        self.assertEqual(response.status_code, 200)

        # Check database updates
        self.enrollment.refresh_from_db()
        self.assertEqual(self.enrollment.final_grade, new_grade)
        self.assertEqual(str(self.enrollment.date_enrolled), new_date)

    def test_missing_student_id_redirects(self):
        response = self.client.post(reverse('admin_edit_enrollment'), {})
        self.assertEqual(response.status_code, 302)

class AdminStudentEditViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.student = MyUser.objects.create(
            fullName='Old Full Name',
            name='Old Name',
            email='old@example.com',
            password='oldpass',
            role='student'
        )

    def test_edit_student_account_form_loads(self):
        response = self.client.post(reverse('admin_student_acct_edit'), {
            'student_id': self.student.id
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"Edit {self.student.name}'s Account")
        self.assertContains(response, self.student.email)

    def test_edit_student_account_submission_updates_data(self):
        response = self.client.post(reverse('admin_student_acct_edit'), {
            'student_id': self.student.id,
            'name': 'New Name',
            'email': 'new@example.com',
            'password': 'newpass'
        })
        self.assertEqual(response.status_code, 200)  # Should redirect to student manager

        self.student.refresh_from_db()
        self.assertEqual(self.student.name, 'New Name')
        self.assertEqual(self.student.email, 'new@example.com')
        self.assertEqual(self.student.password, 'newpass')

    def test_invalid_student_id_redirects(self):
        response = self.client.post(reverse('admin_student_acct_edit'), {
            'student_id': 9999  # nonexistent ID
        })
        self.assertEqual(response.status_code, 302)


