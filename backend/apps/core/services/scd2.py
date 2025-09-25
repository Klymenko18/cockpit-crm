from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Tuple, Optional

from django.db import transaction
from django.utils import timezone

from apps.core.models import Entity, EntityDetail, EntityType
from apps.core.utils.hashdiff import norm_str, norm_json, sha256_str

try:
    # Optional dependency: audit app may not be installed in all environments.
    from apps.audit.models import AuditLog  # type: ignore
except Exception:  # pragma: no cover
    AuditLog = None


@dataclass
class UpsertResult:
    """Result of an SCD2 operation.

    Attributes:
        status: One of {"created", "updated", "noop"}.
        entity_uid: Affected logical entity UUID (as string).
        detail_code: Affected detail code, if any.
        valid_from: Effective start timestamp of the resulting open version.
    """
    status: str
    entity_uid: Optional[str] = None
    detail_code: Optional[str] = None
    valid_from: Optional[Any] = None


def _audit_log(actor: str, action: str, entity_uid, detail_code=None, before=None, after=None, change_ts=None):
    """Write an optional audit record if the `audit` app is available.

    Args:
        actor: Who initiated the change (e.g., username or "api").
        action: Audit action code (e.g., "OPEN_ENTITY", "CLOSE_DETAIL").
        entity_uid: Target logical entity UUID.
        detail_code: Optional detail identifier.
        before: Optional dict of previous values.
        after: Optional dict of new values.
        change_ts: Effective time of change; defaults to now.
    """
    if AuditLog is None:
        return
    AuditLog.objects.create(
        actor=str(actor),
        action=action,
        entity_uid=entity_uid,
        detail_code=detail_code,
        before=before,
        after=after,
        change_ts=change_ts or timezone.now(),
    )


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


@transaction.atomic
def update_entity(*, entity_uid, display_name: str, entity_type: str, change_ts=None, actor="api") -> UpsertResult:
    """Idempotent SCD2 upsert for an Entity.

    Behavior:
        - If no current row exists: create the first version (`created`).
        - If the business hash did not change: do nothing (`noop`).
        - Otherwise: close current row at `change_ts` and open a new one (`updated`).

    Args:
        entity_uid: Logical entity UUID.
        display_name: New display name.
        entity_type: `EntityType.code` string.
        change_ts: Optional effective timestamp (defaults to now).
        actor: Audit actor string.

    Returns:
        UpsertResult describing the final state (status, entity_uid, valid_from).
    """
    if change_ts is None:
        change_ts = timezone.now()

    et = EntityType.objects.get(code=entity_type)

    current = Entity.objects.filter(entity_uid=entity_uid, is_current=True).select_for_update().first()
    new_hash = _entity_hash(display_name, et.id)

    if current:
        if current.hashdiff == new_hash:
            return UpsertResult(status="noop", entity_uid=str(entity_uid), valid_from=current.valid_from)

        before = {
            "display_name": current.display_name,
            "entity_type": current.entity_type.code if current.entity_type_id else None,
        }
        current.valid_to = change_ts
        current.is_current = False
        current.save(update_fields=["valid_to", "is_current"])
        _audit_log(actor, "CLOSE_ENTITY", entity_uid, before=before, after=None, change_ts=change_ts)

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
            actor, "OPEN_ENTITY", entity_uid,
            before=None, after={"display_name": display_name, "entity_type": et.code},
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
        actor, "OPEN_ENTITY", entity_uid,
        before=None, after={"display_name": display_name, "entity_type": et.code},
        change_ts=change_ts,
    )
    return UpsertResult(status="created", entity_uid=str(entity_uid), valid_from=obj.valid_from)


@transaction.atomic
def close_entity(*, entity_uid, change_ts=None, actor="api") -> Tuple[str, Optional[Any]]:
    """Close the current SCD2 version for an Entity (soft delete).

    Args:
        entity_uid: Logical entity UUID.
        change_ts: Optional effective time (defaults to now).
        actor: Audit actor.

    Returns:
        Tuple of (status, previous_valid_from). Status is "closed" or "noop".
    """
    if change_ts is None:
        change_ts = timezone.now()
    current = Entity.objects.filter(entity_uid=entity_uid, is_current=True).select_for_update().first()
    if not current:
        return "noop", None
    before = {
        "display_name": current.display_name,
        "entity_type": current.entity_type.code if current.entity_type_id else None,
    }
    current.valid_to = change_ts
    current.is_current = False
    current.save(update_fields=["valid_to", "is_current"])
    _audit_log(actor, "CLOSE_ENTITY", entity_uid, before=before, after=None, change_ts=change_ts)
    return "closed", current.valid_from


@transaction.atomic
def update_entity_detail(*, entity_uid, detail_code: str, value_json: Any, change_ts=None, actor="api") -> UpsertResult:
    """Idempotent SCD2 upsert for an EntityDetail.

    Args:
        entity_uid: Logical entity UUID.
        detail_code: Attribute key.
        value_json: New JSON value.
        change_ts: Optional effective time (defaults to now).
        actor: Audit actor.

    Returns:
        UpsertResult with status and effective valid_from.
    """
    if change_ts is None:
        change_ts = timezone.now()

    current = (
        EntityDetail.objects.filter(entity_uid=entity_uid, detail_code=detail_code, is_current=True)
        .select_for_update()
        .first()
    )
    new_hash = _detail_hash(value_json)

    if current:
        if current.hashdiff == new_hash:
            return UpsertResult(
                status="noop", entity_uid=str(entity_uid), detail_code=detail_code, valid_from=current.valid_from
            )

        before = {"value_json": current.value_json}
        current.valid_to = change_ts
        current.is_current = False
        current.save(update_fields=["valid_to", "is_current"])
        _audit_log(actor, "CLOSE_DETAIL", entity_uid, detail_code=detail_code, before=before, after=None, change_ts=change_ts)

        obj = EntityDetail.objects.create(
            entity_uid=entity_uid,
            detail_code=detail_code,
            value_json=value_json,
            valid_from=change_ts,
            valid_to=None,
            is_current=True,
            hashdiff=new_hash,
        )
        _audit_log(actor, "OPEN_DETAIL", entity_uid, detail_code=detail_code, before=None, after={"value_json": value_json}, change_ts=change_ts)
        return UpsertResult(status="updated", entity_uid=str(entity_uid), detail_code=detail_code, valid_from=obj.valid_from)

    obj = EntityDetail.objects.create(
        entity_uid=entity_uid,
        detail_code=detail_code,
        value_json=value_json,
        valid_from=change_ts,
        valid_to=None,
        is_current=True,
        hashdiff=new_hash,
    )
    _audit_log(actor, "OPEN_DETAIL", entity_uid, detail_code=detail_code, before=None, after={"value_json": value_json}, change_ts=change_ts)
    return UpsertResult(status="created", entity_uid=str(entity_uid), detail_code=detail_code, valid_from=obj.valid_from)


@transaction.atomic
def close_entity_detail(*, entity_uid, detail_code: str, change_ts=None, actor="api") -> Tuple[str, Optional[Any]]:
    """Close the current SCD2 version for a specific EntityDetail.

    Args:
        entity_uid: Logical entity UUID.
        detail_code: Attribute key to close.
        change_ts: Optional effective time (defaults to now).
        actor: Audit actor.

    Returns:
        Tuple of (status, previous_valid_from). Status is "closed" or "noop".
    """
    if change_ts is None:
        change_ts = timezone.now()
    current = (
        EntityDetail.objects.filter(entity_uid=entity_uid, detail_code=detail_code, is_current=True)
        .select_for_update()
        .first()
    )
    if not current:
        return "noop", None
    before = {"value_json": current.value_json}
    current.valid_to = change_ts
    current.is_current = False
    current.save(update_fields=["valid_to", "is_current"])
    _audit_log(actor, "CLOSE_DETAIL", entity_uid, detail_code=detail_code, before=before, after=None, change_ts=change_ts)
    return "closed", current.valid_from
