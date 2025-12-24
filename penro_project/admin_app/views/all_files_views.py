from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db.models import Q

from accounts.models import (
    WorkItemAttachment,
    Team,
    WorkCycle,
)

@staff_member_required
def all_files_uploaded(request):
    """
    Admin view: list all uploaded files with combined filters.
    Year is derived from WorkCycle.due_at.year (NOT uploaded_at).
    """

    # =====================================================
    # BASE QUERYSET
    # =====================================================
    qs = (
        WorkItemAttachment.objects
        .select_related(
            "uploaded_by",
            "work_item",
            "work_item__workcycle",
            "folder",
        )
        .order_by("-uploaded_at")
    )

    # =====================================================
    # ACTIVE FILTER VALUES
    # =====================================================
    year = request.GET.get("year")
    attachment_type = request.GET.get("type")
    division = request.GET.get("division")
    service = request.GET.get("service")
    unit = request.GET.get("unit")

    # =====================================================
    # APPLY FILTERS
    # =====================================================

    # ✅ YEAR — based on WorkCycle, NOT upload date
    if year:
        qs = qs.filter(
            work_item__workcycle__due_at__year=year
        )

    if attachment_type:
        qs = qs.filter(
            attachment_type=attachment_type
        )

    # Folder-based org filters
    if division:
        qs = qs.filter(
            folder__parent__parent__name=division
        )

    if service:
        qs = qs.filter(
            folder__parent__name=service
        )

    if unit:
        qs = qs.filter(
            folder__name=unit
        )

    # =====================================================
    # TABLE DATA (flattened, template-friendly)
    # =====================================================
    files = []

    for a in qs:
        folder = a.folder

        files.append({
            "name": a.file.name.replace("work_items/", ""),
            "type": a.get_attachment_type_display(),
            "workcycle": (
                a.work_item.workcycle.title
                if a.work_item and a.work_item.workcycle
                else None
            ),
            "division": folder.parent.parent.name if folder and folder.parent and folder.parent.parent else None,
            "unit": folder.name if folder else None,
            "uploaded_by": a.uploaded_by,
            "uploaded_at": a.uploaded_at,
            "file_url": a.file.url,
        })

    # =====================================================
    # FILTER OPTIONS (DROPDOWNS)
    # =====================================================

    filters = {
        # DISTINCT years from WorkCycle
        "years": (
            WorkCycle.objects
            .values_list("due_at__year", flat=True)
            .distinct()
            .order_by("-due_at__year")
        ),

        "attachment_types": WorkItemAttachment.ATTACHMENT_TYPE_CHOICES,

        "divisions": (
            Team.objects
            .filter(team_type=Team.TeamType.DIVISION)
            .values_list("name", flat=True)
            .order_by("name")
        ),

        "services": (
            Team.objects
            .filter(team_type=Team.TeamType.SERVICE)
            .values_list("name", flat=True)
            .order_by("name")
        ),

        "units": (
            Team.objects
            .filter(team_type=Team.TeamType.UNIT)
            .values_list("name", flat=True)
            .order_by("name")
        ),
    }

    # =====================================================
    # CONTEXT
    # =====================================================
    return render(
        request,
        "admin/page/all_files_uploaded.html",
        {
            "files": files,
            "total_files": qs.count(),

            "filters": filters,
            "active": {
                "year": year,
                "type": attachment_type,
                "division": division,
                "service": service,
                "unit": unit,
            },
        }
    )
