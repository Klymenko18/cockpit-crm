import uuid as uuidlib

from django.db import models


class EntityType(models.Model):
    """Lookup table for domain entity types.

    Attributes:
        name: Human-readable name of the entity type.
        code: Stable short code used in APIs and configs.
        is_active: Whether this type is available for use.
    """

    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "entity_type"

    def __str__(self) -> str:
        return self.name


class Entity(models.Model):
    """SCD2 table for entities (Slowly Changing Dimension, type 2).

    Each logical entity is identified by a stable `entity_uid`. Every change to
    business-relevant fields opens a new version row and closes the previous one.

    Attributes:
        entity_uid: Stable UUID for the logical entity (not the row PK).
        display_name: Current display name (business field).
        valid_from: Version start timestamp (inclusive).
        valid_to: Version end timestamp (exclusive); NULL means open-ended.
        is_current: Convenience flag for the open version.
        hashdiff: Hex SHA-256 hash over normalized business fields for idempotency.
        entity_type: Foreign key to `EntityType`.
        created_at/updated_at: Audit timestamps for the row itself.
    Indexes:
        - (entity_uid, valid_from): efficient version lookups.
        - (entity_type, is_current): efficient filtering by type for current rows.
    """

    id = models.BigAutoField(primary_key=True)
    entity_uid = models.UUIDField(default=uuidlib.uuid4, editable=False)
    display_name = models.CharField(max_length=500)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField(null=True, blank=True)
    is_current = models.BooleanField(default=True)
    hashdiff = models.CharField(max_length=64)  
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
    """SCD2 table for entity attributes (key/value per version).

    Attributes:
        entity_uid: Foreign reference to the logical entity (UUID).
        detail_code: Attribute key (e.g., "phone", "email").
        value_json: Attribute value stored as JSON (flexible schema).
        valid_from/valid_to/is_current/hashdiff: Same SCD2 semantics as `Entity`.
    Indexes:
        - (entity_uid, detail_code, valid_from): version scans per attribute.
    """

    id = models.BigAutoField(primary_key=True)
    entity_uid = models.UUIDField()
    detail_code = models.CharField(max_length=100)
    value_json = models.JSONField()
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField(null=True, blank=True)
    is_current = models.BooleanField(default=True)
    hashdiff = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "entity_detail"
        indexes = [
            models.Index(
                fields=["entity_uid", "detail_code", "valid_from"],
                name="entity_deta_entity__b35e2e_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.entity_uid}::{self.detail_code}"
