from django.contrib import admin
from .models import MyUser, Course, Enrollment, OverrideRequest, WaitlistEntry
# Register your models here.

admin.site.register(MyUser)
admin.site.register(Course)
admin.site.register(Enrollment)
admin.site.register(OverrideRequest)
admin.site.register(WaitlistEntry)