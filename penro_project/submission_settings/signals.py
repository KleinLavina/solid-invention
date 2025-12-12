# submission_settings/signals.py
from datetime import datetime, timedelta
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import (
    ReportDeadlineSetting,
    ReportSubmission,
    SubmissionReminder,
    UserNotification,
)


@receiver(post_save, sender=ReportDeadlineSetting)
def create_status_and_reminders(sender, instance, created, **kwargs):
    if not created:
        return

    today = timezone.localdate()
    department = instance.department
    workers = list(department.users.all())

    if not workers:
        return

    # 1️⃣ CREATE submission records for every worker
    submission_objects = []

    for user in workers:
        if today < instance.start_date:
            status = "pending"
        elif instance.start_date <= today <= instance.deadline_date:
            status = "in_progress"
        else:
            status = "overdue"  # FIXED (valid choice)

        submission_objects.append(
            ReportSubmission(
                deadline=instance,
                user=user,
                status=status
            )
        )

    ReportSubmission.objects.bulk_create(submission_objects)

    # 2️⃣ CREATE reminder dates
    reminder_before_days = 3
    deadline = instance.deadline_date

    reminder_before = timezone.make_aware(
        datetime.combine(
            deadline - timedelta(days=reminder_before_days),
            datetime.min.time()
        )
    )

    reminder_deadline_day = timezone.make_aware(
        datetime.combine(deadline, datetime.min.time())
    )

    reminder_objects = []

    for user in workers:
        reminder_objects.extend([
            SubmissionReminder(
                deadline=instance,
                user=user,
                reminder_date=reminder_before
            ),
            SubmissionReminder(
                deadline=instance,
                user=user,
                reminder_date=reminder_deadline_day
            ),
        ])

    SubmissionReminder.objects.bulk_create(reminder_objects)

    # 3️⃣ ADD start-date reminder
    start_date_reminder_time = timezone.make_aware(
        datetime.combine(instance.start_date, datetime.min.time())
    )

    start_reminders = [
        SubmissionReminder(
            deadline=instance,
            user=user,
            reminder_date=start_date_reminder_time
        )
        for user in workers
    ]

    SubmissionReminder.objects.bulk_create(start_reminders)

    # 4️⃣ NOTIFY workers
    for user in workers:
        UserNotification.objects.create(
            user=user,
            submission=None,
            title="New Report Deadline Assigned",
            message=(
                f"A new reporting requirement titled '{instance.title}' has been assigned.\n"
                f"Start Date: {instance.start_date}\n"
                f"Deadline: {instance.deadline_date}"
            )
        )
