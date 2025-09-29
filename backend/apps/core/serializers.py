from django.utils import timezone
from rest_framework import serializers

from apps.core.models import Entity, EntityDetail, EntityType
from apps.core.services.scd2 import UpsertResult, update_entity, update_entity_detail


class EntitySnapshotSerializer(serializers.ModelSerializer):

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
        qs = EntityDetail.objects.filter(entity_uid=obj.entity_uid, is_current=True).values(
            "detail_code", "value_json"
        )
        return {r["detail_code"]: r["value_json"] for r in qs}


class EntityUpsertSerializer(serializers.Serializer):


    entity_uid = serializers.UUIDField()
    display_name = serializers.CharField(max_length=500)
    entity_type = serializers.SlugRelatedField(slug_field="code", queryset=EntityType.objects.all())
    change_ts = serializers.DateTimeField(required=False, allow_null=True)

    def create(self, validated_data):
        actor = str(self.context.get("actor") or "api")
        change_ts = validated_data.get("change_ts") or timezone.now()

        entity_type_code = validated_data["entity_type"].code

        res: UpsertResult = update_entity(
            entity_uid=validated_data["entity_uid"],
            display_name=validated_data["display_name"],
            entity_type=entity_type_code, 
            change_ts=change_ts,
            actor=actor,
        )
        return {"status": res.status, "entity_uid": res.entity_uid, "valid_from": res.valid_from}

    def update(self, instance, validated_data):
        return self.create(validated_data)


class EntityDetailUpsertSerializer(serializers.Serializer):

    entity_uid = serializers.UUIDField()
    detail_code = serializers.CharField(max_length=100)
    value_json = serializers.JSONField()
    change_ts = serializers.DateTimeField(required=False, allow_null=True)

    def create(self, validated_data):
        actor = str(self.context.get("actor") or "api")
        change_ts = validated_data.get("change_ts") or timezone.now()

        res: UpsertResult = update_entity_detail(
            entity_uid=validated_data["entity_uid"],
            detail_code=validated_data["detail_code"],
            value_json=validated_data["value_json"],
            change_ts=change_ts,
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
