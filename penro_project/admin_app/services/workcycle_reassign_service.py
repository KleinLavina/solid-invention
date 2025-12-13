from django.db import transaction
from accounts.models import WorkItem, WorkAssignment, TeamMembership

@transaction.atomic
def reassign_workcycle(*, workcycle, users, team, performed_by):

    # 1. Resolve target users
    target_users = set()

    if team:
        members = TeamMembership.objects.filter(team=team).select_related("user")
        target_users.update(m.user for m in members)

    target_users.update(users)

    # 2. Existing work items
    existing_items = WorkItem.objects.filter(workcycle=workcycle)
    existing_users = {wi.owner for wi in existing_items}

    # 3. Deactivate removed users
    removed_users = existing_users - target_users
    WorkItem.objects.filter(
        workcycle=workcycle,
        owner__in=removed_users,
        is_active=True
    ).update(
        is_active=False,
        status="not_started"
    )

    # 4. Reactivate or create safely
    for user in target_users:
        wi, created = WorkItem.objects.get_or_create(
            workcycle=workcycle,
            owner=user,
            defaults={
                "status": "not_started",
                "is_active": True,
            }
        )

        if not created and not wi.is_active:
            wi.is_active = True
            wi.status = "not_started"
            wi.save(update_fields=["is_active", "status"])

    # 5. Replace assignments
    WorkAssignment.objects.filter(workcycle=workcycle).delete()

    if team:
        WorkAssignment.objects.create(
            workcycle=workcycle,
            assigned_team=team
        )
    else:
        WorkAssignment.objects.bulk_create([
            WorkAssignment(workcycle=workcycle, assigned_user=user)
            for user in users
        ])
