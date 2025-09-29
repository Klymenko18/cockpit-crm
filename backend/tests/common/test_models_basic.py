import pytest

from apps.core.models import EntityDetail, EntityType

pytestmark = pytest.mark.django_db


def test_entity_create_and_read(make_entity, person_type, now):
    e = make_entity(valid_from=now, display_name="Alice")
    assert e.pk is not None
    assert e.display_name == "Alice"
    assert e.entity_type == person_type
    assert e.is_current is True
    assert e.valid_from is not None


def test_entitydetail_create_and_link(make_entity, make_detail):
    e = make_entity(display_name="Bob")
    d = make_detail(e, detail_code="EMAIL", value_json={"email": "bob@example.com"})
    assert d.pk is not None
    assert d.entity_uid == e.entity_uid
    assert d.detail_code == "EMAIL"
    assert d.value_json.get("email") == "bob@example.com"
    cnt = EntityDetail.objects.filter(entity_uid=e.entity_uid).count()
    assert cnt == 1


def test_person_type_uniqueness(person_type):
    assert EntityType.objects.filter(code="PERSON").exists()
