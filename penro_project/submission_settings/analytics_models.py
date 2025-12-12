# submission_settings/analytics_models.py
from django.db import models
from django.utils import timezone
from accounts.models import Department, User
from .models import ReportDeadlineSetting, ReportSubmission, ReportFile

# ------------------------------------------------------------
# 1A — PER DEADLINE ANALYTICS
# ------------------------------------------------------------
class ReportAnalytics(models.Model):
    deadline = models.OneToOneField(
        ReportDeadlineSetting,
        on_delete=models.CASCADE,
        related_name="analytics"
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name="deadline_analytics"
    )

    # counts
    total_workers = models.PositiveIntegerField(default=0)
    pending_count = models.PositiveIntegerField(default=0)
    in_progress_count = models.PositiveIntegerField(default=0)
    complete_count = models.PositiveIntegerField(default=0)
    late_count = models.PositiveIntegerField(default=0)
    late_overdue_count = models.PositiveIntegerField(default=0)

    # percentages
    completion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    late_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    # file stats
    total_files = models.PositiveIntegerField(default=0)
    avg_files_per_submission = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    last_refreshed = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Analytics for {self.deadline.title}"


# ------------------------------------------------------------
# 1B — PER DEPARTMENT PER DEADLINE ANALYTICS
# ------------------------------------------------------------
class DepartmentDeadlineAnalytics(models.Model):
    deadline = models.ForeignKey(
        ReportDeadlineSetting,
        on_delete=models.CASCADE,
        related_name="department_analytics"
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name="analytics_by_deadline"
    )

    # counts
    total_users = models.PositiveIntegerField(default=0)
    complete = models.PositiveIntegerField(default=0)
    pending = models.PositiveIntegerField(default=0)
    late = models.PositiveIntegerField(default=0)

    completion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    last_refreshed = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("deadline", "department")

    def __str__(self):
        return f"{self.department.name} — {self.deadline.title}"


# ------------------------------------------------------------
# 1C — PER USER SUBMISSION HISTORY ANALYTICS
# ------------------------------------------------------------
class UserSubmissionAnalytics(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="submission_analytics"
    )

    total_submissions = models.PositiveIntegerField(default=0)

    # performance
    on_time_submissions = models.PositiveIntegerField(default=0)
    late_submissions = models.PositiveIntegerField(default=0)
    average_submission_delay_hours = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    total_files_uploaded = models.PositiveIntegerField(default=0)

    last_refreshed = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"User Analytics — {self.user.username}"


# ------------------------------------------------------------
# 1D — SNAPSHOTS FOR DAILY/WEEKLY HISTORICAL CHARTS
# ------------------------------------------------------------
class ReportAnalyticsSnapshot(models.Model):
    analytics = models.ForeignKey(
        ReportAnalytics,
        on_delete=models.CASCADE,
        related_name="snapshots"
    )

    timestamp = models.DateTimeField(default=timezone.now)

    # saved metrics for charts
    complete_count = models.PositiveIntegerField(default=0)
    pending_count = models.PositiveIntegerField(default=0)
    late_count = models.PositiveIntegerField(default=0)
    completion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    class Meta:
        ordering = ("-timestamp",)

    def __str__(self):
        return f"Snapshot for {self.analytics.deadline.title} @ {self.timestamp}"
