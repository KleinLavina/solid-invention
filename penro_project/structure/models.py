from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError


class DocumentFolder(models.Model):
    class FolderType(models.TextChoices):
        ROOT = "root", "Root"
        YEAR = "year", "Year"
        CATEGORY = "category", "Category"      # e.g. MOV
        WORKCYCLE = "workcycle", "Work Cycle"

        DIVISION = "division", "Division"
        SECTION = "section", "Section"
        SERVICE = "service", "Service"
        UNIT = "unit", "Unit"

        ATTACHMENT = "attachment", "Attachment"

    name = models.CharField(
        max_length=150,
        help_text="Folder display name"
    )

    folder_type = models.CharField(
        max_length=20,
        choices=FolderType.choices,
        db_index=True,
        help_text="Semantic type of this folder"
    )

    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="children",
        on_delete=models.PROTECT,
        help_text="Parent folder in the hierarchy"
    )

    # Only set for WORKCYCLE folders
    workcycle = models.ForeignKey(
        "accounts.WorkCycle",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="folders",
        help_text="Associated work cycle (WORKCYCLE folders only)"
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="User who initiated creation (null for system-generated)"
    )

    is_system_generated = models.BooleanField(
        default=True,
        help_text="Automatically created by the system"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["folder_type", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["parent", "name"],
                name="unique_folder_name_per_parent"
            )
        ]
        indexes = [
            models.Index(fields=["folder_type"]),
            models.Index(fields=["parent"]),
            models.Index(fields=["workcycle"]),
        ]

    # ============================
    # VALIDATION (CRITICAL)
    # ============================
    def clean(self):
        hierarchy = {
            self.FolderType.ROOT: [None],

            self.FolderType.YEAR: [self.FolderType.ROOT],
            self.FolderType.CATEGORY: [self.FolderType.YEAR],
            self.FolderType.WORKCYCLE: [self.FolderType.CATEGORY],

            self.FolderType.DIVISION: [self.FolderType.WORKCYCLE],
            self.FolderType.SECTION: [self.FolderType.DIVISION],
            self.FolderType.SERVICE: [self.FolderType.SECTION],
            self.FolderType.UNIT: [self.FolderType.SECTION, self.FolderType.SERVICE],

            self.FolderType.ATTACHMENT: [self.FolderType.UNIT],
        }

        allowed_parents = hierarchy[self.folder_type]

        # Root must not have parent
        if self.folder_type == self.FolderType.ROOT:
            if self.parent is not None:
                raise ValidationError("Root folder cannot have a parent.")
            return

        # Others must have parent
        if not self.parent:
            raise ValidationError(f"{self.get_folder_type_display()} folder must have a parent.")

        # Parent type validation
        if self.parent.folder_type not in allowed_parents:
            allowed = ", ".join(
                dict(self.FolderType.choices)[t] for t in allowed_parents
            )
            raise ValidationError(
                f"{self.get_folder_type_display()} folder must belong under: {allowed}"
            )

        # Workcycle rule
        if self.folder_type == self.FolderType.WORKCYCLE and not self.workcycle:
            raise ValidationError("Workcycle folder must reference a WorkCycle.")

        if self.folder_type != self.FolderType.WORKCYCLE and self.workcycle:
            raise ValidationError("Only WORKCYCLE folders may reference a WorkCycle.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.get_folder_type_display()})"
