from django.test import TestCase, Client
from django.urls import reverse
from django.core import mail
from ..models import (
    MyUser, Course, Enrollment, OverrideRequest,
    Grade, OfficeHourSlot, OfficeHourBooking
)

class InstructorFeaturesTests(TestCase):
    def setUp(self):
        # feature setup: create instructor and a student
        self.client = Client()
        self.instructor = MyUser.objects.create(
            fullName="John Jay", name='instr1', password='pass', role='instructor', email='instr@example.com'
        )
        self.student = MyUser.objects.create(
            fullName="Larry Bird", name='student1', password='pass', role='student', email='student@example.com'
        )
        # login as instructor
        self.client.post(reverse('login'), {
            'name': 'instr1', 'password': 'pass', 'role': 'instructor'
        })
        # create a course and related objects
        self.course = Course.objects.create(
            code='CS101', title='Test Course', instructor=self.instructor
        )
        self.enrollment = Enrollment.objects.create(
            student=self.student, course=self.course
        )
        self.override_request = OverrideRequest.objects.create(
            student=self.student, course=self.course, reason='Need override'
        )

    # existing tests for features 1–4…
    def test_manage_enrollments_view(self):
        response = self.client.get(reverse('instructor_enrollments'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.student.name)

    def test_remove_enrollment(self):
        response = self.client.post(reverse('instructor_enrollments'), {
            'enrollment_id': self.enrollment.id, 'action': 'remove'
        })
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Enrollment.objects.filter(id=self.enrollment.id).exists())

    def test_manage_override_requests_view(self):
        response = self.client.get(reverse('instructor_requests'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.override_request.reason)

    def test_approve_override_request(self):
        response = self.client.post(reverse('instructor_requests'), {
            'request_id': self.override_request.id, 'action': 'approve'
        })
        self.assertEqual(response.status_code, 302)
        req = OverrideRequest.objects.get(id=self.override_request.id)
        self.assertEqual(req.status, 'approved')
        self.assertTrue(Enrollment.objects.filter(
            student=self.student, course=self.course).exists())

    def test_deny_override_request(self):
        response = self.client.post(reverse('instructor_requests'), {
            'request_id': self.override_request.id, 'action': 'deny'
        })
        self.assertEqual(response.status_code, 302)
        req = OverrideRequest.objects.get(id=self.override_request.id)
        self.assertEqual(req.status, 'denied')

    def test_send_email(self):
        response = self.client.post(reverse('instructor_email'), {
            'course_id': self.course.id,
            'subject': 'Test',
            'message': 'Hello students'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.subject, 'Test')
        self.assertIn(self.student.email, email.to)

    def test_edit_course(self):
        response = self.client.post(reverse('edit_course', args=[self.course.id]), {
            'syllabus': 'New syllabus',
            'meeting_times': 'MWF 10-11',
            'seat_limit': '50'
        })
        self.assertEqual(response.status_code, 302)
        course = Course.objects.get(id=self.course.id)
        self.assertEqual(course.syllabus, 'New syllabus')
        self.assertEqual(course.meeting_times, 'MWF 10-11')
        self.assertEqual(course.seat_limit, 50)

    # new tests for Feature 5: Grade entry/update
    def test_grade_entry_get(self):
        url = reverse('grade-entry', args=[self.course.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"Grades for {self.course.name}")

    def test_grade_entry_post_creates_grade(self):
        url = reverse('grade-entry', args=[self.course.id])
        response = self.client.post(url, {
            'enrollment_id': self.enrollment.id,
            'assignment': 'Midterm',
            'score': '92.50',
            'feedback': 'Great job!'
        })
        self.assertEqual(response.status_code, 302)
        grade = Grade.objects.get(
            enrollment=self.enrollment,
            assignment_name='Midterm'
        )
        self.assertEqual(str(grade.score), '92.50')
        self.assertEqual(grade.feedback, 'Great job!')

    def test_grade_entry_post_updates_grade(self):
        # pre-create a grade to update
        Grade.objects.create(
            enrollment=self.enrollment,
            assignment_name='Midterm',
            score=80,
            feedback='Good'
        )
        url = reverse('grade-entry', args=[self.course.id])
        response = self.client.post(url, {
            'enrollment_id': self.enrollment.id,
            'assignment': 'Midterm',
            'score': '88.00',
            'feedback': 'Improved'
        })
        self.assertEqual(response.status_code, 302)
        grade = Grade.objects.get(
            enrollment=self.enrollment,
            assignment_name='Midterm'
        )
        self.assertEqual(str(grade.score), '88.00')
        self.assertEqual(grade.feedback, 'Improved')

    # new tests for Feature 6: Office‑hour slots & booking
    def test_office_hour_slot_create(self):
        url = reverse('office-hours-create')
        response = self.client.post(url, {
            'start_time': '2025-06-01T10:00',
            'end_time':   '2025-06-01T11:00'
        })
        self.assertEqual(response.status_code, 302)
        slot = OfficeHourSlot.objects.get(instructor=self.instructor)
        # the view parses datetime-local strings into naive datetimes
        self.assertEqual(
            slot.start_time.strftime('%Y-%m-%dT%H:%M'),
            '2025-06-01T10:00'
        )
        self.assertEqual(
            slot.end_time.strftime('%Y-%m-%dT%H:%M'),
            '2025-06-01T11:00'
        )

    def test_office_hours_list_view(self):
        # create a slot manually
        slot = OfficeHourSlot.objects.create(
            instructor=self.instructor,
            start_time='2025-06-02T12:00',
            end_time='2025-06-02T13:00'
        )
        url = reverse('office-hours')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # ensure the slot appears in the context
        self.assertIn(slot, response.context['slots'])

    def test_book_office_hour_slot(self):
        # create a slot to be booked
        slot = OfficeHourSlot.objects.create(
            instructor=self.instructor,
            start_time='2025-06-03T14:00',
            end_time='2025-06-03T15:00'
        )
        # login as the student
        self.client.post(reverse('login'), {
            'name': 'student1', 'password': 'pass', 'role': 'student'
        })
        url = reverse('office-hours-book', args=[slot.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        booking = OfficeHourBooking.objects.get(slot=slot, student=self.student)
        self.assertIsNotNone(booking)
