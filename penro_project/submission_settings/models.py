from datetime import date
from django.utils import timezone
from django.db import models
from django.core.exceptions import ValidationError

from accounts.models import Department, User


# -------------------------
# Validators
# -------------------------
def validate_file_size(file):
    max_mb = 20
    if file.size > max_mb * 1024 * 1024:
        raise ValidationError(f"File too large. Max size is {max_mb} MB.")


def validate_file_extension(file):
    valid_extensions = [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".csv", ".txt", ".zip"]
    name = file.name.lower()
    if not any(name.endswith(ext) for ext in valid_extensions):
        raise ValidationError("Unsupported file type.")


# -------------------------
# Deadline
# -------------------------
class ReportDeadlineSetting(models.Model):
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name="report_deadlines"
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    start_date = models.DateField()
    deadline_date = models.DateField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.department.name}"


# -------------------------
# Submission
# -------------------------
class ReportSubmission(models.Model):

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("overdue", "Overdue"),
        ("late", "Late"),
        ("complete", "Complete"),
    ]

    deadline = models.ForeignKey(
        ReportDeadlineSetting,
        on_delete=models.CASCADE,
        related_name="submissions"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="report_submissions"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    is_submitted = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(null=True, blank=True)

    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("deadline", "user")
        ordering = ("-created_at",)

    def mark_submitted(self):
        from .models import SubmissionReminder, UserNotification

        self.is_submitted = True
        self.submitted_at = timezone.now()

        if self.submitted_at.date() <= self.deadline.deadline_date:
            self.status = "complete"
        else:
            self.status = "late"

        self.save()

        SubmissionReminder.objects.filter(
            deadline=self.deadline,
            user=self.user,
            is_sent=False
        ).update(is_sent=True)

        UserNotification.objects.create(
            user=self.user,
            submission=self,
            title="Submission Completed 🎉",
            message=f"You submitted '{self.deadline.title}'."
        )
    
    def update_status_logic(self):
        """Auto-update status based on date rules and compute display values."""

        today = date.today()
        start = self.deadline.start_date
        due = self.deadline.deadline_date

        # -------------------------------------------------------------
        # 1. Pending — Start date not reached
        # -------------------------------------------------------------
        if today < start:
            self.status = "pending"
            return {
                "show_progress": False,
                "remaining_days": None,
                "lateness_days": 0,
                "progress_pct": 0,
                "late_pct": 0,
            }

        # -------------------------------------------------------------
        # 2. In Progress — Today is between start and deadline
        # -------------------------------------------------------------
        if start <= today <= due:

            # Automatically enter in_progress if not yet submitted
            if not self.is_submitted:
                self.status = "in_progress"

            remaining_days = (due - today).days
            total_days = max((due - start).days, 1)
            elapsed_days = (today - start).days
            progress_pct = int((elapsed_days / total_days) * 100)

            return {
                "show_progress": True,
                "remaining_days": remaining_days,
                "lateness_days": 0,
                "progress_pct": progress_pct,
                "late_pct": 0,
            }

        # -------------------------------------------------------------
        # 3. Today is past the deadline
        # -------------------------------------------------------------
        if today > due:

            lateness_days = (today - due).days

            # 3A. Overdue — NOT submitted at all
            if not self.is_submitted:
                self.status = "overdue"
                return {
                    "show_progress": False,   # ❌ No progress bar
                    "remaining_days": 0,
                    "lateness_days": lateness_days,
                    "progress_pct": 0,
                    "late_pct": 0,
                }

            # 3B. Late — submitted AFTER deadline
            if self.submitted_at and self.submitted_at.date() > due:
                self.status = "late"
                return {
                    "show_progress": True,     # ✔ Progress bar visible
                    "remaining_days": 0,
                    "lateness_days": lateness_days,
                    "progress_pct": 100,       # Green bar full
                    "late_pct": min(100, lateness_days * 10),  # Yellow overlay
                }

            # 3C. Completed before deadline
            self.status = "complete"
            return {
                "show_progress": True,
                "remaining_days": 0,
                "lateness_days": 0,
                "progress_pct": 100,
                "late_pct": 0,
            }

        # Safety fallback
        return {
            "show_progress": False,
            "remaining_days": None,
            "lateness_days": 0,
            "progress_pct": 0,
            "late_pct": 0,
        }



    def __str__(self):
        return f"{self.user} — {self.status}"


# -------------------------
# Files
# -------------------------
class ReportFile(models.Model):
    submission = models.ForeignKey(
        ReportSubmission,
        on_delete=models.CASCADE,
        related_name="files"
    )
    file = models.FileField(upload_to="report_files/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    original_filename = models.CharField(max_length=512, blank=True)

    def __str__(self):
        return f"File for {self.submission.user} - {self.submission.deadline.title}"



# -------------------------
# Reminders
# -------------------------
class SubmissionReminder(models.Model):
    deadline = models.ForeignKey(
        ReportDeadlineSetting,
        on_delete=models.CASCADE,
        related_name="reminders"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="submission_reminders"
    )

    reminder_date = models.DateTimeField()
    is_sent = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)  # <-- RESTORED

    def __str__(self):
        return f"Reminder for {self.user} - {self.deadline.title}"


# -------------------------
# Notifications
# -------------------------
class UserNotification(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    submission = models.ForeignKey(
        ReportSubmission,
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True
    )

    title = models.CharField(max_length=255)
    message = models.TextField()

    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username} - {self.title}"
