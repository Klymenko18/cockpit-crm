from django.contrib import admin

from .models import Entity, EntityDetail


@admin.register(Entity)
class EntityAdmin(admin.ModelAdmin):
    list_display = (
        "entity_uid",
        "entity_type",
        "display_name",
        "is_current",
        "valid_from",
        "valid_to",
        "created_at",
    )
    list_filter = ("entity_type", "is_current")
    search_fields = ("entity_uid", "display_name")
    date_hierarchy = "valid_from"
    ordering = ("-valid_from",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(EntityDetail)
class EntityDetailAdmin(admin.ModelAdmin):
    list_display = (
        "entity_uid",
        "detail_code",
        "value_short",
        "is_current",
        "valid_from",
        "valid_to",
        "hashdiff",
    )
    list_filter = ("detail_code", "is_current")
    search_fields = ("entity_uid", "detail_code", "value")
    date_hierarchy = "valid_from"
    ordering = ("-valid_from",)
    readonly_fields = ("hashdiff", "created_at", "updated_at")

    def value_short(self, obj):
        v = obj.value or ""
        return (v[:80] + "…") if len(v) > 80 else v

    value_short.short_description = "value"
