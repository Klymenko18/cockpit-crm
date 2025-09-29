from django.contrib.postgres.indexes import GinIndex
from django.db import models


class EntityType(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "entity_type"
        indexes = [models.Index(fields=["is_active"])]


class Entity(models.Model):
    entity_uid = models.UUIDField()
    display_name = models.CharField(max_length=500)
    entity_type = models.ForeignKey(EntityType, on_delete=models.PROTECT)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField(null=True, blank=True)
    is_current = models.BooleanField(default=True)
    hashdiff = models.BinaryField()

    class Meta:
        db_table = "entity"
        indexes = [
            models.Index(fields=["entity_type", "is_current"]),
            models.Index(fields=["entity_uid", "valid_from"]),
            GinIndex(
                name="entity_display_name_trgm", fields=["display_name"], opclasses=["gin_trgm_ops"]
            ),
        ]
        constraints = []


class EntityDetail(models.Model):
    entity_uid = models.UUIDField()
    detail_code = models.CharField(max_length=100)
    value_json = models.JSONField()
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField(null=True, blank=True)
    is_current = models.BooleanField(default=True)
    hashdiff = models.BinaryField()

    class Meta:
        db_table = "entity_detail"
        indexes = [
            models.Index(fields=["entity_uid", "detail_code", "valid_from"]),
            GinIndex(fields=["value_json"], name="entity_detail_value_json_gin"),
        ]
        constraints = []
