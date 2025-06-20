from datetime import date, timedelta, datetime

from django.contrib.auth import logout

from idlelib.rpc import request_queue

from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.core.mail import send_mail

from .models import MyUser, Course, Enrollment, OverrideRequest, WaitlistEntry, Grade, OfficeHourSlot, OfficeHourBooking


class LoginView(View):
    def get(self, request):
        request.session.flush() # flush out any session fields.
        # print("get was called.")
        return render(request, "login.html")

    def post(self, request):
        # print("post was called.")
        name = request.POST['name']
        password = request.POST['password']
        # role = request.POST['role']
        user = MyUser.objects.filter(name=name).first()
        if not user: # handle inccorect username
            return render(request, 'login.html', {'message': 'Incorrect Username'})

        if user and user.password != password: # handle inccorect password
                return render(request, 'login.html', {'message': 'Incorrect Password'})

        # store id, name, and role for downstream checks
        request.session['user_id'] = user.id
        request.session['name']    = user.name
        request.session['role']    = user.role
        print("post made it here!")
        if user.role == 'student':
            return redirect('student_dashboard')
        elif user.role == 'administrator':
            return redirect('admin_dashboard')
        print("role:", user.role)
        return redirect('instructor_dashboard')
        # return HttpResponse("Redirecting to instructor dashboard")


class RedirectView(View):
    def get(self, request):
        return render(request, 'redirect.html')


class StudentView(View):
    # gather information needed for Student View
    # gather all courses that students are enrolled in
    def get(self, request):
        name = request.session.get('name')
        if not name or request.session.get('role') != 'student':
            return redirect('login')

        student = MyUser.objects.filter(name=name, role='student').first()
        # Get course IDs the student is already enrolled in
        enrolled_course_ids = Enrollment.objects.filter(student=student).values_list('course_id', flat=True)

        # Filter out those courses — get only ones not enrolled in
        not_enrolled_courses = Course.objects.exclude(id__in=enrolled_course_ids)

        return render(request, 'student_dashboard.html', {'name': student.fullName, 'role': 'student',
            'available_courses': not_enrolled_courses})


class InstructorView(View):
    def get(self, request):
        name = request.session.get('name')
        role = request.session.get('role')
        if not name or role != 'instructor':
            return redirect('login')

        # it isn't finding the user object. because of the two lines commented out
        # instructor = get_object_or_404(MyUser, name=name, role='instructor')
        user = MyUser.objects.filter(name=name).first()
        courses = Course.objects.filter(instructor=user).all()

        return render(request, 'instructor_dashboard.html', {
            'name': user.fullName,
            'role': role,
            'courses': courses,
        })
class AdminView(View):
    # Feature 1: Create and manage courses, including setting prerequisites, seat limits, and instructor
    # assignments
    # Feature 2: Approve or reject special enrollment requests (e.g., overrides for prerequisites, seat limit
    # exceptions)
    # Feature 3: Manage student accounts and enrollment history
    # Feature 4: Generate reports on enrollment statistics and trends
    def get(self, request):
        name = request.session.get('name')
        role = request.session.get('role')
        if not name or role != 'administrator':
            return redirect('login')
        print("role:", role)
        student = MyUser.objects.filter(name=name).first()
        return render(request, 'admin_dashboard.html', {'name': student.fullName, 'role': role})


class SearchCoursesView(View):
    def get(self, request):
        name = request.session.get('name')
        role = request.session.get('role')
        if not name or role != 'student':
            return redirect('login')

        student = MyUser.objects.filter(name=name, role='student').first()
        if not student:
            return redirect('login')

        # Gather filters
        query = request.GET.get('q', '').strip()
        schedule = request.GET.get('schedule', '').strip()

        # Start with all courses
        courses = Course.objects.all()

        # Filter by title or code
        if query:
            courses = courses.filter(title__icontains=query) | courses.filter(code__icontains=query)

        # Filter by meeting_times
        if schedule:
            courses = courses.filter(meeting_times__icontains=schedule)

        # Filter by completed prerequisites (enrolled 119+ days ago)
        cutoff = date.today() - timedelta(days=119)
        completed_course_ids = Enrollment.objects.filter(
            student=student,
            date_enrolled__lte=cutoff
        ).values_list('course_id', flat=True)

        eligible_courses = []
        for course in courses:
            unmet_prereqs = course.prerequisites.exclude(id__in=completed_course_ids)
            if not unmet_prereqs.exists():
                eligible_courses.append(course)

        return render(request, 'search_courses.html', {
            'courses': eligible_courses,
            'query': query,
            'schedule': schedule
        })


class EnrollCourseView(View):
    def get(self, request, course_id):
        name = request.session.get('name')
        if not name:
            return redirect('login')
        user = get_object_or_404(MyUser, name=name)
        course = get_object_or_404(Course, id=course_id)

        # prevent double-enroll
        if Enrollment.objects.filter(student=user, course=course).exists():
            return render(request, "already_enrolled.html", {"course": course})

        Enrollment.objects.create(student=user, course=course)
        return redirect('student_dashboard')


class DropCourseView(View):
    def post(self, request, course_id):
        name = request.session.get('name')
        if not name:
            return redirect('login')

        course = get_object_or_404(Course, id=course_id)
        enrollment = Enrollment.objects.filter(student__name=name, course=course).first()
        if enrollment:
            enrollment.delete()

        return redirect('student_courses')


class StudentCoursesView(View):
    def get(self, request):
        name = request.session.get('name')
        if not name:
            return redirect('login')
        user = get_object_or_404(MyUser, name=name)
        enrollments = Enrollment.objects.filter(student=user)
        return render(request, 'student_courses.html', {'enrollments': enrollments})


class RequestOverrideView(View):
    def get(self, request, course_id):
        name = request.session.get('name')
        if not name:
            return redirect('login')
        course = get_object_or_404(Course, id=course_id)
        existing = OverrideRequest.objects.filter(student__name=name, course=course).first()
        if existing:
            return render(request, 'already_requested.html', {'course': course})
        return render(request, 'request_override.html', {'course': course})

    def post(self, request, course_id):
        name = request.session.get('name')
        if not name:
            return redirect('login')
        course = get_object_or_404(Course, id=course_id)
        student = get_object_or_404(MyUser, name=name)
        reason = request.POST.get('reason')
        OverrideRequest.objects.create(student=student, course=course, reason=reason)
        return redirect('student_dashboard')


class WaitListStatusView(View):
    def get(self, request):
        name = request.session.get('name')
        role = request.session.get('role')
        if not name or role != 'student':
            return redirect('login')

        student = MyUser.objects.filter(name=name, role='student').first()
        if not student:
            return redirect('login')

        entries = WaitlistEntry.objects.filter(student=student)

        entries_with_position = []
        for entry in entries:
            waitlist = WaitlistEntry.objects.filter(course=entry.course).order_by('timestamp')
            position = list(waitlist.values_list('student_id', flat=True)).index(student.id) + 1
            entries_with_position.append({'entry': entry, 'position': position})

        return render(request, 'waitlist_status.html', {
            'waitlist_entries': entries_with_position
        })

class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('login')


# feature 1: Manage Enrollments
class ManageEnrollmentsView(View):
    def get(self, request):
        name = request.session.get('name')
        role = request.session.get('role')
        if not name or role != 'instructor':
            return redirect('login')
        instructor = get_object_or_404(MyUser, name=name, role='instructor')
        courses = Course.objects.filter(instructor=instructor)
        return render(request, 'instructor_enrollments.html', {'courses': courses})

    def post(self, request):
        enrollment_id = request.POST.get('enrollment_id')
        enrollment = get_object_or_404(Enrollment, id=enrollment_id)
        if request.POST.get('action') == 'remove':
            enrollment.delete()
        return redirect('instructor_enrollments')


# feature 2: Override Requests
class ManageOverrideRequestsView(View):
    def get(self, request):
        name = request.session.get('name')
        role = request.session.get('role')
        if not name or role != 'instructor':
            return redirect('login')

        instructor = MyUser.objects.filter(name=name, role='instructor').first()
        reqs = OverrideRequest.objects.filter(course__instructor=instructor, status='pending')
        return render(request, 'instructor_requests.html', {'requests': reqs})

    def post(self, request):
        req = get_object_or_404(OverrideRequest, id=request.POST.get('request_id'))
        req.status = 'approved' if request.POST.get('action') == 'approve' else 'denied'
        req.save()
        if req.status == 'approved':
            Enrollment.objects.create(student=req.student, course=req.course)
        return redirect('instructor_requests')


# feature 3: Send Email
class SendEmailView(View):
    def get(self, request):
        name = request.session.get('name')
        role = request.session.get('role')
        if not name or role != 'instructor':
            return redirect('login')
        instructor = get_object_or_404(MyUser, name=name, role='instructor')
        courses = Course.objects.filter(instructor=instructor)
        return render(request, 'instructor_email.html', {'courses': courses})

    def post(self, request):
        course = Course.objects.filter(
            id=request.POST.get('course_id'),
            instructor__name=request.session.get('name'),
        ).first()
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        students = [enr.student for enr in Enrollment.objects.filter(course=course)]
        recipient_list = [s.email for s in students if s.email]
        send_mail(subject, message, None, recipient_list)
        return render(request, 'email_sent.html', {'recipients': recipient_list})


# feature 4: Edit Course details
class EditCourseView(View):
    def get(self, request, course_id):
        name = request.session.get('name')
        role = request.session.get('role')
        if not name or role != 'instructor':
            return redirect('login')

        instructor = get_object_or_404(MyUser, name=name, role='instructor')
        course = get_object_or_404(Course, id=course_id, instructor=instructor)
        return render(request, 'instructor_edit_course.html', {'course': course})

    def post(self, request, course_id):
        name = request.session.get('name')
        role = request.session.get('role')
        if not name or role != 'instructor':
            return redirect('login')

        instructor = get_object_or_404(MyUser, name=name, role='instructor')
        course = get_object_or_404(Course, id=course_id, instructor=instructor)

        course.syllabus      = request.POST.get('syllabus')
        course.meeting_times = request.POST.get('meeting_times')
        course.seat_limit    = int(request.POST.get('seat_limit'))
        course.save()

        return redirect('instructor_dashboard')
class AdminCourseView(View):
    # Get method used to fetch list of courses.
    def get(self, request):
        name = request.session.get('name')
        role = request.session.get('role')
        if not name or role != 'administrator':
            return redirect('login')

        courses = Course.objects.all()
        return render(request,'admin_course_manager.html', {
            'courses': courses,
            'name' : name ,
            'role' : role})
    # Post method will be used to add/delete/edit courses
    def post(self, request):
        course_id = request.POST.get('course_id')
        action = request.POST.get('action')
        print("Action: ", action)
        if action == 'delete':
            course = Course.objects.filter(code=course_id).first()
            course.delete()
            all_courses = Course.objects.all()
            return render(request, 'admin_course_manager.html', {
                'courses': all_courses,
                'message': 'Course Deleted Successfully'
            })
        request.session['editing_course_id'] = course_id  # store in session
        return redirect('admin_edit_course')
class AdminEditCourseView(View):
    def get(self, request):
        name = request.session.get('name')
        role = request.session.get('role')
        if not name or role != 'administrator':
            return redirect('login')

        course_id = request.session.get('editing_course_id')
        if not course_id:
            return redirect('admin_course_manager')  # fallback
        course = Course.objects.filter(code=course_id).first()
        all_courses = Course.objects.exclude(code=course_id)  # don’t allow self as prereq
        return render(request, 'admin_edit_course.html', {'course': course,
                                                          'all_courses': all_courses})
    def post(self, request):
        # Something wrong when we try to save course editing information.
        course_code = request.POST.get('course_code')
        # print("DEBUG course_code:", course_code)
        if not course_code:
            return redirect('admin_course_manager')  # fallback

        course = Course.objects.get(code=course_code)
        if not course:
            return redirect('admin_course_manager')
        course.title = request.POST.get('title')
        course.syllabus = request.POST.get('syllabus')
        course.meeting_times = request.POST.get('meeting_times')
        # for changes to instructor:
        # We will first check to see if instructor already exist
        instructor_name = request.POST.get('instructor_name')
        # This line will avoid any exception being returned when trying to find instructor.
        find_instructor = MyUser.objects.filter(name=instructor_name, role='instructor').first()
        if find_instructor:
            course.instructor = find_instructor
        else:
            course.instructor = MyUser.objects.create(name=instructor_name, password = "pass",
                                                      role='instructor')

        course.waitlist_enabled = bool(request.POST.get('waitlist_enabled'))
        course.seat_limit = request.POST.get('seat_limit')

        # Save the prereqs
        prereq_ids = request.POST.getlist('prerequisites')
        course.prerequisites.set(prereq_ids)  # ManyToManyField update

        course.save()
        return redirect('admin_course_manager')
class AdminAddCourseView(View):
    def get(self, request):
        name = request.session.get('name')
        role = request.session.get('role')
        if not name or role != 'administrator':
            return redirect('login')

        courses = Course.objects.all()
        return render(request, 'admin_add_course.html', {'courses': courses})
    # handle the processing of adding a new course.
    def post(self, request):
        course_code = request.POST.get('course_code')
        # check if course code exist first and is not just blank or whitespace answer
        if course_code and course_code.strip():
            # if course_code is valid, check....
            # check if course code does not already exist
            check_code = Course.objects.filter(code=course_code).first()
            if check_code:
                return render(request, 'admin_add_course.html', {'message': 'Code already in use. Enter another code'})
        else:
            return render(request, 'admin_add_course.html', {'message': 'Invalid course code. The field cannot be blank'})
        # check if course title is not just blank
        course_title = request.POST.get('title')
        if not course_title or not course_title.strip():
            return render(request, 'admin_add_course.html', {'message': 'Invalid course title. No blank spaces'})
        # check if syllabus isn't empty.
        course_syllabus = request.POST.get('syllabus')
        if not course_syllabus or not course_syllabus.strip():
            return render(request, 'admin_add_course.html', {'message': 'Invalid course syllabus. No blank spaces.'})
        # check if something was entered for meeting times.
        meeting_times = request.POST.get('meeting_times')
        if not meeting_times or not meeting_times.strip():
            return render(request, 'admin_add_course.html', {'message': 'Invalid meeting times. No blank spaces'})
        # check if instructor was entered.
        instructor_name = request.POST.get('instructor_name')
        instructor = 0
        # if instructor name exist, then...
        if instructor_name and instructor_name.strip():
            instructor_found = MyUser.objects.filter(name=instructor_name, role='instructor').first()
            if instructor_found:
                instructor = instructor_found
            else:
                instructor = MyUser.objects.create(name=instructor_name, password = "pass", role = 'instructor')
        else:
            return render(request, 'admin_add_course.html', {'message': 'Invalid instructor name. No blank spaces'})
        waitlist_enabled = bool(request.POST.get('waitlist_enabled'))

        # check if a valid seat limit was entered.
        seat_limit = request.POST.get('seat_limit')
        # safety check
        try:
            seat_limit = int(seat_limit)
        except (TypeError, ValueError):
            seat_limit = 0  # or raise a validation error
        print("seat limit: ", seat_limit)
        # print("seat limit: ", int(seat_limit))
        if seat_limit <= 0:
            return render(request, 'admin_add_course.html', {'message': 'Invalid seat limit. Seat limit must be one or more'})
        # Save the prereqs
        prereq_ids = request.POST.getlist('prerequisites')
        # create course
        new_course = Course.objects.create(code = course_code, title = course_title, syllabus = course_syllabus,
                                           meeting_times = meeting_times, seat_limit = seat_limit, instructor = instructor, waitlist_enabled=waitlist_enabled)
        new_course.prerequisites.set(prereq_ids)
        new_course.save()
        courses = Course.objects.all()
        return render(request, 'admin_course_manager.html', { 'courses' : courses, 'message': 'Added course successfully.'})

class AdminEnrollmentView(View):
    def get(self, request):
        name = request.session.get('name')
        role = request.session.get('role')
        if not name or role != 'administrator':
            return redirect('login')

        pending_requests = OverrideRequest.objects.filter(status='pending')
        return render(request, 'admin_enrollment_manager.html', {
            'name': name,
            'role': role,
            'requests': pending_requests
        })

    def post(self, request):
        request_id = request.POST.get('request_id')
        action = request.POST.get('action')

        override_request = OverrideRequest.objects.filter(id=request_id).first()
        if not override_request:
            pending_requests = OverrideRequest.objects.filter(status='pending')
            return render(request, 'admin_enrollment_manager.html', {
                'requests': pending_requests,
                'message': 'Override request not found.'
            })

        if action == 'denied':
            override_request.status = 'denied'
            override_request.save()
            message = 'Request denied successfully.'
        else:  # action is 'approved'
            override_request.status = 'approved'
            override_request.save()

            student = override_request.student
            course = override_request.course

            # Enroll the student if not already enrolled
            if not Enrollment.objects.filter(student=student, course=course).exists():
                Enrollment.objects.create(
                    student=student,
                    course=course,
                    date_enrolled=date.today()
                )

            # Remove from waitlist if present
            WaitlistEntry.objects.filter(student=student, course=course).delete()

            message = 'Request accepted and student enrolled successfully.'

        # Reload pending requests
        pending_requests = OverrideRequest.objects.filter(status='pending')
        return render(request, 'admin_enrollment_manager.html', {
            'requests': pending_requests,
            'message': message
        })

class AdminStudentManagerView(View):
    def get(self, request):
        # name = request.session.get('name')
        # role = request.session.get('role')
        name = request.session.get('name')
        role = request.session.get('role')
        if not name or role != 'administrator':
            return redirect('login')

        students = MyUser.objects.filter(role='student')
        return render(request, 'admin_student_manager.html', {'students' : students})
    def post(self, request):
        student_id = request.POST.get('student_id')
        student = MyUser.objects.filter(id=student_id).first()

        all_enrollments = Enrollment.objects.filter(student=student)

        today = date.today()
        cutoff = today - timedelta(days=119)

        current_enrollments = all_enrollments.filter(date_enrolled__gte=cutoff)
        past_enrollments = all_enrollments.filter(date_enrolled__lt=cutoff)

        return render(request, 'student_enrollment_history.html', {
            'student': student,
            'current_enrollments': current_enrollments,
            'past_enrollments': past_enrollments
        })

# will work alongside AdminStudentManagerView
class AdminEnrollmentHistoryView(View):
    def get(self, request):
        name = request.session.get('name')
        role = request.session.get('role')
        if not name or role != 'administrator':
            return redirect('login')

        return render(request, 'student_enrollment_history.html')
    def post(self, request):
        # Case: Button clicked on enrollment history page
        student_id = request.POST.get('student_id')
        action = request.POST.get('action')


        if not student_id:
            return redirect('admin_student_manager')

        student = MyUser.objects.filter(id=student_id).first()

        if not student:
            return redirect('admin_student_manager')

        if action == 'Drop':
            enrollment_id = request.POST.get('enrollment_id')
            enrollment = Enrollment.objects.filter(id=enrollment_id,student = student)
            enrollment.delete()

            all_enrollments = Enrollment.objects.filter(student=student)

            today = date.today()
            cutoff = today - timedelta(days=119)

            current_enrollments = all_enrollments.filter(date_enrolled__gte=cutoff)
            past_enrollments = all_enrollments.filter(date_enrolled__lt=cutoff)
            return render(request, 'student_enrollment_history.html', {
                'current_enrollments': current_enrollments,
            'past_enrollments': past_enrollments,
                'message': 'Enrollment dropped successfully.'})
        # Get all enrollments for the student
        enrollments = Enrollment.objects.filter(student=student)

        return render(request, 'admin_edit_enrollment.html', {
            'student': student,
            'enrollments': enrollments
        })

class EditEnrollmentView(View):
    def get(self, request):
        name = request.session.get('name')
        role = request.session.get('role')
        if not name or role != 'administrator':
            return redirect('login')

        return render(request, 'admin_edit_enrollment.html')
    def post(self, request):
        student_id = request.POST.get('student_id')
        action = request.POST.get('action')

        if not student_id:
            return redirect('admin_student_manager')

        student = MyUser.objects.filter(id=student_id).first()
        if not student:
            return redirect('admin_student_manager')

        if action == 'go_back':
            all_enrollments = Enrollment.objects.filter(student=student)

            today = date.today()
            cutoff = today - timedelta(days=119)

            current_enrollments = all_enrollments.filter(date_enrolled__gte=cutoff)
            past_enrollments = all_enrollments.filter(date_enrolled__lt=cutoff)
            return render(request, 'student_enrollment_history.html', {
                'student':student,'current_enrollments': current_enrollments,
                'past_enrollments': past_enrollments})

        # Check if form is trying to save edited data
        if any(key.startswith('grade_') or key.startswith('date_') for key in request.POST):
            # Update enrollments
            for key in request.POST:
                if key.startswith('grade_'):
                    enrollment_id = key.split('_')[1]
                    grade = request.POST.get(f'grade_{enrollment_id}')
                    date_str = request.POST.get(f'date_{enrollment_id}')
                    try:
                        enrollment = Enrollment.objects.get(id=enrollment_id)
                        enrollment.final_grade = grade or None
                        if date_str:
                            enrollment.date_enrolled = datetime.strptime(date_str, '%Y-%m-%d').date()
                        enrollment.save()
                    except Enrollment.DoesNotExist:
                        continue

            # After saving, render back to enrollment history

            all_enrollments = Enrollment.objects.filter(student=student)

            today = date.today()
            cutoff = today - timedelta(days=119)

            current_enrollments = all_enrollments.filter(date_enrolled__gte=cutoff)
            past_enrollments = all_enrollments.filter(date_enrolled__lt=cutoff)

            return render(request, 'student_enrollment_history.html', {
                'student': student,
                'current_enrollments': current_enrollments,
                'past_enrollments': past_enrollments
            })

        # If just clicking "Edit Enrollments", show the edit form
        enrollments = Enrollment.objects.filter(student=student)
        return render(request, 'admin_edit_enrollment.html', {
            'student': student,
            'enrollments': enrollments
        })

class AdminStudentEditView(View):
    def get(self, request):
        name = request.session.get('name')
        role = request.session.get('role')
        if not name or role != 'administrator':
            return redirect('login')

        return render(request, 'admin_student_acct_edit.html')

    def post(self, request):
        student_id = request.POST.get('student_id')
        student = MyUser.objects.filter(id=student_id).first()

        if not student:
            return redirect('admin_student_manager')

        # If the user submitted the edit form with changes
        if 'name' in request.POST and 'email' in request.POST:
            student.name = request.POST.get('name')
            student.email = request.POST.get('email')
            student.password = request.POST.get('password')
            student.save()
            students = MyUser.objects.filter(role='student')
            return render(request, 'admin_student_manager.html', {'students': students})  # back to the student list

        # Otherwise, just show the edit form
        return render(request, 'admin_student_acct_edit.html', {
            'student': student
        })

class EnrollmentGeneratorView(View):
    def get(self, request):
        name = request.session.get('name')
        role = request.session.get('role')
        if not name or role != 'administrator':
            return redirect('login')

        total_enrollments = Enrollment.objects.count()
        total_students = MyUser.objects.filter(role='student').count()
        top_course = Course.objects.annotate(num_students=Count('enrollments')) \
            .order_by('-num_students') \
            .first()
        enrollments_by_course = Course.objects.annotate(num_enrollments=Count('enrollments')).order_by(
            '-num_enrollments')
        enrollments_by_month = (
            Enrollment.objects
            .extra(select={'month': "strftime('%%Y-%%m', date_enrolled)"})
            .values('month')
            .annotate(total=Count('id'))
            .order_by('month')
        )
        return render(request, 'enrollment_report_generator.html',
                      {'total_enrollments': total_enrollments,
                      'total_students': total_students,
                       'top_course': top_course,
                       'enrollments_by_course': enrollments_by_course,
                       'enrollments_by_month': enrollments_by_month})
    def post(self, request):
        return render(request, 'enrollment_report_generator.html')

class CourseCatalogView(View):
    def get(self, request):
        name = request.session.get('name')
        role = request.session.get('role')
        if not name or role != 'student':
            return redirect('login')

        courses = Course.objects.all()
        student = MyUser.objects.filter(name=name).first()
        enrollments = Enrollment.objects.filter(student=student)
        return render(request, 'course_catalog.html', {
            'courses': courses,
            'name': name,
            'role': role,
        'enrollments': enrollments})

    def post(self, request):
        name = request.session.get('name')
        role = request.session.get('role')
        action = request.POST.get('action')

        if not name or role != 'student':
            return redirect('login')

        course_id = request.POST.get('course_id')
        student = MyUser.objects.filter(name=name).first()
        course = Course.objects.filter(id=course_id).first()

        # Handle course drop
        if action == 'drop':
            Enrollment.objects.filter(student=student, course=course).delete()
            message = f"You have been dropped from {course.name}."

            # Auto-enroll next waitlisted student
            next_waitlisted = WaitlistEntry.objects.filter(course=course).order_by('timestamp').first()
            if next_waitlisted:
                Enrollment.objects.create(
                    student=next_waitlisted.student,
                    course=course,
                    date_enrolled=date.today()
                )
                next_waitlisted.delete()
                message += f" {next_waitlisted.student.name} has been auto-enrolled from the waitlist."

            courses = Course.objects.all()
            enrollments = Enrollment.objects.filter(student=student)
            return render(request, 'course_catalog.html', {
                'message': message,
                'courses': courses,
                'enrollments': enrollments
            })

        # Prevent duplicate enrollment
        if Enrollment.objects.filter(student=student, course=course).exists():
            message = f"Oops! You're already enrolled in {course.name}."
            courses = Course.objects.all()
            enrollments = Enrollment.objects.filter(student=student)
            return render(request, 'course_catalog.html', {
                'message': message,
                'courses': courses,
                'enrollments': enrollments
            })

        # Prerequisite completion check (must be enrolled for 119+ days)
        prereqs = course.prerequisites.all()
        cutoff_date = date.today() - timedelta(days=119)
        completed_prereq_ids = Enrollment.objects.filter(
            student=student,
            date_enrolled__lte=cutoff_date
        ).values_list('course_id', flat=True)
        missing_prereqs = prereqs.exclude(id__in=completed_prereq_ids)

        if missing_prereqs.exists():
            missing_titles = ", ".join([p.title for p in missing_prereqs])
            message = (
                f"Oops! You must complete all prerequisites for {course.name} at least 119 days before enrolling. "
                f"Missing or too recent: {missing_titles}."
            )
            courses = Course.objects.all()
            enrollments = Enrollment.objects.filter(student=student)
            return render(request, 'course_catalog.html', {
                'message': message,
                'courses': courses,
                'enrollments': enrollments
            })

        # Seat limit check
        current_enrollment_count = course.enrollments.count()
        if current_enrollment_count >= course.seat_limit:
            if course.waitlist_enabled:
                already_waitlisted = WaitlistEntry.objects.filter(student=student, course=course).exists()
                if not already_waitlisted:
                    WaitlistEntry.objects.create(student=student, course=course)
                    message = f"{course.name} is full. You have been added to the waitlist."
                else:
                    message = f"You are already on the waitlist for {course.name}."
            else:
                message = f"{course.name} is full, and this course does not support waitlisting."

            courses = Course.objects.all()
            enrollments = Enrollment.objects.filter(student=student)
            return render(request, 'course_catalog.html', {
                'message': message,
                'courses': courses,
                'enrollments': enrollments
            })

        # All checks passed — enroll the student
        Enrollment.objects.create(
            student=student,
            course=course,
            date_enrolled=date.today()
        )
        message = f"🎉 You have successfully enrolled in {course.name}!"

        courses = Course.objects.all()
        enrollments = Enrollment.objects.filter(student=student)
        return render(request, 'course_catalog.html', {
            'message': message,
            'courses': courses,
            'enrollments': enrollments
        })

class SignupView(View):
    def get(self, request):
        return render(request, 'signup.html')

    def post(self, request):
        full_name = request.POST.get('fullName')
        name     = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        role     = request.POST.get('role')

        if MyUser.objects.filter(name=name).exists():
            return render(request, 'signup.html', {
                'message': 'That username is already taken.'
            })

        user = MyUser.objects.create(fullName=full_name, name=name, password=password, email=email,role=role)
        request.session['user_id'] = user.id
        request.session['name']    = user.name
        request.session['role']    = user.role

        if role == 'student':
            return redirect('student_dashboard')
        elif role == 'instructor':
            return redirect('instructor_dashboard')
        else:  # administrator
            return redirect('admin_dashboard')

class GradeEntryView(View):
    def get(self, request, course_id):
        course      = Course.objects.get(id=course_id)
        enrollments = Enrollment.objects.filter(course=course)
        return render(request, 'grade_entry.html', {
            'course': course,
            'enrollments': enrollments
        })

    def post(self, request, course_id):
        eid = request.POST['enrollment_id']
        g, _ = Grade.objects.update_or_create(
            enrollment=Enrollment.objects.get(id=eid),
            assignment_name=request.POST['assignment'],
            defaults={
                'score': request.POST['score'],
                'feedback': request.POST.get('feedback','')
            }
        )
        return redirect('grade-entry', course_id=course_id)


class OfficeHourSlotCreateView(View):
    def get(self, request):
        return render(request, 'slot_form.html')

    def post(self, request):
        instructor = MyUser.objects.get(id=request.session['user_id'])
        OfficeHourSlot.objects.create(
            instructor=instructor,
            start_time=request.POST['start_time'],
            end_time=request.POST['end_time']
        )
        return redirect('office-hours')


class OfficeHourListView(View):
    def get(self, request):
        slots = OfficeHourSlot.objects.filter(
            instructor__id=request.session['user_id']
        )
        return render(request, 'office_hours.html', {'slots': slots})


class BookOfficeHourSlotView(View):
    def post(self, request, slot_id):
        student = MyUser.objects.get(id=request.session['user_id'])
        OfficeHourBooking.objects.create(
            slot=OfficeHourSlot.objects.get(id=slot_id),
            student=student
        )
        return redirect('student')
