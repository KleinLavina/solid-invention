from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q, F, ExpressionWrapper, FloatField
from django.db.models.functions import NullIf
from django.shortcuts import render

from accounts.models import WorkItem


@staff_member_required
def completed_work_summary(request):

    summary = (
        WorkItem.objects
        .filter(workcycle__is_active=True, is_active=True)
        .values(
            "workcycle_id",
            "workcycle__title",
            "workcycle__due_at",
        )
        .annotate(
            # TOTAL workers assigned
            total_workers=Count("id"),

            # DONE / SUBMITTED
            done_count=Count(
                "id",
                filter=Q(status="done")
            ),

            # REVIEW STATES (ONLY from DONE)
            pending_review_count=Count(
                "id",
                filter=Q(status="done", review_decision="pending")
            ),

            revision_count=Count(
                "id",
                filter=Q(status="done", review_decision="revision")
            ),

            approved_count=Count(
                "id",
                filter=Q(status="done", review_decision="approved")
            ),
        )
        .annotate(
            approval_pct=ExpressionWrapper(
                100.0 * F("approved_count") / NullIf(F("total_workers"), 0),
                output_field=FloatField()
            )
        )
        .order_by("workcycle__due_at")
    )

    return render(
        request,
        "admin/page/completed_work_summary.html",
        {"summary": summary}
    )
