from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

from accounts.models import WorkItemAttachment


from accounts.models import WorkItemAttachment, DocumentFolder


@staff_member_required
def admin_file_manager(request, folder_id=None):
    current_folder = None

    if folder_id:
        current_folder = DocumentFolder.objects.get(id=folder_id)
        folders = current_folder.children.all()
        attachments = current_folder.files.select_related(
            "work_item", "uploaded_by"
        )
    else:
        folders = DocumentFolder.objects.filter(parent__isnull=True)
        attachments = WorkItemAttachment.objects.filter(
            folder__isnull=True
        ).select_related("work_item", "uploaded_by")

    return render(
        request,
        "admin/page/file_manager.html",
        {
            "current_folder": current_folder,
            "folders": folders,
            "attachments": attachments,
        }
    )

from django.shortcuts import redirect
from accounts.models import DocumentFolder


@staff_member_required
def create_folder(request):
    if request.method == "POST":
        parent_id = request.POST.get("parent_id")
        name = request.POST.get("name")

        DocumentFolder.objects.create(
            name=name,
            parent_id=parent_id or None,
            created_by=request.user
        )

    return redirect("admin_app:file-manager")

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404

from accounts.models import WorkItemAttachment, DocumentFolder


@staff_member_required
@require_POST
def move_attachment(request):
    attachment_ids = request.POST.getlist("attachment_ids[]")
    folder_id = request.POST.get("folder_id")

    folder = None
    if folder_id:
        folder = get_object_or_404(DocumentFolder, id=folder_id)

    moved = []

    for aid in attachment_ids:
        attachment = get_object_or_404(WorkItemAttachment, id=aid)
        old_folder = attachment.folder_id

        attachment.folder = folder
        attachment.save(update_fields=["folder"])

        moved.append({
            "id": attachment.id,
            "old_folder": old_folder
        })

    return JsonResponse({
        "status": "ok",
        "moved": moved
    })

@staff_member_required
def admin_file_manager(request, folder_id=None):
    """
    Admin file manager.
    Always starts at ROOT folder.
    """

    if folder_id:
        current_folder = get_object_or_404(DocumentFolder, id=folder_id)
    else:
        # ROOT folder (must exist)
        current_folder = get_object_or_404(
            DocumentFolder,
            folder_type=DocumentFolder.FolderType.ROOT,
            parent__isnull=True
        )

    folders = current_folder.children.all()
    attachments = current_folder.files.select_related(
        "work_item", "uploaded_by"
    )

    return render(
        request,
        "admin/page/file_manager.html",
        {
            "current_folder": current_folder,
            "folders": folders,
            "attachments": attachments,
        }
    )

@staff_member_required
def create_folder(request):
    if request.method != "POST":
        return redirect("admin_app:file-manager")

    parent_id = request.POST.get("parent_id")
    name = request.POST.get("name", "").strip()

    if not name:
        return redirect("admin_app:file-manager")

    parent = None
    if parent_id:
        parent = get_object_or_404(DocumentFolder, id=parent_id)

    DocumentFolder.objects.create(
        name=name,
        parent=parent,
        folder_type=DocumentFolder.FolderType.ATTACHMENT,
        created_by=request.user,
        is_system_generated=False,
    )

    if parent:
        return redirect("admin_app:file-manager-folder", folder_id=parent.id)

    return redirect("admin_app:file-manager")

@staff_member_required
@require_POST
def move_attachment(request):
    attachment_ids = request.POST.getlist("attachment_ids[]")
    folder_id = request.POST.get("folder_id")

    target_folder = None
    if folder_id:
        target_folder = get_object_or_404(DocumentFolder, id=folder_id)

        # Enforce valid drop target
        if target_folder.folder_type != DocumentFolder.FolderType.ATTACHMENT:
            return JsonResponse(
                {"error": "Files can only be moved into attachment folders."},
                status=400
            )

    moved = []

    for attachment_id in attachment_ids:
        attachment = get_object_or_404(
            WorkItemAttachment,
            id=attachment_id
        )

        old_folder_id = attachment.folder_id
        attachment.folder = target_folder
        attachment.save(update_fields=["folder"])

        moved.append({
            "id": attachment.id,
            "old_folder": old_folder_id
        })

    return JsonResponse({
        "status": "ok",
        "moved": moved
    })
