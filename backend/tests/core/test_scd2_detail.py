import uuid

import pytest
from django.utils import timezone

from apps.core.models import EntityType
from apps.core.services.scd2 import close_entity_detail, update_entity, update_entity_detail

pytestmark = pytest.mark.django_db


def test_detail_upsert_and_close():
    EntityType.objects.create(code="PERSON", name="Person")
    uid = uuid.uuid4()
    t0 = timezone.now()

    update_entity(entity_uid=uid, display_name="Alice", entity_type="PERSON", change_ts=t0)

    r1 = update_entity_detail(
        entity_uid=uid, detail_code="email", value_json="a@ex.com", change_ts=t0
    )
    assert r1.status == "created"

    r2 = update_entity_detail(
        entity_uid=uid, detail_code="email", value_json="a@ex.com", change_ts=t0
    )
    assert r2.status == "noop"

    r3 = update_entity_detail(
        entity_uid=uid, detail_code="email", value_json="b@ex.com", change_ts=t0
    )
    assert r3.status == "updated"

    st, _ = close_entity_detail(entity_uid=uid, detail_code="email", change_ts=t0)
    assert st == "closed"
