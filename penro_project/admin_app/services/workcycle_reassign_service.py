from django.db import transaction
from accounts.models import WorkItem, WorkAssignment, TeamMembership


@transaction.atomic
def reassign_workcycle(*, workcycle, users, team, performed_by):
    """
    Safely reassign a workcycle without violating unique constraints.
    """

    # -------------------------------------------------
    # 1. Resolve final target users
    # -------------------------------------------------
    target_users = set()

    if team:
        team_members = TeamMembership.objects.filter(team=team).select_related("user")
        target_users.update(m.user for m in team_members)

    target_users.update(users)

    # -------------------------------------------------
    # 2. Existing WorkItems
    # -------------------------------------------------
    existing_items = WorkItem.objects.filter(workcycle=workcycle)
    existing_users = {wi.owner for wi in existing_items}

    # -------------------------------------------------
    # 3. Archive removed users
    # -------------------------------------------------
    removed_users = existing_users - target_users
    for wi in existing_items.filter(owner__in=removed_users):
        wi.status = "not_started"  # or add is_archived flag if you want
        wi.save(update_fields=["status"])

    # -------------------------------------------------
    # 4. Create WorkItems for new users ONLY
    # -------------------------------------------------
    new_users = target_users - existing_users
    WorkItem.objects.bulk_create(
        [
            WorkItem(
                workcycle=workcycle,
                owner=user,
                status="not_started",
            )
            for user in new_users
        ]
    )

    # -------------------------------------------------
    # 5. Replace assignments (audit trail)
    # -------------------------------------------------
    WorkAssignment.objects.filter(workcycle=workcycle).delete()

    if team:
        WorkAssignment.objects.create(
            workcycle=workcycle,
            assigned_team=team
        )
    else:
        WorkAssignment.objects.bulk_create(
            [
                WorkAssignment(
                    workcycle=workcycle,
                    assigned_user=user
                )
                for user in users
            ]
        )
