from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

from accounts.models import WorkItem, WorkItemMessage

from ..services.work_item_service import (
    update_work_item_status,
    submit_work_item,
    add_attachment_to_work_item,
    update_work_item_context,
)

# ============================================================
# WORK ITEMS LIST
# ============================================================

@login_required
def user_work_items(request):
    """
    List ALL work items assigned to the user.
    Inactive ones remain visible but marked.
    """
    work_items = (
        WorkItem.objects
        .select_related("workcycle")
        .filter(owner=request.user)
        .order_by("-is_active", "workcycle__due_at")
    )

    return render(
        request,
        "user/page/work_items.html",
        {"work_items": work_items}
    )


# ============================================================
# WORK ITEM DETAIL
# ============================================================

@login_required
def user_work_item_detail(request, item_id):
    work_item = get_object_or_404(
        WorkItem,
        id=item_id,
        owner=request.user,
        is_active=True
    )

    if request.method == "POST":
        action = request.POST.get("action")

        try:
            if action == "update_status":
                update_work_item_status(
                    work_item,
                    request.POST.get("status")
                )
                messages.success(request, "Status updated.")

            elif action == "update_context":
                update_work_item_context(
                    work_item=work_item,
                    label=request.POST.get("status_label", "").strip(),
                    message=request.POST.get("message", "").strip(),
                )
                messages.success(request, "Notes updated.")

            elif action == "submit":
                submit_work_item(
                    work_item=work_item,
                    user=request.user
                )
                messages.success(request, "Work item submitted successfully.")

            return redirect(
                "user_app:work-item-detail",
                item_id=work_item.id
            )

        except Exception as e:
            messages.error(request, str(e))

    # ✅ ADD THIS
    attachments = work_item.attachments.all()

    attachment_types = [
        ("matrix_a", "Monthly Report Form – Matrix A"),
        ("matrix_b", "Monthly Report Form – Matrix B"),
        ("mov", "Means of Verification (MOV)"),
    ]

    uploaded_types = set(
        work_item.attachments.values_list(
            "attachment_type",
            flat=True
        )
    )

    return render(
        request,
        "user/page/work_item_detail.html",
        {
            "work_item": work_item,
            "attachments": attachments,   # 👈 REQUIRED
            "can_edit": work_item.status != "done",
            "status_choices": WorkItem._meta.get_field("status").choices,
            "attachment_types": attachment_types,
            "uploaded_types": uploaded_types,
        }
    )


# ============================================================
# WORK ITEM ATTACHMENTS (NO BREADCRUMBS)
# ============================================================

@login_required
def user_work_item_attachments(request, item_id):
    work_item = get_object_or_404(
        WorkItem,
        id=item_id,
        owner=request.user
    )

    attachment_type = request.GET.get("type")

    TYPE_MAP = {
        "matrix_a": "Monthly Report Form – Matrix A",
        "matrix_b": "Monthly Report Form – Matrix B",
        "mov": "Means of Verification (MOV)",
    }

    if attachment_type not in TYPE_MAP:
        messages.error(request, "Invalid attachment type.")
        return redirect(
            "user_app:work-item-detail",
            item_id=work_item.id
        )

    # ================= UPLOAD =================
    if request.method == "POST":
        try:
            files = request.FILES.getlist("attachments")

            add_attachment_to_work_item(
                work_item=work_item,
                files=files,
                attachment_type=attachment_type,
                user=request.user
            )

            messages.success(request, "Attachment uploaded.")
            return redirect(f"{request.path}?type={attachment_type}")

        except Exception as e:
            messages.error(request, str(e))

    # ================= FETCH ATTACHMENTS =================
    attachments = (
        work_item.attachments
        .filter(attachment_type=attachment_type)
        .order_by("uploaded_at")
    )

    return render(
        request,
        "user/page/work_item_attachments.html",
        {
            "work_item": work_item,
            "attachments": attachments,
            "attachment_type": attachment_type,
            "attachment_label": TYPE_MAP[attachment_type],
        }
    )


# ============================================================
# WORK ITEM COMMENTS
# ============================================================

@login_required
def user_work_item_comments(request, item_id):
    work_item = get_object_or_404(
        WorkItem,
        id=item_id,
        owner=request.user,
        is_active=True
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
            messages.success(request, "Comment posted.")
            return redirect(
                "user_app:work-item-comments",
                item_id=work_item.id
            )

    messages_qs = work_item.messages.select_related("sender")

    return render(
        request,
        "user/page/work_item_comments.html",
        {
            "work_item": work_item,
            "messages": messages_qs,
        }
    )
