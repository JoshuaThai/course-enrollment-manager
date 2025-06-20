from django.core.exceptions import MultipleObjectsReturned
from django.template.base import kwarg_re
from django.test import TestCase, Client
from django.urls import reverse

from ..models import Course, MyUser, OverrideRequest


class AdminOverrideRequestsTest(TestCase):
    def setUp(self):
        self.client = Client()

        # Create test users and course
        self.student = MyUser.objects.create(fullName= "Alice Wonderland",name='Alice', password='pass', role='student')
        self.instructor = MyUser.objects.create(
            fullName="Will Smith", name='Dr. Smith', password='pass', role='instructor')
        self.course = Course.objects.create(code='CS101', title='Intro to CS', instructor=self.instructor)

        # Create override requests
        self.req_prereq = OverrideRequest.objects.create(
            student=self.student,
            course=self.course,
            reason="Missing prerequisite but want to enroll.",
            status='pending'
        )
        self.req_seats = OverrideRequest.objects.create(
            student=self.student,
            course=self.course,
            reason="Course is full but I need it to graduate.",
            status='pending'
        )

    def test_admin_override_approved(self):
        # Approve the prerequisite override request
        response = self.client.post('/admin_enrollment_manager/', {
            'request_id': self.req_prereq.id,
            'action': 'approve'
        })

        self.req_prereq.refresh_from_db()
        # should be re-rendering the enrollment manager page
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.req_prereq.status, 'approved')

        # Ensure it no longer appears in pending
        pending = OverrideRequest.objects.filter(status='pending')
        self.assertNotIn(self.req_prereq, pending)

    def test_admin_override_denied(self):
        # Deny the seat-limit override request
        response = self.client.post('/admin_enrollment_manager/', {
            'request_id': self.req_seats.id,
            'action': 'denied'
        })

        self.req_seats.refresh_from_db()
        # should be re-rendering the enrollment manager page
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.req_seats.status, 'denied')

        # Ensure it no longer appears in pending
        pending = OverrideRequest.objects.filter(status='pending')
        self.assertNotIn(self.req_seats, pending)