from django.utils import timezone
from rest_framework import serializers

from apps.core.models import Entity, EntityDetail, EntityType
from apps.core.services.scd2 import update_entity, update_entity_detail, UpsertResult


class EntitySnapshotSerializer(serializers.ModelSerializer):
    """Serializer for the current snapshot of an entity with its current details.

    The `details` field is computed at read time by collecting all current
    `EntityDetail` rows for the entity and returning them as a flat dict
    `{detail_code: value_json}`.
    """
    details = serializers.SerializerMethodField()
    entity_type = serializers.SlugRelatedField(slug_field="code", read_only=True)

    class Meta:
        model = Entity
        fields = [
            "entity_uid",
            "display_name",
            "entity_type",
            "valid_from",
            "valid_to",
            "is_current",
            "details",
        ]

    def get_details(self, obj):
        qs = EntityDetail.objects.filter(
            entity_uid=obj.entity_uid, is_current=True
        ).values("detail_code", "value_json")
        return {r["detail_code"]: r["value_json"] for r in qs}


class EntityUpsertSerializer(serializers.Serializer):
    """Idempotent SCD2 upsert for an Entity.

    On equal hashdiff (no business change) it yields `noop`, otherwise it
    closes the current version and opens a new one.

    Fields:
        entity_uid: Target logical entity UUID.
        display_name: New display name.
        entity_type: EntityType code.
        change_ts: Optional effective time of change (defaults to now).
    """
    entity_uid = serializers.UUIDField()
    display_name = serializers.CharField(max_length=500)
    entity_type = serializers.CharField(max_length=50)
    change_ts = serializers.DateTimeField(required=False)

    def create(self, validated_data):
        actor = str(self.context.get("actor") or "api")
        res: UpsertResult = update_entity(
            entity_uid=validated_data["entity_uid"],
            display_name=validated_data["display_name"],
            entity_type=validated_data["entity_type"],
            change_ts=validated_data.get("change_ts") or timezone.now(),
            actor=actor,
        )
        return {"status": res.status, "entity_uid": res.entity_uid, "valid_from": res.valid_from}

    def update(self, instance, validated_data):
        return self.create(validated_data)


class EntityDetailUpsertSerializer(serializers.Serializer):
    """Idempotent SCD2 upsert for an EntityDetail.

    Fields:
        entity_uid: Logical entity UUID.
        detail_code: Attribute key.
        value_json: Attribute value.
        change_ts: Optional effective time of change (defaults to now).
    """
    entity_uid = serializers.UUIDField()
    detail_code = serializers.CharField(max_length=100)
    value_json = serializers.JSONField()
    change_ts = serializers.DateTimeField(required=False)

    def create(self, validated_data):
        actor = str(self.context.get("actor") or "api")
        res: UpsertResult = update_entity_detail(
            entity_uid=validated_data["entity_uid"],
            detail_code=validated_data["detail_code"],
            value_json=validated_data["value_json"],
            change_ts=validated_data.get("change_ts") or timezone.now(),
            actor=actor,
        )
        return {
            "status": res.status,
            "entity_uid": res.entity_uid,
            "detail_code": res.detail_code,
            "valid_from": res.valid_from,
        }

    def update(self, instance, validated_data):
        return self.create(validated_data)
