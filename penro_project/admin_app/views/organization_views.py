from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from accounts.models import Team, User


@login_required
def manage_organization(request):

    # --------------------------------------------
    # 1. Load ALL teams (single source of truth)
    # --------------------------------------------
    teams = Team.objects.select_related("parent").order_by("team_type", "name")

    team_by_id = {t.id: t for t in teams}

    # Prepare containers (IMPORTANT)
    for t in teams:
        t.children_list = []
        t.users = []

    # Build tree manually (NO queryset recursion)
    root_teams = []
    for t in teams:
        if t.parent_id:
            team_by_id[t.parent_id].children_list.append(t)
        else:
            root_teams.append(t)

    # --------------------------------------------
    # 2. Load users + org assignments
    # --------------------------------------------
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

    # --------------------------------------------
    # 3. Attach users ONLY to lowest team
    # --------------------------------------------
    for user in users:
        org = user.primary_org
        if not org:
            continue

        if org.unit:
            team_by_id[org.unit_id].users.append(user)
        elif org.service:
            team_by_id[org.service_id].users.append(user)
        elif org.section:
            team_by_id[org.section_id].users.append(user)
        else:
            team_by_id[org.division_id].users.append(user)

    # --------------------------------------------
    # 4. Render
    # --------------------------------------------
    return render(
        request,
        "admin/page/manage_organization.html",
        {"teams": root_teams},
    )

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from accounts.models import Team
from django.core.exceptions import ValidationError


@login_required
def create_team(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        team_type = request.POST.get("team_type")
        parent_id = request.POST.get("parent") or None

        try:
            parent = Team.objects.get(id=parent_id) if parent_id else None

            team = Team(
                name=name,
                team_type=team_type,
                parent=parent,
            )
            team.full_clean()
            team.save()

            return JsonResponse({"success": True})

        except (Team.DoesNotExist, ValidationError) as e:
            return JsonResponse(
                {"success": False, "error": str(e)},
                status=400
            )

    # GET → modal form
    teams = Team.objects.order_by("team_type", "name")
    return render(
        request,
        "admin/page/modals/create_team_modal.html",
        {"teams": teams},
    )

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from accounts.models import Team
from django.core.exceptions import ValidationError
import json


@login_required
@require_http_methods(["POST"])
def edit_team(request):
    """
    Edit an existing organizational unit
    """
    team_id = request.POST.get("team_id")
    name = request.POST.get("name", "").strip()

    if not team_id or not name:
        return JsonResponse(
            {"success": False, "error": "Team ID and name are required"},
            status=400
        )

    try:
        team = Team.objects.get(id=team_id)
        team.name = name
        team.full_clean()
        team.save()

        return JsonResponse({"success": True})

    except Team.DoesNotExist:
        return JsonResponse(
            {"success": False, "error": "Team not found"},
            status=404
        )
    except ValidationError as e:
        return JsonResponse(
            {"success": False, "error": str(e)},
            status=400
        )


@login_required
@require_http_methods(["POST"])
def delete_team(request):
    """
    Delete an organizational unit and all its children
    """
    try:
        data = json.loads(request.body)
        team_id = data.get("team_id")

        if not team_id:
            return JsonResponse(
                {"success": False, "error": "Team ID is required"},
                status=400
            )

        team = Team.objects.get(id=team_id)
        team_name = team.name
        
        # Check if team has children (for logging/response)
        children_count = Team.objects.filter(parent=team).count()
        
        # Delete the team (Django will CASCADE to children if configured)
        team.delete()

        message = f"'{team_name}' deleted successfully."
        if children_count > 0:
            message += f" {children_count} sub-unit(s) were also removed."

        return JsonResponse({
            "success": True,
            "message": message
        })

    except Team.DoesNotExist:
        return JsonResponse(
            {"success": False, "error": "Team not found"},
            status=404
        )
    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "error": "Invalid JSON data"},
            status=400
        )
    except Exception as e:
        return JsonResponse(
            {"success": False, "error": str(e)},
            status=500
        )

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from accounts.models import Team, User
import json


@login_required
def view_hierarchy(request, team_id):
    """
    Display the hierarchical tree view for a specific division/team
    """
    # Get the root team (division)
    division = get_object_or_404(Team, id=team_id)
    
    # Load all teams that belong to this division's hierarchy
    all_teams = Team.objects.select_related("parent").order_by("team_type", "name")
    
    # Create a mapping of teams by ID
    team_by_id = {t.id: t for t in all_teams}
    
    # Initialize containers
    for t in all_teams:
        t.children_list = []
        t.users = []
    
    # Build the tree structure
    for t in all_teams:
        if t.parent_id and t.parent_id in team_by_id:
            team_by_id[t.parent_id].children_list.append(t)
    
    # Load users with their org assignments
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
    
    # Attach users to their lowest-level team
    for user in users:
        org = user.primary_org
        if not org:
            continue
        
        # Only add users that belong to this division's hierarchy
        if org.division_id != division.id:
            continue
        
        if org.unit_id and org.unit_id in team_by_id:
            team_by_id[org.unit_id].users.append(user)
        elif org.service_id and org.service_id in team_by_id:
            team_by_id[org.service_id].users.append(user)
        elif org.section_id and org.section_id in team_by_id:
            team_by_id[org.section_id].users.append(user)
        elif org.division_id == division.id:
            team_by_id[org.division_id].users.append(user)
    
    # Get the division with all its children populated
    division = team_by_id[division.id]
    
    return render(
        request,
        "admin/page/view_hierarchy.html",
        {"division": division},
    )

