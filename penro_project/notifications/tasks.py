from datetime import timedelta
from celery import shared_task
from django.utils import timezone

from notifications.models import Notification
from accounts.models import WorkItem, WorkCycle, User


# =====================================================
# TASK 1: DEADLINE NEAR (USER)
# =====================================================
@shared_task
def remind_deadline_near(days_before=3):
    now = timezone.now()
    target_date = (now + timedelta(days=days_before)).date()

    work_items = (
        WorkItem.objects
        .filter(
            is_active=True,
            status__in=["not_started", "working_on_it"],
            workcycle__due_at__date=target_date,
        )
        .select_related("owner", "workcycle")
    )

    for item in work_items:
        Notification.objects.get_or_create(
            recipient=item.owner,
            notif_type="reminder",
            work_item=item,
            defaults={
                "title": "Deadline Approaching",
                "message": (
                    f"Your work for '{item.workcycle.title}' "
                    f"is due on {item.workcycle.due_at:%b %d, %Y}."
                ),
            },
        )


# =====================================================
# TASK 2: MISSED DEADLINE (ADMIN)
# =====================================================
@shared_task
def notify_admin_missed_deadline():
    now = timezone.now()

    overdue_items = (
        WorkItem.objects
        .filter(
            is_active=True,
            status__in=["not_started", "working_on_it"],
            workcycle__due_at__lt=now,
        )
        .select_related("owner", "workcycle")
    )

    admins = User.objects.filter(login_role="admin")

    for item in overdue_items:
        for admin in admins:
            Notification.objects.get_or_create(
                recipient=admin,
                notif_type="reminder",
                work_item=item,
                defaults={
                    "title": "Missed Deadline",
                    "message": (
                        f"{item.owner.get_full_name()} missed the deadline "
                        f"for '{item.workcycle.title}'."
                    ),
                },
            )


# =====================================================
# TASK 3: AUTO CLOSE COMPLETED CYCLES
# =====================================================
@shared_task
def auto_close_completed_cycles():
    active_cycles = (
        WorkCycle.objects
        .filter(is_active=True)
        .prefetch_related("work_items__owner")
    )

    for cycle in active_cycles:
        total = cycle.work_items.count()
        done = cycle.work_items.filter(status="done").count()

        if total > 0 and total == done:
            cycle.is_active = False
            cycle.save(update_fields=["is_active"])

            for item in cycle.work_items.all():
                Notification.objects.create(
                    recipient=item.owner,
                    notif_type="system",
                    title="Work Cycle Completed",
                    message=f"The cycle '{cycle.title}' is now completed.",
                )
