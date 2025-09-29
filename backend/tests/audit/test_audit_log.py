import uuid

import pytest
from django.utils import timezone

from apps.audit.models import AuditLog
from apps.core.models import EntityType
from apps.core.services.scd2 import update_entity

pytestmark = pytest.mark.django_db


def test_audit_written_on_open_and_update():
    EntityType.objects.create(code="PERSON", name="Person")
    uid = uuid.uuid4()
    t0 = timezone.now()

    update_entity(
        entity_uid=uid, display_name="Bob", entity_type="PERSON", change_ts=t0, actor="test"
    )
    update_entity(
        entity_uid=uid, display_name="Bob B.", entity_type="PERSON", change_ts=t0, actor="test"
    )

    actions = list(AuditLog.objects.values_list("action", flat=True))
    assert actions.count("OPEN_ENTITY") >= 2
    assert actions.count("CLOSE_ENTITY") >= 1
