from django.shortcuts import redirect
from django.conf import settings

class LoginRequiredMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        path = request.path

        # URLs that do NOT require login
        PUBLIC_PATHS = [
            settings.LOGIN_URL,  # "/auth/login/"
            "/auth/logout/",
            "/static/",
            "/admin/",  # Django admin site only
        ]

        # Allow access to PUBLIC paths
        if any(path.startswith(p) for p in PUBLIC_PATHS):
            return self.get_response(request)

        # BLOCK unauthenticated users
        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)

        # Authenticated but request invalid URL → send to login
        # (optional but matches your request)
        # Here, restricting by catching 404s is tricky...
        # But we can force disallowed paths redirect manually if needed.
        # For now, we assume all protected urls are valid.
        return self.get_response(request)
