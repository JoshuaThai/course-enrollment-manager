from django.test import TestCase, Client
from ..models import MyUser

"""
1. Login System Test for Students
    - We need to test if the login system redirects properly for students
    - We need to test if the role is remaining consistent during login
    - We need to test if password validation is occurring correctly.
2. Login System Test for Instructors
    - We need to test for same thing as above just for instructors
"""

class StudentLogin(TestCase):
    def setUp(self):
        self.user = MyUser.objects.create(fullName= "John Doe", name='testuser', password='testpass', role='student')
        session = self.client.session
        session['name'] = 'testuser'
        session['role'] = 'student'
        session.save()
    def test_correct_name_in_response(self):
        client = Client()
        response = client.post('/', {'name': 'testuser', 'password': 'testpass'}, follow=True)
        self.assertContains(response, "John Doe")
    def test_correct_role_in_response(self):
        client = Client()
        response = client.post('/', {'name': 'testuser', 'password': 'testpass'}, follow=True)
        self.assertEqual(response.context['role'], 'student')
    def test_incorrect_password_in_response(self):
        client = Client()
        response = client.post('/', {'name': 'testuser', 'password': 'testpass1'}, follow=True)
        self.assertFalse(response.context['user'].is_authenticated)
        self.assertContains(response, 'Incorrect Password' )
    # need to create more tests for student login

class InstructorLogin(TestCase):
    def setUp(self):
        self.user = MyUser.objects.create(fullName= "John Williams", name='testuser', password='testpass', role='instructor')
    def test_correct_name_in_response(self):
        client = Client()
        response = client.post('/', {'name': 'testuser', 'password': 'testpass'}, follow=True)
        self.assertContains(response, "John Williams")
    def test_correct_role_in_response(self):
        client = Client()
        response = client.post('/', {'name': 'testuser', 'password': 'testpass'}, follow=True)
        self.assertEqual(response.context['role'], 'instructor')
    def test_incorrect_password_in_response(self):
        client = Client()
        response = client.post('/', {'name': 'testuser', 'password': 'testpass1'}, follow=True)
        self.assertFalse(response.context['user'].is_authenticated)
        self.assertContains(response, 'Incorrect Password' )

class AdminLogin(TestCase):
    def setUp(self):
        self.user = MyUser.objects.create(fullName= "John Doe", name='testuser', password='testpass', role='administrator')
        session = self.client.session
        session['name'] = 'testuser'
        session['role'] = 'administrator'
        session.save()
    def test_correct_name_in_response(self):
        client = Client()
        response = client.post('/', {'name': 'testuser', 'password': 'testpass'}, follow=True)
        self.assertEqual(client.session['name'], 'testuser')
    def test_correct_role_in_response(self):
        client = Client()
        response = client.post('/', {'name': 'testuser', 'password': 'testpass'}, follow=True)
        self.assertEqual(response.context['role'], 'administrator')
    def test_incorrect_password_in_response(self):
        client = Client()
        response = client.post('/', {'name': 'testuser', 'password': 'testpass1'}, follow=True)
        self.assertFalse(response.context['user'].is_authenticated)
        self.assertContains(response, 'Incorrect Password' )
