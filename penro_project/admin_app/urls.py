from django.urls import path
from admin_app.views import (
    dashboard,
    workcycle_list, create_workcycle, edit_workcycle, reassign_workcycle, workcycle_assignments,  
    team_views,
    users, create_user, update_user, delete_user,
    completed_work_summary, done_workers_by_workcycle,
    review_work_item, admin_work_item_discussion, admin_work_item_threads,
)
from .views.notification_views import admin_notifications
from .views.document_views import admin_documents
from .views.file_manager_views import admin_file_manager, create_folder, move_attachment, move_folder, rename_folder, delete_file, delete_folder, download_file, upload_files
from .views.all_files_views import all_files_uploaded


app_name = "admin_app"


urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("discussions/", admin_work_item_threads, name="discussion-list"),
    path("notifications/", admin_notifications, name="admin-notifications"),

    path("workcycles/", workcycle_list, name="workcycles"),
    path("workcycles/create/", create_workcycle, name="workcycle-create"),
    path("workcycles/edit/", edit_workcycle, name="workcycle-edit"),
    path("workcycles/reassign/", reassign_workcycle, name="workcycle-reassign"),
    # admin_app/urls.py
    path(
    "workcycles/<int:pk>/assignments/",
    workcycle_assignments,
    name="workcycle-assignments",
),

    path(
        "analytics/completed-work/",
        completed_work_summary,
        name="completed-work-summary"
    ),
    path(
        "analytics/workcycle/<int:workcycle_id>/done-workers/",
        done_workers_by_workcycle,
        name="done-workers-by-workcycle"
    ),
    path(
    "work-items/<int:item_id>/discussion/",
    admin_work_item_discussion,
    name="work-item-discussion"),
    path(
        "work-items/<int:item_id>/review/",
        review_work_item,
        name="work-item-review"
    ),
path(
    "documents/",
    admin_documents,
    name="documents"
),

path(
    "documents/files/",
    admin_file_manager,
    name="file-manager"
),

path(
    "documents/files/<int:folder_id>/",
    admin_file_manager,
    name="file-manager-folder"
),
path("documents/files/create-folder/", create_folder, name="create-folder"),
path(
    "documents/files/move/",
    move_attachment,
    name="move-attachment"
),
    path(
    "documents/files/move-folder/",
    move_folder,
    name="move-folder"
),
    path(
        "documents/all-files/",
        all_files_uploaded,
        name="all-files-uploaded"
    ),
# admin_app/urls.py - ADD THESE PATHS

path("documents/files/create-folder/", create_folder, name="create-folder"),
path("documents/files/rename-folder/", rename_folder, name="rename-folder"),
path("documents/files/delete-folder/", delete_folder, name="delete-folder"),
path("documents/files/delete-file/", delete_file, name="delete-file"),
path("documents/files/download/<int:attachment_id>/", download_file, name="download-file"),
path("documents/files/upload/", upload_files, name="upload-files"),
path("documents/files/move/", move_attachment, name="move-attachment"),
path("documents/files/move-folder/", move_folder, name="move-folder"),


    path("teams/", team_views, name="teams"),

    path("users/<int:user_id>/update/", update_user, name="user-update"),
    path("users/<int:user_id>/delete/", delete_user, name="user-delete"),
    path("users/create/", create_user, name="user-create"),
    path("users/", users, name="users"),
    

    


    

]
