from .dashboard_views import dashboard
from .workcycle_views import workcycle_list, create_workcycle, edit_workcycle, reassign_workcycle, workcycle_assignments
from .team_views import team_views
from .user_views import users, create_user, update_user, delete_user
from .complete_work_summary import completed_work_summary
from .done_workers_by_workcycle import done_workers_by_workcycle
from .review_views import review_work_item, admin_work_item_discussion
from .work_item_threads import admin_work_item_threads
from .document_views import admin_documents
from .file_manager_views import admin_file_manager, create_folder, move_attachment