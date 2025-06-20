from django.test import TestCase, Client
from django.urls import reverse
from ..models import MyUser  # Adjust import if needed

class SignupViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.signup_url = reverse('signup')  # Adjust if URL name is different

    def test_signup_page_loads_successfully(self):
        response = self.client.get(self.signup_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Create Your Account")

    def test_successful_student_signup_redirects_to_student_dashboard(self):
        response = self.client.post(self.signup_url, {
            'fullName': 'Test Student',
            'name': 'studentuser',
            'email': 'student@example.com',
            'password': 'testpass123',
            'role': 'student'
        })
        self.assertRedirects(response, reverse('student_dashboard'))
        self.assertTrue(MyUser.objects.filter(name='studentuser').exists())

    def test_successful_instructor_signup_redirects_to_instructor_dashboard(self):
        response = self.client.post(self.signup_url, {
            'fullName': 'Test Instructor',
            'name': 'instructoruser',
            'email': 'instructor@example.com',
            'password': 'testpass123',
            'role': 'instructor'
        })
        self.assertRedirects(response, reverse('instructor_dashboard'))
        self.assertTrue(MyUser.objects.filter(name='instructoruser').exists())

    def test_successful_admin_signup_redirects_to_admin_dashboard(self):
        response = self.client.post(self.signup_url, {
            'fullName': 'Admin User',
            'name': 'adminuser',
            'email': 'admin@example.com',
            'password': 'testpass123',
            'role': 'administrator'
        })
        self.assertRedirects(response, reverse('admin_dashboard'))
        self.assertTrue(MyUser.objects.filter(name='adminuser').exists())

    def test_duplicate_username_shows_error(self):
        MyUser.objects.create(fullName='Existing User', name='takenuser', password='pass', email='test@test.com', role='student')
        response = self.client.post(self.signup_url, {
            'fullName': 'New User',
            'name': 'takenuser',
            'email': 'new@example.com',
            'password': 'newpass123',
            'role': 'student'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'That username is already taken.')
