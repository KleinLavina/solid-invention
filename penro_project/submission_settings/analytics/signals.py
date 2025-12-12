# submission_settings/analytics/signals.py

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from submission_settings.models import (
    ReportSubmission,
    ReportDeadlineSetting,
    ReportFile,
)
from submission_settings.analytics.refresh import (
    refresh_deadline_analytics,
    refresh_user_analytics,
)


# ------------------------------------------------------------
# When a submission is created or updated, refresh all analytics
# ------------------------------------------------------------
@receiver(post_save, sender=ReportSubmission)
def on_submission_saved(sender, instance, **kwargs):
    deadline_id = instance.deadline_id
    user_id = instance.user_id

    # Refresh per-deadline analytics
    refresh_deadline_analytics(deadline_id, create_snapshot=False)

    # Refresh per-user analytics
    refresh_user_analytics(user_id)


# ------------------------------------------------------------
# When a submission is deleted (rare), refresh analytics
# ------------------------------------------------------------
@receiver(post_delete, sender=ReportSubmission)
def on_submission_deleted(sender, instance, **kwargs):
    refresh_deadline_analytics(instance.deadline_id, create_snapshot=False)
    refresh_user_analytics(instance.user_id)


# ------------------------------------------------------------
# When a file is uploaded, refresh associated user/deadline analytics
# ------------------------------------------------------------
@receiver(post_save, sender=ReportFile)
def on_file_uploaded(sender, instance, created, **kwargs):
    if not created:
        return

    submission = instance.submission

    # Update user analytics (files count, delay metrics)
    refresh_user_analytics(submission.user_id)

    # Update deadline analytics (file counts & avg file numbers)
    refresh_deadline_analytics(submission.deadline_id, create_snapshot=False)


# ------------------------------------------------------------
# When a new deadline is created, initialize analytics row
# ------------------------------------------------------------
@receiver(post_save, sender=ReportDeadlineSetting)
def on_deadline_created(sender, instance, created, **kwargs):
    if created:
        # Create baseline analytics snapshot
        refresh_deadline_analytics(instance.id, create_snapshot=True)
