from rest_framework import serializers

from apps.audit.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(source="change_ts", read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "created_at",
            "actor",
            "action",
            "entity_uid",
            "detail_code",
            "before",
            "after",
        ]
        read_only_fields = fields
