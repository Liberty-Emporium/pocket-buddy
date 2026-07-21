from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Organization, User


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "display_name", "created_at")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "role", "organization", "is_staff")
    list_filter = ("role", "organization", "is_staff")
    fieldsets = UserAdmin.fieldsets + (
        ("Pocket Assistant", {"fields": ("organization", "role")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Pocket Assistant", {"fields": ("organization", "role")}),
    )
