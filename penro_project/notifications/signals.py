from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from accounts.models import WorkItem, WorkItemMessage
from .models import Notification

User = get_user_model()


# ============================
# CHAT MESSAGE NOTIFICATION
# ============================
@receiver(post_save, sender=WorkItemMessage)
def notify_chat_message(sender, instance, created, **kwargs):
    if not created:
        return

    work_item = instance.work_item

    # Notify the owner if someone else messaged
    if instance.sender != work_item.owner:
        Notification.objects.create(
            recipient=work_item.owner,
            notif_type="chat",
            title="New Message",
            message=instance.message[:200],
            work_item=work_item
        )


# ============================
# REVIEW DECISION NOTIFICATION
# ============================
@receiver(post_save, sender=WorkItem)
def notify_review_decision(sender, instance, created, **kwargs):
    if created:
        return

    if instance.review_decision in ("approved", "revision"):
        Notification.objects.create(
            recipient=instance.owner,
            notif_type="review",
            title="Review Update",
            message=f"Your work was marked as {instance.review_decision.upper()}",
            work_item=instance
        )


# ============================
# SUBMISSION NOTIFICATION
# ============================
@receiver(post_save, sender=WorkItem)
def notify_submission(sender, instance, created, **kwargs):
    if created:
        return

    if instance.status == "done" and instance.submitted_at:
        admins = User.objects.filter(login_role__in=("admin", "manager"))

        for admin in admins:
            Notification.objects.create(
                recipient=admin,
                notif_type="status",
                title="Work Submitted",
                message=f"{instance.owner} submitted {instance.workcycle.title}",
                work_item=instance
            )
