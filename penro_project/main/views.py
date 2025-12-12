from django.contrib import messages
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from datetime import date
from django.shortcuts import render
from django.db.models import Count
from accounts.models import Department, User
from django.shortcuts import render, redirect, get_object_or_404
from datetime import datetime
from submission_settings.models import ReportDeadlineSetting, ReportSubmission, ReportFile, SubmissionReminder, UserNotification
from submission_settings.analytics_models import (
    ReportAnalytics,
    DepartmentDeadlineAnalytics,
    ReportAnalyticsSnapshot,
    UserSubmissionAnalytics,
)



@login_required
def admin_dashboard(request):
    return render(request, "admin/page/dashboard.html")

@login_required
def department_list(request):
    departments = Department.objects.all().prefetch_related("users")
    total_workers = User.objects.filter(department__isnull=False).count()

    return render(request, "admin/page/departments.html", {
        "departments": departments,
        "total_workers": total_workers,
    })
@login_required
def department_create(request):
    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description", "")

        if not name:
            messages.error(request, "Department name is required.")
            return redirect("main:departments")  # FIXED

        Department.objects.create(
            name=name,
            description=description
        )

        messages.success(request, "Department created successfully!")
        return redirect("main:departments")  # FIXED

    return redirect("main:departments")  # FIXED

@login_required
def department_edit(request, dept_id):
    dept = get_object_or_404(Department, id=dept_id)

    if request.method == "POST":
        dept.name = request.POST.get("name")
        dept.description = request.POST.get("description", "")
        dept.save()

        messages.success(request, "Department updated successfully!")
        return redirect("main:departments")

    return redirect("main:departments")


@login_required
def department_delete(request, dept_id):
    dept = get_object_or_404(Department, id=dept_id)

    if request.method == "POST":

        # 1️⃣ Delete notifications linked to submissions of this department
        from submission_settings.models import ReportSubmission
        from submission_settings.models import UserNotification, SubmissionReminder, ReportFile

        submissions = ReportSubmission.objects.filter(deadline__department=dept)

        UserNotification.objects.filter(submission__in=submissions).delete()

        # 2️⃣ Delete reminders for deadlines of this department
        SubmissionReminder.objects.filter(deadline__department=dept).delete()

        # 3️⃣ Delete files attached to submissions
        ReportFile.objects.filter(submission__in=submissions).delete()

        # 4️⃣ Delete all submissions (safe now)
        submissions.delete()

        # 5️⃣ Delete all deadlines for this department
        dept.report_deadlines.all().delete()

        # 6️⃣ Delete analytics related to deadlines and department
        dept.deadline_analytics.all().delete()
        dept.analytics_by_deadline.all().delete()

        # 7️⃣ Delete users in this department
        dept.users.all().delete()

        # 8️⃣ Now delete the department safely
        dept.delete()

        messages.success(request, "Department deleted successfully!")
        return redirect("main:departments")

    return redirect("main:departments")


def workers_by_department(request, dept_id):
    all_departments = Department.objects.all()  # needed for dropdown

    if dept_id == 0:
        workers = User.objects.filter(department__isnull=False)
        dept_name = "All Workers"
    else:
        dept = get_object_or_404(Department, id=dept_id)
        workers = dept.users.all()
        dept_name = dept.name

    return render(request, "admin/page/workers.html", {
        "dept_name": dept_name,
        "workers": workers,
        "dept_id": dept_id,
        "all_departments": all_departments,  # <-- added
    })

@login_required
def worker_create(request, dept_id):
    if request.method == "POST":

        password = request.POST["password"]
        confirm_password = request.POST["confirm_password"]

        # Server-side password match check
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("main:workers", dept_id=dept_id)

        user = User.objects.create_user(
            username=request.POST["username"],
            password=password,
            first_name=request.POST.get("first_name", ""),
            last_name=request.POST.get("last_name", ""),
            position_title=request.POST.get("position_title", ""),
            contact_number=request.POST.get("contact_number", ""),
            department_id=request.POST.get("department"),
            permission_role="user",
        )

        messages.success(request, f"Worker '{user.get_full_name()}' created!")
        return redirect("main:workers", dept_id=dept_id)

    return redirect("main:workers", dept_id=dept_id)

@login_required
def worker_edit(request, dept_id, worker_id):
    # Get the worker WITHOUT filtering by department
    worker = get_object_or_404(User, id=worker_id)

    if request.method == "POST":
        worker.first_name = request.POST.get("first_name", "")
        worker.last_name = request.POST.get("last_name", "")
        worker.username = request.POST.get("username", worker.username)
        worker.position_title = request.POST.get("position_title", "")
        worker.contact_number = request.POST.get("contact_number", "")

        # Allow admin to change department
        new_dept = request.POST.get("department")
        if new_dept:
            worker.department_id = new_dept

        worker.save()

        # Redirect back to the workers page (even if dept_id = 0)
        return redirect(f"/main/admin/departments/{dept_id}/workers/")

    return redirect(f"/main/admin/departments/{dept_id}/workers/")

@login_required
def worker_delete(request, dept_id, worker_id):
    worker = get_object_or_404(User, id=worker_id)

    if request.method == "POST":

        # 1️⃣ Delete files uploaded by this user
        ReportFile.objects.filter(submission__user=worker).delete()

        # 2️⃣ Delete all submissions
        ReportSubmission.objects.filter(user=worker).delete()

        # 3️⃣ Delete reminders
        SubmissionReminder.objects.filter(user=worker).delete()

        # 4️⃣ Delete notifications
        UserNotification.objects.filter(user=worker).delete()

        # 5️⃣ Delete user analytics
        UserSubmissionAnalytics.objects.filter(user=worker).delete()

        # 6️⃣ Finally delete the user
        worker.delete()

        return redirect("main:workers", dept_id=dept_id)

    return redirect("main:workers", dept_id=dept_id)


@login_required
def deadline_list(request):
    # Load deadlines and related objects
    deadlines = ReportDeadlineSetting.objects.select_related("department") \
        .prefetch_related("submissions", "submissions__user")

    departments = Department.objects.all()
    enriched = []

    today = timezone.now().date()  # calculate once for performance

    for d in deadlines:
        submissions_qs = d.submissions.all()
        dept_user_count = d.department.users.count()

        # --- Submission-level logic (your update_status_logic) ---
        context_subs = []
        for sub in submissions_qs:
            info = sub.update_status_logic()
            context_subs.append({
                "obj": sub,
                "user": sub.user,
                **info
            })

        # --- Deadline stats ---
        total_expected = dept_user_count
        total_submitted = submissions_qs.count()

        complete_count = submissions_qs.filter(status="complete").count()
        in_progress_count = submissions_qs.filter(status="in_progress").count()
        pending_count = submissions_qs.filter(status="pending").count()
        late_count = submissions_qs.filter(status="late").count()
        late_overdue_count = submissions_qs.filter(status="late_overdue").count()

        # --- Completion percentage ---
        if total_expected > 0:
            completion_pct = round((complete_count / total_expected) * 100)
        else:
            completion_pct = round((complete_count / total_submitted) * 100) if total_submitted else 0

        completion_pct = max(0, min(100, completion_pct))  # clamp 0–100

        # --- Determine if progress should show ---
        if total_expected > 0:
            show_progress = pending_count < total_expected
        else:
            show_progress = (total_submitted > 0 and pending_count < total_submitted)

        # -------------------------------------
        # 🟢 NEW: DAYS REMAINING CALCULATION
        # -------------------------------------
        days_remaining = (d.deadline_date - today).days

        enriched.append({
            "obj": d,
            "department": d.department,

            # submission objects with computed status
            "submissions": context_subs,

            # deadline-level data
            "total_expected": total_expected,
            "total_submitted": total_submitted,
            "complete_count": complete_count,
            "in_progress_count": in_progress_count,
            "pending_count": pending_count,
            "late_count": late_count,
            "late_overdue_count": late_overdue_count,
            "completion_pct": completion_pct,
            "show_progress": show_progress,

            "start_date": d.start_date,
            "deadline_date": d.deadline_date,

            # 🌟 REQUIRED FOR YOUR TEMPLATE
            "days_remaining": days_remaining,
        })

    return render(request, "admin/page/report_deadline_list.html", {
        "deadlines": enriched,
        "departments": departments,
    })

@login_required
def deadline_create(request):
    if request.method == "POST":
        department_id = request.POST.get("department")
        title = request.POST.get("title")
        description = request.POST.get("description")
        start_date_str = request.POST.get("start_date")
        deadline_date_str = request.POST.get("deadline_date")

        # Basic validation
        if not (department_id and title and start_date_str and deadline_date_str):
            messages.error(request, "All required fields must be filled.")
            return redirect("main:deadline-list")

        # Convert strings → date objects
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        deadline_date = datetime.strptime(deadline_date_str, "%Y-%m-%d").date()

        # Save to model
        ReportDeadlineSetting.objects.create(
            department_id=department_id,
            title=title,
            description=description,
            start_date=start_date,
            deadline_date=deadline_date,
        )

        messages.success(request, "Deadline successfully created!")
        return redirect("main:deadline-list")

    return redirect("main:deadline-list")

@login_required
def deadline_edit(request, pk):
    deadline = get_object_or_404(ReportDeadlineSetting, pk=pk)

    if request.method == "POST":
        deadline.department_id = request.POST.get("department")
        deadline.title = request.POST.get("title")
        deadline.description = request.POST.get("description")
        deadline.start_date = request.POST.get("start_date")
        deadline.deadline_date = request.POST.get("deadline_date")
        deadline.save()

    return redirect("main:deadline-list")


@login_required
def deadline_delete(request, pk):
    deadline = get_object_or_404(ReportDeadlineSetting, pk=pk)

    # Delete analytics safely
    ReportAnalyticsSnapshot.objects.filter(analytics__deadline=deadline).delete()
    DepartmentDeadlineAnalytics.objects.filter(deadline=deadline).delete()
    ReportAnalytics.objects.filter(deadline=deadline).delete()

    # Delete submissions + files
    ReportFile.objects.filter(submission__deadline=deadline).delete()
    ReportSubmission.objects.filter(deadline=deadline).delete()

    # Finally delete the deadline itself
    deadline.delete()

    return redirect("main:deadline-list")

@login_required
def deadline_status_view(request, deadline_id):
    deadline = get_object_or_404(
        ReportDeadlineSetting.objects.select_related("department"),
        id=deadline_id
    )

    # Fetch all submissions for this deadline
    submissions = (
        ReportSubmission.objects
        .select_related("user")
        .filter(deadline=deadline)
        .order_by("user__last_name")
    )

    # Attach computed values (remaining days, status, etc.)
    worker_list = []

    for sub in submissions:
        info = sub.update_status_logic()  # from your model
        worker_list.append({
            "obj": sub,
            "user": sub.user,
            **info
        })

    context = {
        "deadline": deadline,
        "workers": worker_list,
    }

    return render(request, "admin/page/deadline_worker_statuses.html", context)
