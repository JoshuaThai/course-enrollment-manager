from django.core.exceptions import MultipleObjectsReturned
from django.template.base import kwarg_re
from django.test import TestCase, Client
from django.urls import reverse

from ..models import Course, MyUser

# Code cannot be edited and should not be edited under no circumstances.
# We can test modifying all other parts of the Course though.
class AdminCourseEditTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.course = Course.objects.create(
            code='CS101',
            title='Intro to CS',
            syllabus='Old syllabus',
            meeting_times='MWF 10-11',
            seat_limit=30,
            instructor= MyUser.objects.create(
                fullName="John Adams", name='John', password = 'password', role='instructor')
        )
    def test_edit_title(self):
        response = self.client.post('/admin_edit_course/', {
            'course_code': 'CS101',
            'title': 'Intro to Computer Science',
            'syllabus': 'Old syllabus',
            'meeting_times': 'MWF 10-11',
            'seat_limit': 30,
            'instructor_name': 'John'
        })
        self.course.refresh_from_db()
        self.assertEqual(self.course.title, 'Intro to Computer Science')
        # check if it unchanged.
        self.assertFalse(self.course.title == 'Intro to CS')
        # check if title is really correct.
        self.assertFalse(self.course.title =='CS INTRO')

    def test_edit_syllabus(self):
        response = self.client.post('/admin_edit_course/', {
            'course_code': 'CS101',
            'title': 'Intro to Computer Science',
            'syllabus': 'New syllabus',
            'meeting_times': 'MWF 10-11',
            'seat_limit': 30,
            'instructor_name': 'John'
        })
        self.course.refresh_from_db()
        self.assertEqual(self.course.syllabus, 'New syllabus')
        # check if it unchanged.
        self.assertFalse(self.course.syllabus == 'Old syllabus')
        # check if title is really correct.
        self.assertFalse(self.course.syllabus =='random stuff')

    def test_edit_meeting_times(self):
        response = self.client.post('/admin_edit_course/', {
            'course_code': 'CS101',
            'title': 'Intro to Computer Science',
            'syllabus': 'New syllabus',
            'meeting_times': 'TF 12-1:50',
            'seat_limit': 30,
            'instructor_name': 'John'
        })
        self.course.refresh_from_db()
        self.assertEqual(self.course.meeting_times, 'TF 12-1:50')
        # check if it unchanged.
        self.assertFalse(self.course.meeting_times == 'MWF 10-11')
        # check if title is really correct.
        self.assertFalse(self.course.meeting_times =='TR 12-1:50')

    def test_edit_seat_limit(self):
        response = self.client.post('/admin_edit_course/', {
            'course_code': 'CS101',
            'title': 'Intro to CS',
            'syllabus': 'Old syllabus',
            'meeting_times': 'MWF 10-11',
            'seat_limit': 25,
            'instructor_name': 'John'
        })
        self.course.refresh_from_db()
        self.assertEqual(self.course.seat_limit, 25)
        # check if it unchanged.
        self.assertFalse(self.course.title == 30)
        # check if seat limit is really correct.
        self.assertFalse(self.course.title == 0)

    def test_edit_instructor(self):
        # Ensure instructor doesn't exist yet
        self.assertFalse(MyUser.objects.filter(name='NewInstructor', role='instructor').exists())

        response = self.client.post('/admin_edit_course/', {
            'course_code': 'CS101',
            'title': 'Intro to CS',
            'syllabus': 'Old syllabus',
            'meeting_times': 'MWF 10-11',
            'seat_limit': 30,
            'instructor_name': 'Bob'
        })
        self.course.refresh_from_db()

        # instructor isn't changing because we haven't implemented a way to change instructor info.
        self.assertEqual(self.course.instructor.name, 'Bob')
        # check if it unchanged.
        self.assertFalse(self.course.instructor.name == 'John')
        # check if role is 'instructor'
        self.assertTrue(self.course.instructor.role == 'instructor')
        # check if password matches
        self.assertFalse(self.course.instructor.password == 'password')

        # Check that the instructor was created
        new_instructor = MyUser.objects.filter(name='Bob', role='instructor').first()
        self.assertIsNotNone(new_instructor)

        # perform additional checks
        # check if name matches the newly created object for instructor.
        self.assertEqual(self.course.instructor.name, new_instructor.name)
        # check if role matches for the newly created object for instructor
        self.assertEqual(self.course.instructor.role, new_instructor.role)

class AdminCourseAddTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.course = Course.objects.create(
            code='CS101',
            title='Intro to CS',
            syllabus='Old syllabus',
            meeting_times='MWF 10-11',
            seat_limit=30,
            instructor=MyUser.objects.create(name='John', password='password', role='instructor')
        )
    # first we will test if it can handle cases where you entered unacceptable output for course code.

    # check if invalid input for course code is detected.
    # test handling of code being invalid when non-digits are entered.
    def test_add_invalid_code_empty(self):
        response = self.client.post('/admin_add_course/', {
            'course_code': '',
            'title': 'Intro to Computer Science',
            'syllabus': 'New syllabus',
            'meeting_times': 'MWF 10-11',
            'instructor_name': 'John',
            'seat_limit': 30
        })
        self.course.refresh_from_db()
        # Check that we stayed on the same page (status 200)
        self.assertEqual(response.status_code, 200)

        # Check that the expected error message appear.
        self.assertContains(response, 'Invalid course code. The field cannot be blank')

        # Check that the course wasn't unintentionally made despite error.
        self.assertFalse(Course.objects.filter(code='').exists())

    # test handling of code being invalid when only whitespace are entered.
    def test_add_invalid_code_space(self):
        response = self.client.post('/admin_add_course/', {
            'course_code': ' ',
            'title': 'Intro to Computer Science',
            'syllabus': 'New syllabus',
            'meeting_times': 'MWF 10-11',
            'instructor_name': 'John',
            'seat_limit': 30
        })
        self.course.refresh_from_db()
        # Check that we stayed on the same page (status 200)
        self.assertEqual(response.status_code, 200)

        # Check that the expected error message appear.
        self.assertContains(response, 'Invalid course code. The field cannot be blank')

        # Check that the course wasn't unintentionally made despite error.
        self.assertFalse(Course.objects.filter(code=' ').exists())

    # test handling of code being invalid when it is not of the right length, despite being all digits
    def test_add_invalid_code_alreadyUsed(self):
        response = self.client.post('/admin_add_course/', {
            'course_code': 'CS101',
            'title': 'Intro to Computer Science',
            'syllabus': 'New syllabus',
            'meeting_times': 'MWF 10-11',
            'instructor_name': 'John',
            'seat_limit': 30
        })
        self.course.refresh_from_db()
        # Check that we stayed on the same page (status 200)
        self.assertEqual(response.status_code, 200)

        # Check that the expected error message appear.
        self.assertContains(response, 'Code already in use. Enter another code')

        # Check that the course wasn't unintentionally made despite error.
        try:
            Course.objects.filter(code='CS101').get()
        except MultipleObjectsReturned:
            self.fail("MultipleObjectsReturned was raised unexpectedly.")

    def test_add_invalid_title(self):
        response = self.client.post('/admin_add_course/', {
            'course_code': 'CS102',
            'title': ' ',
            'syllabus': 'New syllabus',
            'meeting_times': 'MWF 10-11',
            'instructor_name': 'John',
            'seat_limit': 30
        })
        self.course.refresh_from_db()
        # Check if we stay on page.
        self.assertEqual(response.status_code, 200)

        # check if correct error message was returned.
        self.assertContains(response, 'Invalid course title. No blank spaces')

        self.assertFalse(Course.objects.filter(title=' ').exists())

    def test_add_invalid_syllabus(self):
        response = self.client.post('/admin_add_course/', {
            'course_code': 'CS102',
            'title': 'Intermediate Computer Programming',
            'syllabus': '',
            'meeting_times': 'MWF 10-11',
            'instructor_name': 'John',
            'seat_limit': 30
        })
        self.course.refresh_from_db()
        # Check if we stay on page.
        self.assertEqual(response.status_code, 200)

        # check if correct error message was returned.
        self.assertContains(response, 'Invalid course syllabus. No blank spaces.')

        self.assertFalse(Course.objects.filter(syllabus = '').exists())

    def test_add_invalid_meeting_times(self):
        response = self.client.post('/admin_add_course/', {
            'course_code': 'CS102',
            'title': 'Intermediate Computer Programming',
            'syllabus': 'Syllabus',
            'meeting_times': ' ',
            'instructor_name': 'John',
            'seat_limit': 30
        })
        self.course.refresh_from_db()
        # Check if we stay on page.
        self.assertEqual(response.status_code, 200)

        # check if correct error message was returned.
        self.assertContains(response, 'Invalid meeting times. No blank spaces')

        self.assertFalse(Course.objects.filter(meeting_times=' ').exists())

    def test_add_invalid_instructor(self):
        response = self.client.post('/admin_add_course/', {
            'course_code': 'CS102',
            'title': 'Intermediate Computer Programming',
            'syllabus': 'Syllabus',
            'meeting_times': 'MW 10 - 11:15 AM',
            'instructor_name': ' ',
            'seat_limit': 30
        })
        self.course.refresh_from_db()
        # Check if we stay on page.
        self.assertEqual(response.status_code, 200)

        # check if correct error message was returned.
        self.assertContains(response, 'Invalid instructor name. No blank spaces')

        #check if object wasn't accidentally created with invalid instructor.
        self.assertFalse(MyUser.objects.filter(name=' ', role = 'instructor').exists())

    def test_add_invalid_seat_limit(self):
        response = self.client.post('/admin_add_course/', {
            'course_code': 'CS102',
            'title': 'Intermediate Computer Programming',
            'syllabus': 'Syllabus',
            'meeting_times': 'MW 10 - 11:15 AM',
            'instructor_name': 'Josh',
            'seat_limit': -1
        })
        self.course.refresh_from_db()
        # Check if we stay on page.
        self.assertEqual(response.status_code, 200)

        # check if correct error message was returned.
        self.assertContains(response, 'Invalid seat limit. Seat limit must be one or more')

        #check if object wasn't accidentally created with invalid instructor.
        self.assertFalse(Course.objects.filter(seat_limit= -1).exists())

    def test_add_valid_course(self):
        response = self.client.post('/admin_add_course/', {
            'course_code': 'CS102',
            'title': 'Intermediate Computer Programming',
            'syllabus': 'Syllabus',
            'meeting_times': 'MW 10 - 11:15 AM',
            'instructor_name': 'Josh',
            'seat_limit': 10
        })
        self.course.refresh_from_db()
        # Check if we stay on page.
        self.assertEqual(response.status_code, 200)

        # check if correct error message was returned.
        self.assertContains(response, 'Added course successfully.')

        find_instructor = MyUser.objects.filter(name='Josh', role = 'instructor').first()
        self.assertTrue(find_instructor)
        # check if object was created
        self.assertTrue(Course.objects.filter(
            code = 'CS102', title = 'Intermediate Computer Programming',
        syllabus = 'Syllabus', meeting_times = 'MW 10 - 11:15 AM',
        seat_limit = 10, instructor = find_instructor).exists())

class AdminCourseDeleteTest(TestCase):
    def setUp(self):
        self.client = Client()

        new_instructor = MyUser.objects.create(
            name='Test Instructor',
            password='pass',
            role='instructor'
        )

        self.course = Course.objects.create(
            code='CS105',
            title='Test Course',
            syllabus='Sample syllabus',
            meeting_times='MWF 10-11',
            instructor= new_instructor,
            seat_limit=25
        )
    def test_admin_course_delete(self):
        response = self.client.post('/admin_course_manager/', {
            'course_id': 'CS105',
            'action': 'delete'
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Course.objects.filter(code='CS105').exists())
        self.assertNotContains(response, 'Test Course')
        self.assertContains(response, 'Course Deleted Successfully')

class AdminPrerequisiteEditingTest(TestCase):
    def setUp(self):
        self.client = Client()

        # Create an instructor
        self.instructor = MyUser.objects.create(name='Dr. Smith', password='pass', role='instructor')

        # Create courses
        self.course = Course.objects.create(code='CS201', title='Data Structures', instructor=self.instructor)
        self.prereq1 = Course.objects.create(code='CS101', title='Intro to CS', instructor=self.instructor)
        self.prereq2 = Course.objects.create(code='CS150', title='Programming Basics', instructor=self.instructor)

        # Set session manually to simulate selected course for editing
        session = self.client.session
        session['editing_course_id'] = 'CS201'
        session.save()

    def test_add_prerequisites(self):
        response = self.client.post('/admin_edit_course/', {
            'course_code': 'CS201',
            'title': 'Data Structures',
            'syllabus': 'Learn about trees and graphs.',
            'meeting_times': 'MWF 10-11',
            'instructor_name': 'Dr. Smith',
            'seat_limit': 30,
            'prerequisites': [str(self.prereq1.id), str(self.prereq2.id)]
        })

        self.course.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(set(self.course.prerequisites.all()), {self.prereq1, self.prereq2})

    def test_remove_prerequisite(self):
        # Pre-add both
        self.course.prerequisites.set([self.prereq1, self.prereq2])

        # Now simulate removing one prereq
        response = self.client.post('/admin_edit_course/', {
            'course_code': 'CS201',
            'title': 'Data Structures',
            'syllabus': 'Updated syllabus.',
            'meeting_times': 'MWF 10-11',
            'instructor_name': 'Dr. Smith',
            'seat_limit': 30,
            'prerequisites': [str(self.prereq1.id)]  # only keep one
        })

        self.course.refresh_from_db()
        # check if we stay on page.
        self.assertEqual(response.status_code, 302)
        # check if only first prereq remains in prerequisities list.
        self.assertIn(self.prereq1, self.course.prerequisites.all())
        self.assertNotIn(self.prereq2, self.course.prerequisites.all())

    class AddCourseWithPrerequisitesTest(TestCase):
        def setUp(self):
            self.client = Client()

            # Create an instructor
            self.instructor = MyUser.objects.create(name='Dr. Brown', password='pass', role='instructor')

            # Create prerequisite courses
            self.prereq1 = Course.objects.create(code='CS100', title='Intro to CS', instructor=self.instructor)
            self.prereq2 = Course.objects.create(code='CS150', title='Programming Basics',
                                                 instructor=self.instructor)

        def test_add_course_with_prerequisites(self):
            response = self.client.post('/admin_add_course/', {
                'course_code': 'CS200',
                'title': 'Data Structures',
                'syllabus': 'Covers trees, graphs, and more.',
                'meeting_times': 'MWF 9:00 - 10:00 AM',
                'instructor_name': 'Dr. Brown',
                'seat_limit': 30,
                'prerequisites': [str(self.prereq1.id), str(self.prereq2.id)]
            })

            # Confirm redirect or success response
            self.assertEqual(response.status_code, 302)

            # Verify the course was created
            new_course = Course.objects.get(code='CS200')
            prereqs = new_course.prerequisites.all()

            # Check both prerequisites were saved
            self.assertIn(self.prereq1, prereqs)
            self.assertIn(self.prereq2, prereqs)
