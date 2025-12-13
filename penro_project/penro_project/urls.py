from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('penro/django/admin/', admin.site.urls),

    # Login / Logout
    path('auth/', include('accounts.urls')),
    path('admin/', include('admin_app.urls')),

]
