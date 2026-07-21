import os

from django.conf import settings
from django.db import models


class Matter(models.Model):
    """A client / case / folder that documents get grouped under."""

    organization = models.ForeignKey(
        "accounts.Organization",
        on_delete=models.CASCADE,
        related_name="matters",
    )
    name = models.CharField(max_length=200)
    client_name = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


def upload_to(instance, filename):
    org = instance.organization.slug if instance.organization_id else "misc"
    return f"{org}/{filename}"


class Document(models.Model):
    """
    A file uploaded by the secretary. The AI organizer fills in category and
    summary daily. JAY LAW: these fields stay empty until real content is
    processed — nothing is ever invented.
    """

    class Category(models.TextChoices):
        UNSORTED = "unsorted", "Unsorted"
        CONTRACT = "contract", "Contract / Agreement"
        MOTION = "motion", "Motion / Filing"
        EVIDENCE = "evidence", "Evidence / Exhibit"
        CORRESPONDENCE = "correspondence", "Correspondence"
        FINANCIAL = "financial", "Financial / Billing"
        OTHER = "other", "Other"

    organization = models.ForeignKey(
        "accounts.Organization",
        on_delete=models.CASCADE,
        related_name="documents",
    )
    matter = models.ForeignKey(
        Matter,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
    )
    file = models.FileField(upload_to=upload_to)
    original_name = models.CharField(max_length=255, blank=True)
    title = models.CharField(max_length=255, blank=True)
    note = models.TextField(blank=True, help_text="Secretary's note for the boss.")

    # Filled by the AI organizer (blank until then).
    category = models.CharField(
        max_length=20, choices=Category.choices, default=Category.UNSORTED
    )
    ai_summary = models.TextField(blank=True)
    ai_processed_at = models.DateTimeField(null=True, blank=True)

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="uploads",
    )
    # Boss workflow.
    seen_by_boss = models.BooleanField(default=False)
    handled = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title or self.original_name or f"Document #{self.pk}"

    def save(self, *args, **kwargs):
        if self.file and not self.original_name:
            self.original_name = os.path.basename(self.file.name)
        if not self.title:
            self.title = self.original_name
        super().save(*args, **kwargs)

    @property
    def extension(self):
        name = self.original_name or self.file.name
        return os.path.splitext(name)[1].lower().lstrip(".")


class DocumentComment(models.Model):
    """Two-way notes between secretary and boss on a single document."""

    document = models.ForeignKey(
        Document, on_delete=models.CASCADE, related_name="comments"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment on {self.document} by {self.author}"
