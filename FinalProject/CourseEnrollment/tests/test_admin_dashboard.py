from django.test import TestCase, Client
from django.urls import reverse

from ..models import MyUser
# reverse checks the url path from a name which you specify in urls.py
class AdminDashboardTest(TestCase):
    def setUp(self):
        client = Client()
        # self.user = MyUser.objects.create(name='testuser', password='testpass', role='admin')
        response = client.post('/', {'name': 'testuser', 'password': 'testpass'}, follow=True)
        # Simulate a session with admin credentials
        session = self.client.session
        session['name'] = 'testuser'
        session['role'] = 'administrator'
        session.save()

    def test_course_manager_url(self):
        url = reverse('admin_course_manager')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # check some text that should appear on that page:
        self.assertContains(response, "Course Manager")
    def test_enrollment_manager_url(self):
        url = reverse('admin_enrollment_manager')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # check some text that should appear on that page:
        self.assertContains(response, "Special Enrollment Requests")
    def test_admin_student_manager_url(self):
        url = reverse('admin_student_manager')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # check some text that should appear on that page:
        self.assertContains(response, "Student Accounts Manager")
    def test_enrollment_report_url(self):
        url = reverse('enrollment_report_generator')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # check some text that should appear on that page:
        self.assertContains(response, "Enrollment Report")
