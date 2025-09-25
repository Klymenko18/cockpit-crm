import uuid as uuidlib
from django.db import models

class EntityType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "entity_type"

    def __str__(self) -> str:
        return self.name

class Entity(models.Model):
    id = models.BigAutoField(primary_key=True)
    entity_uid = models.UUIDField(default=uuidlib.uuid4, editable=False)
    display_name = models.CharField(max_length=500)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField(null=True, blank=True)
    is_current = models.BooleanField(default=True)
    hashdiff = models.BinaryField()
    entity_type = models.ForeignKey(EntityType, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "entity"
        indexes = [
            models.Index(fields=["entity_uid", "valid_from"], name="entity_entity__d227b0_idx"),
            models.Index(fields=["entity_type", "is_current"], name="entity_entity__df9f7a_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.display_name} ({self.entity_uid})"

class EntityDetail(models.Model):
    id = models.BigAutoField(primary_key=True)
    entity_uid = models.UUIDField()
    detail_code = models.CharField(max_length=100)
    value_json = models.JSONField()
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField(null=True, blank=True)
    is_current = models.BooleanField(default=True)
    hashdiff = models.BinaryField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "entity_detail"
        indexes = [
            models.Index(fields=["entity_uid", "detail_code", "valid_from"], name="entity_deta_entity__b35e2e_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.entity_uid}::{self.detail_code}"
