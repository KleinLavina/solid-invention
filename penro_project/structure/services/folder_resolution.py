from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone

from accounts.models import TeamMembership
from structure.models import DocumentFolder


# ============================================================
# TEAM HIERARCHY RESOLUTION
# ============================================================

def get_team_chain(team):
    """
    Walks up the Team hierarchy and returns the chain
    from Division → ... → Unit.

    Example return order:
        [division, section, service?, unit]
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

    Rules:
    - Admins can upload anywhere
    - Users can ONLY upload to their own WorkItem
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
):
    folder, _ = DocumentFolder.objects.get_or_create(
        parent=parent,
        name=name,
        defaults={
            "folder_type": folder_type,
            "workcycle": workcycle,
            "created_by": created_by,
            "is_system_generated": True,
        }
    )
    return folder


# ============================================================
# MAIN RESOLUTION SERVICE
# ============================================================

def resolve_attachment_folder(*, work_item, attachment_type, actor):
    """
    Resolves (and creates if missing) the correct attachment folder.

    Folder structure enforced:

    ROOT
      └── YEAR
           └── CATEGORY (MOV)
                └── WORKCYCLE
                     └── DIVISION
                          └── SECTION
                               └── SERVICE? (optional)
                                    └── UNIT
                                         └── ATTACHMENT
    """

    # ---------------------------
    # 1. Permission check
    # ---------------------------
    assert_can_upload(work_item=work_item, actor=actor)

    # ---------------------------
    # 2. Resolve actor team
    # ---------------------------
    try:
        membership = TeamMembership.objects.select_related("team").get(
            user=actor
        )
    except TeamMembership.DoesNotExist:
        raise PermissionDenied(
            "You must belong to a team to upload attachments."
        )

    team_chain = get_team_chain(membership.team)

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
    year_name = str(work_item.workcycle.due_at.year)

    year_folder = get_or_create_folder(
        name=year_name,
        folder_type=DocumentFolder.FolderType.YEAR,
        parent=root,
    )

    # ---------------------------
    # 5. CATEGORY (MOV)
    # ---------------------------
    category_name = attachment_type.upper()

    category_folder = get_or_create_folder(
        name=category_name,
        folder_type=DocumentFolder.FolderType.CATEGORY,
        parent=year_folder,
    )

    # ---------------------------
    # 6. WORKCYCLE
    # ---------------------------
    wc_folder = get_or_create_folder(
        name=work_item.workcycle.title,
        folder_type=DocumentFolder.FolderType.WORKCYCLE,
        parent=category_folder,
        workcycle=work_item.workcycle,
    )

    # ---------------------------
    # 7. ORG STRUCTURE FOLDERS
    # ---------------------------
    parent_folder = wc_folder

    for team in team_chain:
        folder_type = team.team_type

        parent_folder = get_or_create_folder(
            name=team.name,
            folder_type=folder_type,
            parent=parent_folder,
        )

    # ---------------------------
    # 8. ATTACHMENT FOLDER
    # ---------------------------
    attachment_folder = get_or_create_folder(
        name="Attachments",
        folder_type=DocumentFolder.FolderType.ATTACHMENT,
        parent=parent_folder,
    )

    return attachment_folder
