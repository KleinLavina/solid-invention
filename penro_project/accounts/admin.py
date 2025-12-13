from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import (
    User,
    Team,
    TeamMembership,
    WorkCycle,
    WorkAssignment,
    WorkItem,
    WorkItemAttachment,
)

# =========================
# USER
# =========================

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        "username",
        "first_name",
        "last_name",
        "position_title",
        "login_role",
        "is_active",
    )

    list_filter = ("login_role", "is_active")
    search_fields = ("username", "first_name", "last_name", "email")
    ordering = ("username",)

    fieldsets = BaseUserAdmin.fieldsets + (
        (
            "PENRO Details",
            {
                "fields": (
                    "position_title",
                    "login_role",
                )
            },
        ),
    )


# =========================
# TEAMS
# =========================

class TeamMembershipInline(admin.TabularInline):
    model = TeamMembership
    extra = 1


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name",)
    inlines = [TeamMembershipInline]


@admin.register(TeamMembership)
class TeamMembershipAdmin(admin.ModelAdmin):
    list_display = ("team", "user", "role", "joined_at")
    list_filter = ("role", "team")


# =========================
# WORK CYCLES
# =========================

@admin.register(WorkCycle)
class WorkCycleAdmin(admin.ModelAdmin):
    list_display = ("title", "due_at", "is_active", "created_by")
    list_filter = ("is_active",)
    search_fields = ("title",)
    ordering = ("-due_at",)


# =========================
# WORK ASSIGNMENTS
# =========================

@admin.register(WorkAssignment)
class WorkAssignmentAdmin(admin.ModelAdmin):
    list_display = ("workcycle", "assigned_user", "assigned_team", "assigned_at")
    list_filter = ("assigned_team",)
    search_fields = ("workcycle__title", "assigned_user__username")


# =========================
# WORK ITEMS
# =========================

class WorkItemAttachmentInline(admin.TabularInline):
    model = WorkItemAttachment
    extra = 0
    readonly_fields = ("uploaded_at",)


@admin.register(WorkItem)
class WorkItemAdmin(admin.ModelAdmin):
    list_display = (
        "workcycle",
        "owner",
        "status",
        "review_decision",
        "submitted_at",
    )

    list_filter = (
        "status",
        "review_decision",
        "workcycle",
    )

    search_fields = (
        "workcycle__title",
        "owner__username",
        "owner__first_name",
        "owner__last_name",
    )

    readonly_fields = ("created_at",)
    ordering = ("-created_at",)
    inlines = [WorkItemAttachmentInline]


# =========================
# ATTACHMENTS
# =========================

@admin.register(WorkItemAttachment)
class WorkItemAttachmentAdmin(admin.ModelAdmin):
    list_display = ("work_item", "uploaded_by", "uploaded_at")
    readonly_fields = ("uploaded_at",)
