from django.core.exceptions import PermissionDenied
from accounts.models import TeamMembership
from structure.models import DocumentFolder


# ============================================================
# TEAM HIERARCHY RESOLUTION
# ============================================================

def get_team_chain(team):
    """
    Walks up the Team hierarchy and returns the chain
    from Division → ... → Unit.
    """
    chain = []
    current = team

    while current:
        chain.append(current)
        current = current.parent

    return list(reversed(chain))


# ============================================================
# PERMISSION CHECKS
# ============================================================

def assert_can_upload(*, work_item, actor):
    """
    Enforces who is allowed to upload attachments.
    """

    if actor.login_role == "admin":
        return

    if work_item.owner_id != actor.id:
        raise PermissionDenied(
            "You are not allowed to upload attachments for this work item."
        )


# ============================================================
# FOLDER GET-OR-CREATE HELPERS
# ============================================================

def get_or_create_folder(
    *,
    name,
    folder_type,
    parent,
    workcycle=None,
    created_by=None,
    system=True,
):
    folder, _ = DocumentFolder.objects.get_or_create(
        parent=parent,
        name=name,
        defaults={
            "folder_type": folder_type,
            "workcycle": workcycle,
            "created_by": created_by,
            "is_system_generated": system,
        }
    )
    return folder


# ============================================================
# MAIN RESOLUTION SERVICE (OPTION A)
# ============================================================

def resolve_attachment_folder(*, work_item, attachment_type, actor):
    """
    Resolves the DEFAULT attachment folder for uploads.

    NOTE:
    - This does NOT lock files to a single location
    - Drag & drop may move files later
    """

    # ---------------------------
    # 1. Permission check
    # ---------------------------
    assert_can_upload(work_item=work_item, actor=actor)

    # ---------------------------
    # 2. Resolve actor team (optional context)
    # ---------------------------
    team_chain = []
    try:
        membership = TeamMembership.objects.select_related("team").get(
            user=actor
        )
        team_chain = get_team_chain(membership.team)
    except TeamMembership.DoesNotExist:
        pass  # uploads still allowed for admins / system

    # ---------------------------
    # 3. ROOT folder
    # ---------------------------
    root = get_or_create_folder(
        name="ROOT",
        folder_type=DocumentFolder.FolderType.ROOT,
        parent=None,
    )

    # ---------------------------
    # 4. YEAR folder
    # ---------------------------
    year_folder = get_or_create_folder(
        name=str(work_item.workcycle.due_at.year),
        folder_type=DocumentFolder.FolderType.YEAR,
        parent=root,
    )

    # ---------------------------
    # 5. CATEGORY folder
    # ---------------------------
    category_folder = get_or_create_folder(
        name=attachment_type.upper(),
        folder_type=DocumentFolder.FolderType.CATEGORY,
        parent=year_folder,
    )

    # ---------------------------
    # 6. WORKCYCLE folder
    # ---------------------------
    wc_folder = get_or_create_folder(
        name=work_item.workcycle.title,
        folder_type=DocumentFolder.FolderType.WORKCYCLE,
        parent=category_folder,
        workcycle=work_item.workcycle,
    )

    # ---------------------------
    # 7. OPTIONAL ORG STRUCTURE (system-only)
    # ---------------------------
    parent_folder = wc_folder
    for team in team_chain:
        parent_folder = get_or_create_folder(
            name=team.name,
            folder_type=team.team_type,
            parent=parent_folder,
        )

    # ---------------------------
    # 8. DEFAULT ATTACHMENT FOLDER
    # ---------------------------
    attachment_folder = get_or_create_folder(
        name="Attachments",
        folder_type=DocumentFolder.FolderType.ATTACHMENT,
        parent=parent_folder,
    )

    return attachment_folder
