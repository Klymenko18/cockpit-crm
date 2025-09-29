import pytest
from django.db import IntegrityError
from django.utils import timezone

from apps.core.models import Entity, EntityDetail, EntityType

pytestmark = pytest.mark.pg_only


@pytest.mark.db
def test_entity_overlap_exclusion(db):
    et = EntityType.objects.create(code="PERSON", name="Person")
    now = timezone.now()

    Entity.objects.create(
        entity_uid="e1",
        display_name="John",
        entity_type=et,
        valid_from=now,
        valid_to=None,
        is_current=True,
        hashdiff="h1",
    )


    with pytest.raises(IntegrityError):
        Entity.objects.create(
            entity_uid="e1",
            display_name="John v2",
            entity_type=et,
            valid_from=now,  
            valid_to=None,
            is_current=True,
            hashdiff="h2",
        )


@pytest.mark.db
def test_detail_overlap_exclusion(db):
    et = EntityType.objects.create(code="PERSON", name="Person")
    now = timezone.now()

    e = Entity.objects.create(
        entity_uid="e2",
        display_name="Jane",
        entity_type=et,
        valid_from=now,
        valid_to=None,
        is_current=True,
        hashdiff="he",
    )

    EntityDetail.objects.create(
        entity_uid=e.entity_uid,
        detail_code="EMAIL",
        value_json={"email": "a@b.com"},
        valid_from=now,
        valid_to=None,
        is_current=True,
        hashdiff="hd1",
    )

    with pytest.raises(IntegrityError):
        EntityDetail.objects.create(
            entity_uid=e.entity_uid,
            detail_code="EMAIL",
            value_json={"email": "a2@b.com"},
            valid_from=now,  
            valid_to=None,
            is_current=True,
            hashdiff="hd2",
        )
