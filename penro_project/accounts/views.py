from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages


def login_view(request):

    # 🚫 Prevent authenticated users from accessing login page
    if request.user.is_authenticated:
        return redirect_user_by_role(request.user)

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # redirect to next=... if present
            next_url = request.GET.get("next")
            if next_url:
                return redirect(next_url)

            return redirect_user_by_role(user)

        messages.error(request, "Invalid username or password.")

    return render(request, "auth/login.html")

def redirect_user_by_role(user):
    if user.permission_role == "admin":
        return redirect("/main/admin/")

    elif user.permission_role == "manager":
        return redirect("/main/manager/")

    return redirect("/workers/user/")

def logout_view(request):
    logout(request)
    return redirect("login")


