from django.utils import timezone
from rest_framework import serializers
from apps.core.models import Entity, EntityDetail, EntityType
from apps.core.services.scd2 import update_entity, update_entity_detail

class EntitySnapshotSerializer(serializers.ModelSerializer):
    details = serializers.SerializerMethodField()
    entity_type = serializers.SlugRelatedField(slug_field="code", read_only=True)

    class Meta:
        model = Entity
        fields = ["entity_uid", "display_name", "entity_type", "valid_from", "valid_to", "is_current", "details"]

    def get_details(self, obj):
        qs = EntityDetail.objects.filter(entity_uid=obj.entity_uid, is_current=True).values("detail_code", "value_json")
        return {r["detail_code"]: r["value_json"] for r in qs}

class EntityUpsertSerializer(serializers.Serializer):
    entity_uid = serializers.UUIDField()
    display_name = serializers.CharField(max_length=500)
    entity_type = serializers.CharField(max_length=50)
    change_ts = serializers.DateTimeField(required=False)

    def create(self, validated_data):
        et = EntityType.objects.get(code=validated_data["entity_type"])
        status, _ = update_entity(
            change_ts=validated_data.get("change_ts") or timezone.now(),
            actor=str(self.context.get("actor") or "api"),
            payload={
                "entity_uid": validated_data["entity_uid"],
                "display_name": validated_data["display_name"],
                "entity_type_id": et.id,
            },
        )
        return {"status": status}

    def update(self, instance, validated_data):
        return self.create(validated_data)

class EntityDetailUpsertSerializer(serializers.Serializer):
    entity_uid = serializers.UUIDField()
    detail_code = serializers.CharField(max_length=100)
    value_json = serializers.JSONField()
    change_ts = serializers.DateTimeField(required=False)

    def create(self, validated_data):
        status, _ = update_entity_detail(
            change_ts=validated_data.get("change_ts") or timezone.now(),
            actor=str(self.context.get("actor") or "api"),
            payload=validated_data,
        )
        return {"status": status}

    def update(self, instance, validated_data):
        return self.create(validated_data)
