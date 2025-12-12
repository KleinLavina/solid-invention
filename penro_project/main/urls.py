from django.urls import path
from . import views

app_name = "main"

urlpatterns = [
    path('admin/', views.admin_dashboard, name='admin'),
    path("admin/departments/", views.department_list, name="departments"),
    path("admin/departments/create/", views.department_create, name="department-create"),
     path("admin/departments/<int:dept_id>/edit/", views.department_edit, name="department-edit"),
    path("admin/departments/<int:dept_id>/delete/", views.department_delete, name="department-delete"),
    
    path("admin/departments/<int:dept_id>/workers/", views.workers_by_department, name="workers"),
    path("admin/departments/<int:dept_id>/workers/create/", views.worker_create, name="worker-create"),
    path("admin/departments/<int:dept_id>/workers/<int:worker_id>/edit/", views.worker_edit, name="worker-edit"),
    path("admin/departments/<int:dept_id>/workers/<int:worker_id>/delete/", views.worker_delete,name="worker-delete"),

 
    path("admin/deadlines/", views.deadline_list, name="deadline-list"),
    path("admin/deadlines/create/", views.deadline_create, name="deadline-create"),
    path("admin/deadlines/<int:pk>/edit/", views.deadline_edit, name="deadline-edit"),
    path("admin/deadlines/<int:pk>/delete/", views.deadline_delete, name="deadline-delete"),
    path("admin/deadlines/<int:deadline_id>/statuses/", views.deadline_status_view, name="deadline-status"),
]
