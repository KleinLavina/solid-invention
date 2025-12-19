from django.contrib import admin
from django.utils.html import format_html

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Admin configuration for system notifications
    """

    # ==========================
    # LIST VIEW
    # ==========================
    list_display = (
        "id",
        "recipient",
        "notif_type",
        "colored_title",
        "is_read",
        "created_at",
    )

    list_filter = (
        "notif_type",
        "is_read",
        "created_at",
    )

    search_fields = (
        "title",
        "message",
        "recipient__username",
        "recipient__first_name",
        "recipient__last_name",
    )

    ordering = ("-created_at",)

    list_per_page = 25

    # ==========================
    # FIELDSETS
    # ==========================
    fieldsets = (
        ("Recipient", {
            "fields": ("recipient",),
        }),
        ("Notification", {
            "fields": ("notif_type", "title", "message"),
        }),
        ("Context", {
            "fields": ("work_item",),
        }),
        ("Status", {
            "fields": ("is_read", "created_at"),
        }),
    )

    readonly_fields = ("created_at",)

    # ==========================
    # ACTIONS
    # ==========================
    actions = (
        "mark_as_read",
        "mark_as_unread",
    )

    # ==========================
    # CUSTOM DISPLAY
    # ==========================
    def colored_title(self, obj):
        color_map = {
            "chat": "#2563eb",     # blue
            "review": "#7c3aed",   # purple
            "status": "#16a34a",   # green
            "reminder": "#f59e0b", # orange
            "system": "#6b7280",   # gray
        }
        color = color_map.get(obj.notif_type, "#000")
        return format_html(
            '<span style="color:{}; font-weight:600;">{}</span>',
            color,
            obj.title,
        )

    colored_title.short_description = "Title"

    # ==========================
    # ADMIN ACTIONS
    # ==========================
    @admin.action(description="Mark selected notifications as READ")
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)

    @admin.action(description="Mark selected notifications as UNREAD")
    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)
