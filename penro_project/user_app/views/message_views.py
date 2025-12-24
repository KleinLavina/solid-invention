from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages

from accounts.models import WorkItem, WorkItemMessage


from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.clickjacking import xframe_options_exempt

@login_required
@xframe_options_exempt
def user_work_item_discussion(request, item_id):
    work_item = get_object_or_404(
        WorkItem.objects.select_related("owner", "workcycle"),
        id=item_id
    )

    if request.method == "POST":
        text = request.POST.get("message", "").strip()
        if text:
            WorkItemMessage.objects.create(
                work_item=work_item,
                sender=request.user,
                sender_role=request.user.login_role,
                message=text
            )
        return redirect("user_app:work-item-discussion", item_id=work_item.id)

    messages_qs = (
        work_item.messages
        .select_related("sender")
        .order_by("created_at")
    )

    return render(
        request,
        "user/page/work_item_discussion.html",
        {
            "work_item": work_item,
            "messages": messages_qs,
        }
    )
