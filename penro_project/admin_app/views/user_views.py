from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse

from accounts.models import User, Team, OrgAssignment
from accounts.forms import UserCreateForm

@login_required
def users(request):
    users = (
        User.objects
        .select_related(
            "org_assignment__division",
            "org_assignment__section",
            "org_assignment__service",
            "org_assignment__unit",
        )
        .order_by("username")
    )

    form = UserCreateForm()  # ✅ REQUIRED

    return render(
        request,
        "admin/page/users.html",
        {
            "users": users,
            "total_users": users.count(),
            "form": form,          # ✅ THIS MAKES INPUTS APPEAR
        },
    )

@login_required
def create_user(request):
    """
    AJAX-only user creation endpoint.
    Always returns JSON.
    """

    # ❌ Block GET requests
    if request.method != "POST":
        return JsonResponse(
            {
                "success": False,
                "error": "Invalid request method"
            },
            status=405
        )

    form = UserCreateForm(request.POST)

    # ❌ Invalid form → return errors
    if not form.is_valid():
        return JsonResponse(
            {
                "success": False,
                "errors": form.errors
            },
            status=400
        )

    # ✅ Create user
    user = form.save()

    # (Optional) Store raw form data for onboarding if you still need it
    request.session[f"user_form_{user.id}"] = request.POST

    # ✅ SUCCESS (always JSON)
    return JsonResponse(
        {
            "success": True,
            "onboard_url": reverse(
                "admin_app:onboard-division",
                args=[user.id]
            )
        },
        status=201
    )

# ============================================
# ONBOARDING FLOW
# ============================================

@login_required
def onboard_division(request, user_id):
    """Step 1: Select Division (Modal-ready)"""
    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        division_id = request.POST.get("division")

        if division_id:
            # Save selection to session
            request.session[f"onboard_{user.id}_division"] = division_id

            # If AJAX → return next step URL
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({
                    "next": reverse(
                        "admin_app:onboard-section",
                        args=[user.id]
                    )
                })

            # Fallback for non-AJAX
            return redirect(
                "admin_app:onboard-section",
                user_id=user.id
            )

    divisions = Team.objects.filter(
        team_type=Team.TeamType.DIVISION
    ).order_by("name")

    return render(
        request,
        "admin/page/modals/onboard_division.html",
        {
            "user": user,
            "divisions": divisions,
            "step": 1,
            "total_steps": 4,
        },
    )

@login_required
def onboard_section(request, user_id):
    user = get_object_or_404(User, id=user_id)
    division_id = request.session.get(f"onboard_{user.id}_division")

    if not division_id:
        return redirect("admin_app:onboard-division", user_id=user.id)

    if request.method == "POST":
        section_id = request.POST.get("section")

        if section_id:
            request.session[f"onboard_{user.id}_section"] = section_id

            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({
                    "next": reverse(
                        "admin_app:onboard-service",
                        args=[user.id]
                    )
                })

            return redirect(
                "admin_app:onboard-service",
                user_id=user.id
            )

    sections = Team.objects.filter(
        team_type=Team.TeamType.SECTION,
        parent_id=division_id
    ).order_by("name")

    division = Team.objects.get(id=division_id)

    return render(
        request,
        "admin/page/modals/onboard_section.html",
        {
            "user": user,
            "sections": sections,
            "division": division,
            "step": 2,
            "total_steps": 4,
        },
    )

@login_required
def onboard_service(request, user_id):
    user = get_object_or_404(User, id=user_id)
    section_id = request.session.get(f"onboard_{user.id}_section")

    if not section_id:
        return redirect("admin_app:onboard-section", user_id=user.id)

    if request.method == "POST":
        service_id = request.POST.get("service")

        if service_id:
            request.session[f"onboard_{user.id}_service"] = service_id

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({
                "next": reverse(
                    "admin_app:onboard-unit",
                    args=[user.id]
                )
            })

        return redirect(
            "admin_app:onboard-unit",
            user_id=user.id
        )

    services = Team.objects.filter(
        team_type=Team.TeamType.SERVICE,
        parent_id=section_id
    ).order_by("name")

    section = Team.objects.get(id=section_id)

    return render(
        request,
        "admin/page/modals/onboard_service.html",
        {
            "user": user,
            "services": services,
            "section": section,
            "step": 3,
            "total_steps": 4,
        },
    )

@login_required
def onboard_unit(request, user_id):
    user = get_object_or_404(User, id=user_id)
    section_id = request.session.get(f"onboard_{user.id}_section")
    service_id = request.session.get(f"onboard_{user.id}_service")

    if not section_id:
        return redirect("admin_app:onboard-section", user_id=user.id)

    if request.method == "POST":
        unit_id = request.POST.get("unit")

        if unit_id:
            request.session[f"onboard_{user.id}_unit"] = unit_id

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({
                "next": reverse(
                    "admin_app:onboard-complete",
                    args=[user.id]
                )
            })

        return redirect(
            "admin_app:onboard-complete",
            user_id=user.id
        )

    parent_ids = [section_id]
    if service_id:
        parent_ids.append(service_id)

    units = Team.objects.filter(
        team_type=Team.TeamType.UNIT,
        parent_id__in=parent_ids
    ).order_by("name")

    section = Team.objects.get(id=section_id)
    service = Team.objects.filter(id=service_id).first() if service_id else None

    return render(
        request,
        "admin/page/modals/onboard_unit.html",
        {
            "user": user,
            "units": units,
            "section": section,
            "service": service,
            "step": 4,
            "total_steps": 4,
        },
    )


@login_required
def onboard_complete(request, user_id):
    """
    Final onboarding step.
    This view MUST return HTML because it is rendered inside a modal.
    """

    user = get_object_or_404(User, id=user_id)

    # Pull onboarding data from session
    division_id = request.session.get(f"onboard_{user.id}_division")
    section_id = request.session.get(f"onboard_{user.id}_section")
    service_id = request.session.get(f"onboard_{user.id}_service")
    unit_id = request.session.get(f"onboard_{user.id}_unit")

    # Safety check: onboarding incomplete → restart
    if not division_id or not section_id:
        return redirect("admin_app:onboard-division", user_id=user.id)

    # Create or update organization assignment
    org_assignment, _ = OrgAssignment.objects.update_or_create(
        user=user,
        defaults={
            "division_id": division_id,
            "section_id": section_id,
            "service_id": service_id or None,
            "unit_id": unit_id or None,
        }
    )

    # Clear onboarding session data
    for key in (
        f"onboard_{user.id}_division",
        f"onboard_{user.id}_section",
        f"onboard_{user.id}_service",
        f"onboard_{user.id}_unit",
        f"user_form_{user.id}",
    ):
        request.session.pop(key, None)

    # ✅ ALWAYS return HTML (no JSON here)
    return render(
        request,
        "admin/page/modals/onboard_complete.html",
        {
            "user": user,
            "org_assignment": org_assignment,
        },
    )