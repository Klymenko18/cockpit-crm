import uuid

import pytest
from django.utils import timezone

from apps.core.models import Entity, EntityType
from apps.core.services.scd2 import close_entity, update_entity

pytestmark = pytest.mark.django_db


def test_entity_upsert_and_close():
    et = EntityType.objects.create(code="PERSON", name="Person")
    uid = uuid.uuid4()
    t0 = timezone.now()

    r1 = update_entity(entity_uid=uid, display_name="Alice", entity_type="PERSON", change_ts=t0)
    assert r1.status == "created"
    e = Entity.objects.get(entity_uid=uid, is_current=True)
    assert e.display_name == "Alice"

    r2 = update_entity(entity_uid=uid, display_name="Alice", entity_type="PERSON", change_ts=t0)
    assert r2.status == "noop"
    assert Entity.objects.filter(entity_uid=uid, is_current=True).count() == 1

    t1 = t0 + timezone.timedelta(seconds=10)
    r3 = update_entity(entity_uid=uid, display_name="Alice B.", entity_type="PERSON", change_ts=t1)
    assert r3.status == "updated"
    assert Entity.objects.filter(entity_uid=uid, is_current=True).get().display_name == "Alice B."
    assert Entity.objects.filter(entity_uid=uid, is_current=False).count() == 1
    status, prev_from = close_entity(entity_uid=uid, change_ts=t1 + timezone.timedelta(seconds=5))
    assert status == "closed"
    assert Entity.objects.filter(entity_uid=uid, is_current=True).count() == 0
