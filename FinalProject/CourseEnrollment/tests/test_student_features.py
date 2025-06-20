from django.test import TestCase
from django.urls import reverse
from ..models import MyUser, Course, Enrollment, OverrideRequest, WaitlistEntry


class StudentFeaturesTests(TestCase):
    def setUp(self):
        # Create a test student
        self.student = MyUser.objects.create(name='teststudent', password='password123', role='student')
        self.instructor = MyUser.objects.create(name='testinstructor', password='password', role='instructor')
        # self.client.post(reverse('login'), {
        #     'name': 'teststudent',
        #     'password': 'password123',
        #     'role': 'student',
        # })

        # Manually simulate session login
        session = self.client.session
        session['name'] = self.student.name
        session['role'] = self.student.role
        session.save()

        # Create a couple test courses
        self.course1 = Course.objects.create( code='MATH101',
        title='Math 101',
        syllabus='Algebra and Calculus basics',
        meeting_times='MWF 9-10AM',
        seat_limit=2,
        instructor=self.instructor)
        self.course2 = Course.objects.create(code='HIST202',
        title='History 202',
        syllabus='World History overview',
        meeting_times='TTh 1-2:30PM',
        seat_limit=0,
        instructor=self.instructor)

    def test_search_courses(self):
        response = self.client.get(reverse('search_courses'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Math 101')
        self.assertContains(response, 'History 202')

    def test_enroll_in_course(self):
        response = self.client.get(reverse('enroll_course', args=[self.course1.id]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Enrollment.objects.filter(student=self.student, course=self.course1).exists())

    def test_drop_course(self):
        Enrollment.objects.create(student=self.student, course=self.course1)
        response = self.client.post(reverse('drop_course', args=[self.course1.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Enrollment.objects.filter(student=self.student, course=self.course1).exists())

    def test_submit_override_request(self):
        response = self.client.post(reverse('request_override', args=[self.course2.id]), {
            'reason': 'Need this course to graduate.'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(OverrideRequest.objects.filter(student=self.student, course=self.course2).exists())

    def test_view_waitlist_status(self):
        WaitlistEntry.objects.create(student=self.student, course=self.course2)
        response = self.client.get(reverse('waitlist_status'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'History 202')

