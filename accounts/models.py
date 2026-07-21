from django.contrib.auth.models import AbstractUser
from django.db import models


class Organization(models.Model):
    """One customer = one organization. Customer #1 is Jason Goins."""

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=80, unique=True)
    # Free-form label shown in the header, e.g. "Jason Goins, Attorney at Law".
    display_name = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class User(AbstractUser):
    """
    Custom user. Everyone belongs to one organization and has a role.
    - secretary: uploads and tags files
    - boss: views files on the phone, uses them, leaves notes
    """

    class Role(models.TextChoices):
        SECRETARY = "secretary", "Secretary"
        BOSS = "boss", "Boss"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="users",
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.SECRETARY,
    )

    @property
    def is_boss(self):
        return self.role == self.Role.BOSS

    @property
    def is_secretary(self):
        return self.role == self.Role.SECRETARY
