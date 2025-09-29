from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal, Optional, Tuple

from django.db import IntegrityError, transaction
from django.db.models import BinaryField, CharField
from django.utils import timezone

from apps.core.models import Entity, EntityDetail, EntityType
from apps.core.utils.hashdiff import norm_json, norm_str, sha256_str

try:
    from apps.audit.models import AuditLog  
except Exception:  
    AuditLog = None



def _ensure_aware(ts: Optional[datetime]) -> datetime:
    """Return an aware timestamp in the current timezone."""
    if ts is None:
        return timezone.now()
    if timezone.is_naive(ts):
        return timezone.make_aware(ts, timezone.get_current_timezone())
    return ts


def _adapt_hash_for_field(model_cls, field_name: str, hex_digest: str) -> bytes | str:
    """Convert a hex digest to the correct DB representation for the model field.

    - If model field is BinaryField -> return raw bytes.
    - If model field is CharField  -> return hex string.
    """
    f = model_cls._meta.get_field(field_name)
    if isinstance(f, BinaryField):
        return bytes.fromhex(hex_digest)
    if isinstance(f, CharField):
        return hex_digest
    return hex_digest


def _entity_hash(display_name: str | None, entity_type_id: int | None) -> str:
    """Compute a hex SHA-256 over normalized business fields of an Entity."""
    base = {
        "display_name": norm_str(display_name),
        "entity_type_id": entity_type_id,
    }
    return sha256_str(norm_json(base))


def _detail_hash(value_json: Any) -> str:
    """Compute a hex SHA-256 over normalized JSON value of a detail."""
    return sha256_str(norm_json(value_json))


def _audit_log(
    actor: str,
    action: str,
    entity_uid,
    detail_code: str | None = None,
    before: dict | None = None,
    after: dict | None = None,
    change_ts: Optional[datetime] = None,
) -> None:
    """Write an optional audit record if the `audit` app is available."""
    if AuditLog is None:
        return
    AuditLog.objects.create(
        actor=str(actor),
        action=action,
        entity_uid=entity_uid,
        detail_code=detail_code,
        before=before,
        after=after,
        change_ts=_ensure_aware(change_ts),
    )


@dataclass
class UpsertResult:
    """Result of an SCD2 operation.

    Attributes:
        status: One of {"created", "updated", "noop"}.
        entity_uid: Affected logical entity UUID (as string).
        detail_code: Affected detail code, if any.
        valid_from: Effective start timestamp of the resulting open version.
    """

    status: Literal["created", "updated", "noop"]
    entity_uid: Optional[str] = None
    detail_code: Optional[str] = None
    valid_from: Optional[Any] = None


@transaction.atomic
def update_entity(
    *,
    entity_uid,
    display_name: str,
    entity_type: str,
    change_ts: Optional[datetime] = None,
    actor: str = "api",
) -> UpsertResult:
    """Idempotent SCD2 upsert for an Entity.

    Behavior:
        - If no current row exists: create the first version (`created`).
        - If the business hash did not change: do nothing (`noop`).
        - Otherwise: close current row at `change_ts` and open a new one (`updated`).
    """
    change_ts = _ensure_aware(change_ts)

    et = EntityType.objects.get(code=entity_type)
    current = (
        Entity.objects.filter(entity_uid=entity_uid, is_current=True).select_for_update().first()
    )
    new_hash_hex = _entity_hash(display_name, et.id)
    new_hash = _adapt_hash_for_field(Entity, "hashdiff", new_hash_hex)

    if current:
        if current.hashdiff == new_hash:
            return UpsertResult(
                status="noop", entity_uid=str(entity_uid), valid_from=current.valid_from
            )

    
        before = {
            "display_name": current.display_name,
            "entity_type": current.entity_type.code if current.entity_type_id else None,
        }
        updated = Entity.objects.filter(id=current.id, is_current=True).update(
            valid_to=change_ts, is_current=False
        )
        if updated != 1:
            fresh = Entity.objects.filter(entity_uid=entity_uid, is_current=True).first()
            return UpsertResult(
                status="noop",
                entity_uid=str(entity_uid),
                valid_from=fresh.valid_from if fresh else None,
            )

        _audit_log(
            actor, "CLOSE_ENTITY", entity_uid, before=before, after=None, change_ts=change_ts
        )

        try:
            obj = Entity.objects.create(
                entity_uid=entity_uid,
                display_name=display_name,
                entity_type=et,
                valid_from=change_ts,
                valid_to=None,
                is_current=True,
                hashdiff=new_hash,
            )
        except IntegrityError:
            obj = Entity.objects.filter(entity_uid=entity_uid, is_current=True).first()
            return UpsertResult(
                status="noop",
                entity_uid=str(entity_uid),
                valid_from=obj.valid_from if obj else None,
            )

        _audit_log(
            actor,
            "OPEN_ENTITY",
            entity_uid,
            before=None,
            after={"display_name": display_name, "entity_type": et.code},
            change_ts=change_ts,
        )
        return UpsertResult(status="updated", entity_uid=str(entity_uid), valid_from=obj.valid_from)

    obj = Entity.objects.create(
        entity_uid=entity_uid,
        display_name=display_name,
        entity_type=et,
        valid_from=change_ts,
        valid_to=None,
        is_current=True,
        hashdiff=new_hash,
    )
    _audit_log(
        actor,
        "OPEN_ENTITY",
        entity_uid,
        before=None,
        after={"display_name": display_name, "entity_type": et.code},
        change_ts=change_ts,
    )
    return UpsertResult(status="created", entity_uid=str(entity_uid), valid_from=obj.valid_from)


@transaction.atomic
def close_entity(
    *,
    entity_uid,
    change_ts: Optional[datetime] = None,
    actor: str = "api",
) -> Tuple[Literal["closed", "noop"], Optional[Any]]:
    """Close the current SCD2 version for an Entity (soft delete)."""
    change_ts = _ensure_aware(change_ts)
    current = (
        Entity.objects.filter(entity_uid=entity_uid, is_current=True).select_for_update().first()
    )
    if not current:
        return "noop", None

    before = {
        "display_name": current.display_name,
        "entity_type": current.entity_type.code if current.entity_type_id else None,
    }
    updated = Entity.objects.filter(id=current.id, is_current=True).update(
        valid_to=change_ts, is_current=False
    )
    if updated != 1:
        return "noop", None

    _audit_log(actor, "CLOSE_ENTITY", entity_uid, before=before, after=None, change_ts=change_ts)
    return "closed", current.valid_from


@transaction.atomic
def update_entity_detail(
    *,
    entity_uid,
    detail_code: str,
    value_json: Any,
    change_ts: Optional[datetime] = None,
    actor: str = "api",
) -> UpsertResult:
    """Idempotent SCD2 upsert for an EntityDetail keyed by (entity_uid, detail_code)."""
    change_ts = _ensure_aware(change_ts)

    current = (
        EntityDetail.objects.filter(entity_uid=entity_uid, detail_code=detail_code, is_current=True)
        .select_for_update()
        .first()
    )
    new_hash_hex = _detail_hash(value_json)
    new_hash = _adapt_hash_for_field(EntityDetail, "hashdiff", new_hash_hex)

    if current:
        if current.hashdiff == new_hash:
            return UpsertResult(
                status="noop",
                entity_uid=str(entity_uid),
                detail_code=detail_code,
                valid_from=current.valid_from,
            )

        before = {"value_json": current.value_json}
        updated = EntityDetail.objects.filter(id=current.id, is_current=True).update(
            valid_to=change_ts, is_current=False
        )
        if updated != 1:
            fresh = EntityDetail.objects.filter(
                entity_uid=entity_uid, detail_code=detail_code, is_current=True
            ).first()
            return UpsertResult(
                status="noop",
                entity_uid=str(entity_uid),
                detail_code=detail_code,
                valid_from=fresh.valid_from if fresh else None,
            )

        _audit_log(
            actor,
            "CLOSE_DETAIL",
            entity_uid,
            detail_code=detail_code,
            before=before,
            after=None,
            change_ts=change_ts,
        )

        try:
            obj = EntityDetail.objects.create(
                entity_uid=entity_uid,
                detail_code=detail_code,
                value_json=value_json,
                valid_from=change_ts,
                valid_to=None,
                is_current=True,
                hashdiff=new_hash,
            )
        except IntegrityError:
            obj = EntityDetail.objects.filter(
                entity_uid=entity_uid, detail_code=detail_code, is_current=True
            ).first()
            return UpsertResult(
                status="noop",
                entity_uid=str(entity_uid),
                detail_code=detail_code,
                valid_from=obj.valid_from if obj else None,
            )

        _audit_log(
            actor,
            "OPEN_DETAIL",
            entity_uid,
            detail_code=detail_code,
            before=None,
            after={"value_json": value_json},
            change_ts=change_ts,
        )
        return UpsertResult(
            status="updated",
            entity_uid=str(entity_uid),
            detail_code=detail_code,
            valid_from=obj.valid_from,
        )
    obj = EntityDetail.objects.create(
        entity_uid=entity_uid,
        detail_code=detail_code,
        value_json=value_json,
        valid_from=change_ts,
        valid_to=None,
        is_current=True,
        hashdiff=new_hash,
    )
    _audit_log(
        actor,
        "OPEN_DETAIL",
        entity_uid,
        detail_code=detail_code,
        before=None,
        after={"value_json": value_json},
        change_ts=change_ts,
    )
    return UpsertResult(
        status="created",
        entity_uid=str(entity_uid),
        detail_code=detail_code,
        valid_from=obj.valid_from,
    )


@transaction.atomic
def close_entity_detail(
    *,
    entity_uid,
    detail_code: str,
    change_ts: Optional[datetime] = None,
    actor: str = "api",
) -> Tuple[Literal["closed", "noop"], Optional[Any]]:
    """Close the current SCD2 version for a specific EntityDetail."""
    change_ts = _ensure_aware(change_ts)
    current = (
        EntityDetail.objects.filter(entity_uid=entity_uid, detail_code=detail_code, is_current=True)
        .select_for_update()
        .first()
    )
    if not current:
        return "noop", None

    before = {"value_json": current.value_json}
    updated = EntityDetail.objects.filter(id=current.id, is_current=True).update(
        valid_to=change_ts, is_current=False
    )
    if updated != 1:
        return "noop", None

    _audit_log(
        actor,
        "CLOSE_DETAIL",
        entity_uid,
        detail_code=detail_code,
        before=before,
        after=None,
        change_ts=change_ts,
    )
    return "closed", current.valid_from
