from rest_framework import serializers
from .models import AuditLog

class AuditLogSerializer(serializers.ModelSerializer):
    """Read-only serializer for audit records."""
    class Meta:
        model = AuditLog
        fields = (
            "id", "actor", "action", "entity_uid", "detail_code",
            "before", "after", "change_ts", "created_at",
        )
        read_only_fields = fields
