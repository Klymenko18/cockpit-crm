from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Tuple, Optional

from django.db import transaction
from django.utils import timezone

from apps.core.models import Entity, EntityDetail, EntityType
from apps.core.utils.hashdiff import norm_str, norm_json, sha256_str

try:
    from apps.audit.models import AuditLog
except Exception:
    AuditLog = None 


@dataclass
class UpsertResult:
    status: str  
    entity_uid: Optional[str] = None
    detail_code: Optional[str] = None
    valid_from: Optional[Any] = None


def _audit_log(actor: str, action: str, entity_uid, detail_code=None, before=None, after=None, change_ts=None):
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
    base = {
        "display_name": norm_str(display_name),
        "entity_type_id": entity_type_id,
    }
    return sha256_str(norm_json(base))


def _detail_hash(value_json: Any) -> str:
    return sha256_str(norm_json(value_json))


@transaction.atomic
def update_entity(*, entity_uid, display_name: str, entity_type: str, change_ts=None, actor="api") -> UpsertResult:
    """
    Idempotent SCD2 upsert for Entity.
    - If no current row: create first version.
    - If current exists and business value unchanged: NOOP (idempotent).
    - Else: close current at change_ts and open new.
    """
    if change_ts is None:
        change_ts = timezone.now()

    et = EntityType.objects.get(code=entity_type)

    current = Entity.objects.filter(entity_uid=entity_uid, is_current=True).select_for_update().first()
    new_hash = _entity_hash(display_name, et.id)

    if current:
        if current.hashdiff == new_hash:
            if current.valid_from == change_ts or change_ts <= current.valid_from:
                return UpsertResult(status="noop", entity_uid=str(entity_uid), valid_from=current.valid_from)
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
        _audit_log(actor, "OPEN_ENTITY", entity_uid, before=None, after={"display_name": display_name, "entity_type": et.code}, change_ts=change_ts)
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
    _audit_log(actor, "OPEN_ENTITY", entity_uid, before=None, after={"display_name": display_name, "entity_type": et.code}, change_ts=change_ts)
    return UpsertResult(status="created", entity_uid=str(entity_uid), valid_from=obj.valid_from)


@transaction.atomic
def close_entity(*, entity_uid, change_ts=None, actor="api") -> Tuple[str, Optional[Any]]:
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
    """
    Idempotent SCD2 upsert for EntityDetail.
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
            if current.valid_from == change_ts or change_ts <= current.valid_from:
                return UpsertResult(status="noop", entity_uid=str(entity_uid), detail_code=detail_code, valid_from=current.valid_from)
            return UpsertResult(status="noop", entity_uid=str(entity_uid), detail_code=detail_code, valid_from=current.valid_from)

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
