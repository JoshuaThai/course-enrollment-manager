from django.contrib import admin
from .views import LogoutView, AdminEnrollmentHistoryView, EditEnrollmentView, AdminStudentEditView
from django.urls import path

from .views import (
    LoginView, RedirectView, StudentView, InstructorView,
    SearchCoursesView, EnrollCourseView, DropCourseView,
    StudentCoursesView, RequestOverrideView, WaitListStatusView,
    ManageEnrollmentsView, ManageOverrideRequestsView,
    SendEmailView, EditCourseView, AdminView, AdminCourseView, AdminEnrollmentView, AdminStudentManagerView,
    EnrollmentGeneratorView, AdminEditCourseView, AdminAddCourseView, CourseCatalogView, SignupView, GradeEntryView,
    OfficeHourSlotCreateView, OfficeHourListView, BookOfficeHourSlotView
)

urlpatterns = [
    path('', LoginView.as_view(), name='login'),
    path('redirect/', RedirectView.as_view(), name='redirect'),
    path('student/', StudentView.as_view(), name='student_dashboard'),
    path('student/search/', SearchCoursesView.as_view(), name='search_courses'),
    path('student/enroll/<int:course_id>/', EnrollCourseView.as_view(), name='enroll_course'),
    path('student/drop/<int:course_id>/', DropCourseView.as_view(), name='drop_course'),
    path('student/request-override/<int:course_id>/', RequestOverrideView.as_view(), name='request_override'),
    path('student/waitlist/', WaitListStatusView.as_view(), name='waitlist_status'),
    path('instructor/', InstructorView.as_view(), name='instructor_dashboard'),
    path('student/courses/', StudentCoursesView.as_view(), name='student_courses'),
    path('administrator/', AdminView.as_view(), name='admin_dashboard'),

    path('logout/', LogoutView.as_view(), name='logout'),

    # admin external sites
    path('admin_course_manager/', AdminCourseView.as_view(), name='admin_course_manager'),
    path('admin_edit_course/', AdminEditCourseView.as_view(), name='admin_edit_course'),
    path('admin_enrollment_manager/', AdminEnrollmentView.as_view(), name='admin_enrollment_manager'),
    path('admin_student_manager/', AdminStudentManagerView.as_view(), name='admin_student_manager'),
    path('enrollment_report_generator/', EnrollmentGeneratorView.as_view(), name = 'enrollment_report_generator'),
    path('admin_add_course/', AdminAddCourseView.as_view(), name = 'admin_add_course'),
    path('student_enroll_history/', AdminEnrollmentHistoryView.as_view(), name = 'student_enrollment_history'),
    path('edit_enrollment/', EditEnrollmentView.as_view(), name = 'admin_edit_enrollment'),
    path('admin_student_acct_edit', AdminStudentEditView.as_view(), name = 'admin_student_acct_edit'),
    path('student/coursecatalog/', CourseCatalogView.as_view() ,name='course_catalog'),
    path('student/', StudentView.as_view(), name='student'),
]

# Instructor features
urlpatterns += [
    path('instructor/enrollments/', ManageEnrollmentsView.as_view(), name='instructor_enrollments'),
    path('instructor/requests/', ManageOverrideRequestsView.as_view(), name='instructor_requests'),
    path('instructor/email/', SendEmailView.as_view(), name='instructor_email'),
    path('instructor/course/<int:course_id>/edit/', EditCourseView.as_view(), name='edit_course'),
    path('signup/', SignupView.as_view(), name='signup'),
    path('course/<int:course_id>/grades/', GradeEntryView.as_view(), name='grade-entry'),
    path('office-hours/', OfficeHourListView.as_view(), name='office-hours'),
    path('office-hours/new/', OfficeHourSlotCreateView.as_view(), name='office-hours-create'),
    path('office-hours/<int:slot_id>/book/', BookOfficeHourSlotView.as_view(), name='office-hours-book'),
]
