from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.core.paginator import Paginator

from notifications.models import Notification


@login_required
def admin_notifications(request):
    if request.user.login_role != "admin":
        return render(request, "403.html", status=403)

    qs = (
        Notification.objects
        .filter(recipient=request.user)
        .select_related("work_item")
        .order_by("-created_at")
    )

    paginator = Paginator(qs, 15)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "admin/page/notifications.html",
        {
            "page_obj": page_obj,
        }
    )
