import pytest

from apps.core.models import Entity
from apps.core.serializers import EntitySnapshotSerializer

pytestmark = pytest.mark.db


def test_entity_snapshot_serializer_basic_fields(make_entity):
    e = make_entity(display_name="Alice")
    data = EntitySnapshotSerializer(e).data
    assert data["entity_uid"] == e.entity_uid
    assert data["display_name"] == "Alice"
    assert data["entity_type"] == e.entity_type.code
    assert data["is_current"] is True
    assert "details" in data


def test_entity_snapshot_serializer_with_details(make_entity, make_detail):
    e = make_entity()
    make_detail(e, detail_code="EMAIL", value_json={"email": "a@b.c"})
    make_detail(e, detail_code="PHONE", value_json={"phone": "+421"})
    data = EntitySnapshotSerializer(e).data
    assert data["details"] == {"EMAIL": {"email": "a@b.c"}, "PHONE": {"phone": "+421"}}


def test_entity_snapshot_serializer_without_details(make_entity):
    e = make_entity()
    data = EntitySnapshotSerializer(e).data
    assert data["details"] == {}
