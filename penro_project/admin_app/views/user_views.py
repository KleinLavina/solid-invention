from django.shortcuts import render, redirect, get_object_or_404
from accounts.models import User
from accounts.forms import UserCreateForm, UserUpdateForm


from django.shortcuts import render
from accounts.models import User, Team
from django.db.models import Prefetch


def users(request):
    divisions = (
        Team.objects
        .filter(team_type=Team.TeamType.DIVISION)
        .prefetch_related(
            "children__children__children",
            "children__children__memberships__user",
            "children__memberships__user",
            "memberships__user",
        )
        .order_by("name")
    )

    return render(
        request,
        "admin/page/users.html",
        {
            "divisions": divisions,
        }
    )


def create_user(request):
    if request.method == "POST":
        form = UserCreateForm(request.POST)
        if form.is_valid():
            form.save()
    return redirect("admin_app:users")


def update_user(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        user.first_name = request.POST.get("first_name", "")
        user.last_name = request.POST.get("last_name", "")
        user.email = request.POST.get("email", "")
        user.position_title = request.POST.get("position_title", "")
        user.login_role = request.POST.get("login_role", user.login_role)
        user.is_active = "is_active" in request.POST
        user.save()

    return redirect("admin_app:users")



def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        user.delete()
    return redirect("admin_app:users")
