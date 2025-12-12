from django.contrib import admin
from .models import (
    ReportDeadlineSetting, ReportSubmission, ReportFile,
    SubmissionReminder, UserNotification
)

@admin.register(ReportDeadlineSetting)
class ReportDeadlineAdmin(admin.ModelAdmin):
    list_display = ("title", "department", "start_date", "deadline_date", "created_at")
    list_filter = ("department",)

@admin.register(ReportSubmission)
class ReportSubmissionAdmin(admin.ModelAdmin):
    list_display = ("deadline", "user", "status", "is_submitted", "submitted_at")
    list_filter = ("status", "deadline__department")

@admin.register(ReportFile)
class ReportFileAdmin(admin.ModelAdmin):
    list_display = ("submission", "original_filename", "uploaded_at")
    readonly_fields = ("uploaded_at",)

admin.site.register(SubmissionReminder)
admin.site.register(UserNotification)
