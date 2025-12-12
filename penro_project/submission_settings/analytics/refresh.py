# submission_settings/analytics/refresh.py

from django.db.models import Count, Q, Avg
from django.utils import timezone
from decimal import Decimal

from submission_settings.models import (
    ReportSubmission,
    ReportDeadlineSetting,
    ReportFile,
)
from submission_settings.analytics_models import (
    ReportAnalytics,
    DepartmentDeadlineAnalytics,
    UserSubmissionAnalytics,
    ReportAnalyticsSnapshot,
)


# ------------------------------------------------------------
# MAIN ENGINE — REFRESH ANALYTICS FOR DEADLINE
# ------------------------------------------------------------
def refresh_deadline_analytics(deadline_id, create_snapshot=True):
    deadline = ReportDeadlineSetting.objects.get(pk=deadline_id)

    submissions = ReportSubmission.objects.filter(deadline=deadline)
    total_workers = submissions.count()

    pending = submissions.filter(status="pending").count()
    in_prog = submissions.filter(status="in_progress").count()
    complete = submissions.filter(status="complete").count()
    late = submissions.filter(status="late").count()
    late_overdue = submissions.filter(status="late_overdue").count()

    total_files = ReportFile.objects.filter(submission__deadline=deadline).count()

    avg_files = (total_files / total_workers) if total_workers > 0 else 0.0

    completion_rate = round((complete / total_workers * 100), 2) if total_workers else 0
    late_rate = round((late + late_overdue) / total_workers * 100, 2) if total_workers else 0

    analytics, created = ReportAnalytics.objects.update_or_create(
        deadline=deadline,
        defaults={
            "department": deadline.department,
            "total_workers": total_workers,
            "pending_count": pending,
            "in_progress_count": in_prog,
            "complete_count": complete,
            "late_count": late,
            "late_overdue_count": late_overdue,
            "completion_rate": completion_rate,
            "late_rate": late_rate,
            "total_files": total_files,
            "avg_files_per_submission": round(avg_files, 2),
        }
    )

    # Create snapshot for historical charts
    if create_snapshot:
        ReportAnalyticsSnapshot.objects.create(
            analytics=analytics,
            complete_count=complete,
            pending_count=pending,
            late_count=late + late_overdue,
            completion_rate=completion_rate
        )

    # Refresh department-level analytics
    refresh_department_deadline_analytics(deadline)

    return analytics


# ------------------------------------------------------------
# PER-DEPARTMENT PER-DEADLINE ANALYTICS
# ------------------------------------------------------------
def refresh_department_deadline_analytics(deadline):
    department = deadline.department
    submissions = ReportSubmission.objects.filter(deadline=deadline)

    total = submissions.count()
    pending = submissions.filter(status="pending").count()
    complete = submissions.filter(status="complete").count()
    late = submissions.filter(Q(status="late") | Q(status="late_overdue")).count()

    completion_rate = round((complete / total) * 100, 2) if total else 0

    DepartmentDeadlineAnalytics.objects.update_or_create(
        deadline=deadline,
        department=department,
        defaults={
            "total_users": total,
            "pending": pending,
            "complete": complete,
            "late": late,
            "completion_rate": completion_rate,
        }
    )


# ------------------------------------------------------------
# PER USER ANALYTICS
# ------------------------------------------------------------
def refresh_user_analytics(user_id):
    submissions = ReportSubmission.objects.filter(user_id=user_id)
    files = ReportFile.objects.filter(submission__user_id=user_id)

    total = submissions.count()
    complete_on_time = submissions.filter(status="complete").count()
    late = submissions.filter(Q(status="late") | Q(status="late_overdue")).count()

    total_files = files.count()

    # calculate average submission delay (in hours)
    delays = []
    for s in submissions:
        if not s.submitted_at:
            continue
        deadline_time = timezone.datetime.combine(
            s.deadline.deadline_date,
            timezone.datetime.min.time(),
            tzinfo=timezone.get_current_timezone()
        )
        delay_hours = (s.submitted_at - deadline_time).total_seconds() / 3600
        delays.append(delay_hours)

    avg_delay = sum(delays) / len(delays) if delays else 0.0

    UserSubmissionAnalytics.objects.update_or_create(
        user_id=user_id,
        defaults={
            "total_submissions": total,
            "on_time_submissions": complete_on_time,
            "late_submissions": late,
            "average_submission_delay_hours": round(avg_delay, 2),
            "total_files_uploaded": total_files,
        }
    )
