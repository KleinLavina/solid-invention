from django.shortcuts import render, redirect, get_object_or_404
from accounts.models import User
from accounts.forms import UserCreateForm, UserUpdateForm


def users(request):
    users_qs = User.objects.all().order_by("username")

    # ✅ define role choices HERE (safe)
    role_choices = User._meta.get_field("login_role").choices

    return render(
        request,
        "admin/page/users.html",
        {
            "users": users_qs,
            "create_form": UserCreateForm(),
            "role_choices": role_choices,  # 👈 pass to template
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
