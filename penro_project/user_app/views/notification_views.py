from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.core.paginator import Paginator

from notifications.models import Notification


@login_required
def user_notifications(request):
    # Extra safety: prevent admins from using user UI
    if request.user.login_role != "user":
        return render(request, "403.html", status=403)

    notifications = (
        Notification.objects
        .filter(recipient=request.user)
        .select_related("work_item")
        .order_by("-created_at")
    )

    paginator = Paginator(notifications, 15)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "user/page/notifications.html",
        {
            "page_obj": page_obj,
        }
    )
