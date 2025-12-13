from django.db import transaction
from accounts.models import WorkCycle, WorkAssignment, WorkItem


@transaction.atomic
def create_workcycle_with_assignments(
    *,
    title,
    description,
    due_at,
    created_by,
    users,
    team,
):
    workcycle = WorkCycle.objects.create(
        title=title,
        description=description,
        due_at=due_at,
        created_by=created_by,
    )

    if team:
        WorkAssignment.objects.create(
            workcycle=workcycle,
            assigned_team=team
        )

        for membership in team.memberships.select_related("user"):
            WorkItem.objects.create(
                workcycle=workcycle,
                owner=membership.user
            )

    for user in users:
        WorkAssignment.objects.create(
            workcycle=workcycle,
            assigned_user=user
        )

        WorkItem.objects.create(
            workcycle=workcycle,
            owner=user
        )

    return workcycle
