from django.contrib import admin
from django.utils.html import format_html

from .models import DocumentFolder


@admin.register(DocumentFolder)
class DocumentFolderAdmin(admin.ModelAdmin):
    # =========================
    # LIST VIEW
    # =========================
    list_display = (
        "name",
        "folder_type",
        "parent_display",
        "workcycle",
        "is_system_generated",
        "created_by",
        "created_at",
    )

    list_filter = (
        "folder_type",
        "is_system_generated",
        "created_at",
    )

    search_fields = (
        "name",
        "workcycle__title",
        "parent__name",
    )

    ordering = ("folder_type", "name")

    # =========================
    # FORM LAYOUT
    # =========================
    fieldsets = (
        ("Folder Information", {
            "fields": (
                "name",
                "folder_type",
                "parent",
            )
        }),
        ("Work Cycle Context", {
            "fields": (
                "workcycle",
            ),
            "description": "Only applicable for WORKCYCLE folders.",
        }),
        ("System Metadata", {
            "fields": (
                "is_system_generated",
                "created_by",
                "created_at",
            ),
        }),
    )

    readonly_fields = (
        "created_at",
    )

    # =========================
    # UX SAFETY GUARDS
    # =========================
    def get_readonly_fields(self, request, obj=None):
        """
        Prevent changing critical fields once created.
        """
        ro = list(self.readonly_fields)

        if obj:
            # Prevent hierarchy corruption
            ro.extend(["folder_type", "parent"])

        return ro

    def get_queryset(self, request):
        """
        Optimize admin queries.
        """
        return (
            super()
            .get_queryset(request)
            .select_related("parent", "workcycle", "created_by")
        )
    @admin.action(description="Delete folder and all children")
    def delete_with_children(modeladmin, request, queryset):
        for folder in queryset:
            folder.children.all().delete()  
            folder.delete()
    # =========================
    # DISPLAY HELPERS
    # =========================
    @admin.display(description="Parent Folder")
    def parent_display(self, obj):
        if not obj.parent:
            return format_html("<span style='color:#64748b'>— Root —</span>")
        return obj.parent.name

    # =========================
    # SAVE HOOK
    # =========================
    def save_model(self, request, obj, form, change):
        """
        Auto-assign creator when manually created in admin.
        """
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
