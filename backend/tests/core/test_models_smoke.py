import pytest

from apps.core.models import Entity, EntityDetail


@pytest.mark.db
def test_create_entity(make_entity):
    e = make_entity(display_name="Alice")
    assert isinstance(e, Entity)
    assert e.display_name == "Alice"
    assert e.is_current is True
    assert e.valid_from is not None


@pytest.mark.db
def test_create_detail(make_entity, make_detail):
    e = make_entity()
    d = make_detail(e, detail_code="EMAIL", value_json={"email": "a@b.c"})
    assert isinstance(d, EntityDetail)
    assert d.entity_uid == e.entity_uid
    assert d.detail_code == "EMAIL"
    assert d.value_json.get("email") == "a@b.c"
    assert d.is_current is True
