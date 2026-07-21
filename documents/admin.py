from django.contrib import admin

from .models import Document, DocumentComment, Matter


@admin.register(Matter)
class MatterAdmin(admin.ModelAdmin):
    list_display = ("name", "client_name", "organization", "created_at")
    list_filter = ("organization",)


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "organization",
        "matter",
        "category",
        "seen_by_boss",
        "handled",
        "created_at",
    )
    list_filter = ("organization", "category", "seen_by_boss", "handled")
    search_fields = ("title", "original_name", "note", "ai_summary")


@admin.register(DocumentComment)
class DocumentCommentAdmin(admin.ModelAdmin):
    list_display = ("document", "author", "created_at")
