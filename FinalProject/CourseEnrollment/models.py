from datetime import date
from typing import Any

from django.db import models
from django.utils import timezone

# Create your models here.
class MyUser(models.Model):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.enrolled_courses = None
    fullName = models.CharField(max_length=50, default="")
    name = models.CharField(max_length=20)
    password = models.CharField(max_length=20)
    role = models.CharField(max_length=20, default='student')
    # can be student, instructor, administrator or advisor
    email = models.EmailField(blank=True)  # email for communications
    # we need a model field that will handle the history enrollment of a students.
    # This model field will also include that courses a student is currently enrolled in.


class Course(models.Model):
    code = models.CharField(max_length=10, default = "0000", unique=True)
    title = models.CharField(max_length=100)
    syllabus = models.TextField(blank=True)
    meeting_times = models.CharField(max_length=100, blank=True)
    seat_limit = models.PositiveIntegerField(default=0)
    instructor = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='courses', default = "")
    # We also need a model field that will add prerequisites to the individual courses.
    prerequisites = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='required_for')
    waitlist_enabled = models.BooleanField(default=True)

    @property
    def name(self):
        return self.title

    def __str__(self):
        return f"{self.code}: {self.title}"


# used this to look at which classes a student is enrolled in.
class Enrollment(models.Model):
    student = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    date_enrolled = models.DateField(default=timezone.now)
    final_grade = models.CharField(max_length=3, blank=True, null=True, default="n/a")  # e.g. A, B+, C, etc.

    def __str__(self):
        return f"{self.student.name} enrolled in {self.course.code}"


class OverrideRequest(models.Model):
    student = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='override_requests', default = "")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='override_requests', default = "")
    reason = models.TextField()
    status = models.CharField(
        max_length=10,
        choices=[('pending', 'Pending'), ('approved', 'Approved'), ('denied', 'Denied')],
        default='pending'
    )

    def __str__(self):
        return f"OverrideRequest by {self.student.name} for {self.course.code} [{self.status}]"


class WaitlistEntry(models.Model):
    student = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='waitlist_entries')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='waitlist_entries')
    timestamp = models.DateTimeField(default = timezone.now)

    def __str__(self):
        return f"{self.student.name} on waitlist for {self.course.code}"

class Grade(models.Model):
    enrollment      = models.ForeignKey(Enrollment, on_delete=models.CASCADE)
    assignment_name = models.CharField(max_length=100)
    score           = models.DecimalField(max_digits=5, decimal_places=2)
    feedback        = models.TextField(blank=True)
    updated_at      = models.DateTimeField(auto_now=True)

class OfficeHourSlot(models.Model):
    instructor = models.ForeignKey(MyUser,
                                   limit_choices_to={'role':'instructor'},
                                   on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time   = models.DateTimeField()

class OfficeHourBooking(models.Model):
    slot    = models.ForeignKey(OfficeHourSlot, on_delete=models.CASCADE)
    student = models.ForeignKey(MyUser,
                                limit_choices_to={'role':'student'},
                                on_delete=models.CASCADE)
    booked_at = models.DateTimeField(auto_now_add=True)
