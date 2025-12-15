from django.shortcuts import get_object_or_404, render, redirect
from accounts.models import WorkItem

def review_work_item(request, item_id):
    work_item = get_object_or_404(
        WorkItem.objects.select_related("owner", "workcycle").prefetch_related("attachments"),
        id=item_id,
        status="done"
    )

    if request.method == "POST" and request.POST.get("action") == "update_review":
        decision = request.POST.get("review_decision")
        if decision in {"pending", "approved", "revision"}:
            work_item.review_decision = decision
            work_item.save(update_fields=["review_decision"])

        return redirect("admin_app:work-item-review", item_id=item_id)

    return render(
        request,
        "admin/page/review_work_item.html",
        {
            "work_item": work_item,
        }
    )
