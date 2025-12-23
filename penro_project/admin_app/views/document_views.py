from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.utils.timezone import now

from accounts.models import WorkItemAttachment


@staff_member_required
def admin_documents(request):
    current_year = now().year

    total_files = WorkItemAttachment.objects.count()
    files_this_year = WorkItemAttachment.objects.filter(
        uploaded_at__year=current_year
    ).count()

    years = (
        WorkItemAttachment.objects
        .values_list("uploaded_at__year", flat=True)
        .distinct()
        .order_by("-uploaded_at__year")
    )

    return render(
        request,
        "admin/page/documents_dashboard.html",
        {
            "total_files": total_files,
            "files_this_year": files_this_year,
            "years": years,
            "now": now(),  # 👈 required by template
        }
    )
