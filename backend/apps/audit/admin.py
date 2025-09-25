from django.contrib import admin
from .models import AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Read-only admin for audit log."""
    list_display = ("change_ts", "actor", "action", "entity_uid", "detail_code")
    list_filter = ("action",)
    search_fields = ("actor", "entity_uid", "detail_code")
    readonly_fields = [f.name for f in AuditLog._meta.fields]

    def has_add_permission(self, request):  # type: ignore[override]
        return False
    def has_change_permission(self, request, obj=None):  # type: ignore[override]
        return False
    def has_delete_permission(self, request, obj=None):  # type: ignore[override]
        return False
