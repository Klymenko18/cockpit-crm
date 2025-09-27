from __future__ import annotations

from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """
    Admin configuration for audit log entries.

    Shows key attributes and makes the view read-only by default,
    as audit records should not be edited manually.
    """
    list_display = ("change_ts", "actor", "action", "entity_uid", "detail_code")
    list_filter = ("action", "actor", "detail_code")
    search_fields = ("actor", "action", "entity_uid", "detail_code")
    date_hierarchy = "change_ts"

    readonly_fields = (
        "change_ts",
        "actor",
        "action",
        "entity_uid",
        "detail_code",
        "before",
        "after",
    )

    fieldsets = (
        ("When & Who", {"fields": ("change_ts", "actor", "action")}),
        ("Target", {"fields": ("entity_uid", "detail_code")}),
        ("Payload", {"fields": ("before", "after")}),
    )

    def has_add_permission(self, request):
        return False  # disallow manual creation from admin

    def has_change_permission(self, request, obj=None):
        return False  # read-only

    def has_delete_permission(self, request, obj=None):
        return False  # keep auditing immutable
