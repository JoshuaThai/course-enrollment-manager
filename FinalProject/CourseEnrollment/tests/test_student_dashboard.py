from django.test import TestCase, Client
from django.urls import reverse
from ..models import MyUser



class StudentDashboardTests(TestCase):
    def setUp(self):
        # Create a student user
        self.client = Client()
        self.student = MyUser.objects.create(fullName = "John Doe", name="student1", password="testpass123", role="student")
        # Simulate login
        session = self.client.session
        session['name'] = self.student.name
        session['role'] = self.student.role
        session.save()

    def test_student_dashboard_loads_successfully(self):
        """Test that the student dashboard page loads and displays the student name."""
        response = self.client.get(reverse('student_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Welcome")
        self.assertContains(response, self.student.fullName)

    def test_student_dashboard_displays_correct_role(self):
        """Test that the student dashboard correctly shows 'student' role."""
        response = self.client.get(reverse('student_dashboard'))
        self.assertContains(response, "Role: student")