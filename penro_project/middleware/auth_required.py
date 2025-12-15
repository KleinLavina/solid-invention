from django.conf import settings
from django.shortcuts import redirect
from django.urls import resolve, Resolver404

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

        self.PUBLIC_PREFIXES = (
            settings.LOGIN_URL,
            "/auth/",
            "/static/",
            "/media/",
            "/penro/django/admin/",
        )

    def __call__(self, request):
        path = request.path

        # Allow public paths
        if path.startswith(self.PUBLIC_PREFIXES):
            return self.get_response(request)

        # Block unauthenticated users
        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)

        # Authenticated user — validate URL
        try:
            resolve(path)
        except Resolver404:
            # Invalid URL → redirect safely
            if request.user.login_role == "admin":
                return redirect("admin_app:dashboard")
            return redirect("user_app:dashboard")

        return self.get_response(request)
