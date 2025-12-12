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
        return  # no employees in department → no need to continue

    #
    # ============================================================
    # 1️⃣ CREATE SUBMISSION RECORD FOR EACH WORKER (AUTO STATUS)
    # ============================================================
    #
    submission_objects = []

    for user in workers:
        # Determine initial status
        if today < instance.start_date:
            status = "pending"
        elif instance.start_date <= today <= instance.deadline_date:
            status = "in_progress"
        else:
            status = "late_overdue"

        submission_objects.append(
            ReportSubmission(
                deadline=instance,   # <- use 'deadline' (new field name)
                user=user,
                status=status
            )
        )

    ReportSubmission.objects.bulk_create(submission_objects)

    #
    # ============================================================
    # 2️⃣ CREATE REMINDERS (BEFORE DEADLINE + ON DEADLINE)
    # ============================================================
    #
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
        reminder_objects.append(
            SubmissionReminder(
                deadline=instance,   # <- use 'deadline' (new field name)
                user=user,
                reminder_date=reminder_before
            )
        )
        reminder_objects.append(
            SubmissionReminder(
                deadline=instance,
                user=user,
                reminder_date=reminder_deadline_day
            )
        )

    SubmissionReminder.objects.bulk_create(reminder_objects)

    #
    # ============================================================
    # 3️⃣ OPTIONAL: CREATE START-DATE REMINDER
    # ============================================================
    #
    start_date_reminder_time = timezone.make_aware(
        datetime.combine(instance.start_date, datetime.min.time())
    )

    start_reminders = [
        SubmissionReminder(
            deadline=instance,   # <- use 'deadline'
            user=user,
            reminder_date=start_date_reminder_time
        )
        for user in workers
    ]
    SubmissionReminder.objects.bulk_create(start_reminders)

    #
    # ============================================================
    # 4️⃣ SEND UserNotification: NEW DEADLINE ASSIGNED
    # ============================================================
    #
    for user in workers:
        UserNotification.objects.create(
            user=user,
            submission=None,   # <- use 'submission' (new field name). None because this is not tied to a submission yet.
            title="New Report Deadline Assigned",
            message=(
                f"A new reporting requirement titled '{instance.title}' "
                f"has been assigned to your department.\n"
                f"Start Date: {instance.start_date}\n"
                f"Deadline: {instance.deadline_date}"
            )
        )
