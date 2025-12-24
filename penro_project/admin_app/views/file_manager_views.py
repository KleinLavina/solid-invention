# file_manager_views.py

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError

from accounts.models import WorkItemAttachment
from structure.models import DocumentFolder


@staff_member_required
def admin_file_manager(request, folder_id=None):
    """
    Admin File Manager with deep breadcrumb navigation.
    """
    if folder_id:
        current_folder = get_object_or_404(DocumentFolder, id=folder_id)
    else:
        current_folder = get_object_or_404(
            DocumentFolder,
            folder_type=DocumentFolder.FolderType.ROOT,
            parent__isnull=True
        )

    breadcrumb = current_folder.get_path()
    folders = current_folder.children.all()
    attachments = current_folder.files.select_related(
        "work_item",
        "uploaded_by"
    )

    return render(
        request,
        "admin/page/file_manager.html",
        {
            "current_folder": current_folder,
            "breadcrumb": breadcrumb,
            "folders": folders,
            "attachments": attachments,
        }
    )


@staff_member_required
def create_folder(request):
    """
    Creates a user folder under the selected parent.
    Validation is handled by the model.
    """
    if request.method != "POST":
        return redirect("admin_app:file-manager")

    parent_id = request.POST.get("parent_id")
    name = request.POST.get("name", "").strip()

    if not name or not parent_id:
        return redirect("admin_app:file-manager")

    parent = get_object_or_404(DocumentFolder, id=parent_id)

    try:
        folder = DocumentFolder(
            name=name,
            parent=parent,
            folder_type=DocumentFolder.FolderType.ATTACHMENT,
            created_by=request.user,
            is_system_generated=False,
        )
        folder.save()
    except ValidationError as e:
        # In a real app, you'd want to pass this error to the template
        pass

    return redirect("admin_app:file-manager-folder", folder_id=parent.id)


@staff_member_required
@require_POST
def move_attachment(request):
    """
    Moves file attachments to a target folder.
    Returns specific error messages for invalid drops.
    """
    attachment_ids = request.POST.getlist("attachment_ids[]")
    folder_id = request.POST.get("folder_id")

    if not attachment_ids:
        return JsonResponse(
            {"status": "error", "message": "No files selected."},
            status=400
        )

    target_folder = get_object_or_404(DocumentFolder, id=folder_id)

    moved = []
    
    try:
        for attachment_id in attachment_ids:
            attachment = get_object_or_404(
                WorkItemAttachment,
                id=attachment_id
            )

            old_folder_id = attachment.folder_id
            attachment.folder = target_folder
            
            # This triggers clean() which validates the placement
            attachment.save()

            moved.append({
                "id": attachment.id,
                "old_folder": old_folder_id
            })

        return JsonResponse({
            "status": "success",
            "message": f"Moved {len(moved)} file(s) successfully.",
            "moved": moved
        })

    except ValidationError as e:
        # Extract the first error message
        error_msg = e.messages[0] if e.messages else "Invalid drop location."
        return JsonResponse(
            {"status": "error", "message": error_msg},
            status=400
        )
    except Exception as e:
        return JsonResponse(
            {"status": "error", "message": "An unexpected error occurred."},
            status=500
        )


@staff_member_required
@require_POST
def move_folder(request):
    """
    Moves user-created folders. System folders cannot be moved.
    """
    folder_id = request.POST.get("folder_id")
    target_folder_id = request.POST.get("target_folder_id")

    if not folder_id or not target_folder_id:
        return JsonResponse(
            {"status": "error", "message": "Missing folder IDs."},
            status=400
        )

    folder = get_object_or_404(DocumentFolder, id=folder_id)
    target_folder = get_object_or_404(DocumentFolder, id=target_folder_id)

    # Prevent moving system folders
    if folder.is_system_generated:
        return JsonResponse(
            {
                "status": "error",
                "message": "System-generated folders cannot be moved."
            },
            status=400
        )

    try:
        old_parent_id = folder.parent_id
        folder.parent = target_folder
        folder.save()  # This triggers validation

        return JsonResponse({
            "status": "success",
            "message": f"Folder '{folder.name}' moved successfully.",
            "folder_id": folder.id,
            "old_parent": old_parent_id
        })

    except ValidationError as e:
        error_msg = e.messages[0] if e.messages else "Invalid folder placement."
        return JsonResponse(
            {"status": "error", "message": error_msg},
            status=400
        )

# file_manager_views.py - ADD THESE NEW VIEWS

from django.http import FileResponse, Http404
import os

@staff_member_required
@require_POST
def rename_folder(request):
    """
    Renames a user-created folder.
    System folders cannot be renamed.
    """
    folder_id = request.POST.get("folder_id")
    new_name = request.POST.get("new_name", "").strip()
    
    if not folder_id or not new_name:
        return JsonResponse(
            {"status": "error", "message": "Invalid input."},
            status=400
        )
    
    folder = get_object_or_404(DocumentFolder, id=folder_id)
    
    if folder.is_system_generated:
        return JsonResponse(
            {"status": "error", "message": "System folders cannot be renamed."},
            status=400
        )
    
    try:
        old_name = folder.name
        folder.name = new_name
        folder.save()
        
        return JsonResponse({
            "status": "success",
            "message": f"Renamed '{old_name}' to '{new_name}'."
        })
    except ValidationError as e:
        error_msg = e.messages[0] if e.messages else "Invalid folder name."
        return JsonResponse(
            {"status": "error", "message": error_msg},
            status=400
        )


@staff_member_required
@require_POST
def delete_folder(request):
    """
    Deletes a user-created folder.
    System folders cannot be deleted.
    Folder must be empty to be deleted.
    """
    folder_id = request.POST.get("folder_id")
    
    if not folder_id:
        return JsonResponse(
            {"status": "error", "message": "Folder ID required."},
            status=400
        )
    
    folder = get_object_or_404(DocumentFolder, id=folder_id)
    
    if folder.is_system_generated:
        return JsonResponse(
            {"status": "error", "message": "System folders cannot be deleted."},
            status=400
        )
    
    # Check if folder has children or files
    if folder.children.exists():
        return JsonResponse(
            {"status": "error", "message": "Folder must be empty. Remove subfolders first."},
            status=400
        )
    
    if folder.files.exists():
        return JsonResponse(
            {"status": "error", "message": "Folder must be empty. Remove files first."},
            status=400
        )
    
    folder_name = folder.name
    parent_id = folder.parent_id
    folder.delete()
    
    return JsonResponse({
        "status": "success",
        "message": f"Deleted '{folder_name}'.",
        "parent_id": parent_id
    })


@staff_member_required
@require_POST
def delete_file(request):
    """
    Deletes a file attachment.
    """
    attachment_id = request.POST.get("attachment_id")
    
    if not attachment_id:
        return JsonResponse(
            {"status": "error", "message": "File ID required."},
            status=400
        )
    
    attachment = get_object_or_404(WorkItemAttachment, id=attachment_id)
    
    file_name = os.path.basename(attachment.file.name)
    
    # Delete the actual file from storage
    if attachment.file:
        attachment.file.delete(save=False)
    
    attachment.delete()
    
    return JsonResponse({
        "status": "success",
        "message": f"Deleted '{file_name}'."
    })


@staff_member_required
def download_file(request, attachment_id):
    """
    Downloads a file attachment.
    """
    attachment = get_object_or_404(WorkItemAttachment, id=attachment_id)
    
    if not attachment.file:
        raise Http404("File not found.")
    
    try:
        response = FileResponse(
            attachment.file.open('rb'),
            as_attachment=True,
            filename=os.path.basename(attachment.file.name)
        )
        return response
    except Exception:
        raise Http404("File not found.")


@staff_member_required
def upload_files(request):
    """
    Handles multiple file uploads to the current folder.
    """
    if request.method != "POST":
        return redirect("admin_app:file-manager")
    
    folder_id = request.POST.get("folder_id")
    files = request.FILES.getlist("files")
    
    if not folder_id or not files:
        return redirect("admin_app:file-manager")
    
    folder = get_object_or_404(DocumentFolder, id=folder_id)
    
    # Ensure folder can accept files
    invalid_types = [
        DocumentFolder.FolderType.ROOT,
        DocumentFolder.FolderType.YEAR,
        DocumentFolder.FolderType.CATEGORY,
    ]
    
    if folder.folder_type in invalid_types:
        # Redirect with error message (you'd want to use Django messages framework)
        return redirect("admin_app:file-manager-folder", folder_id=folder.id)
    
    uploaded_count = 0
    
    for file in files:
        try:
            # You'll need to adapt this based on your WorkItemAttachment model requirements
            # This is a simplified version - you may need work_item, attachment_type, etc.
            attachment = WorkItemAttachment(
                file=file,
                folder=folder,
                uploaded_by=request.user,
                # Add other required fields based on your model
            )
            attachment.save()
            uploaded_count += 1
        except Exception as e:
            # Log error but continue with other files
            continue
    
    return redirect("admin_app:file-manager-folder", folder_id=folder.id)