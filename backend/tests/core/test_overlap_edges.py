
from datetime import timedelta

import pytest
from django.db import IntegrityError
from django.utils import timezone


@pytest.mark.db
def test_entity_touching_intervals_allowed(make_entity):
    t0 = timezone.now()
    t1 = t0 + timedelta(minutes=1)
    t2 = t1 + timedelta(minutes=1)

    e1 = make_entity(valid_from=t0, valid_to=t1)
    make_entity(entity_uid=e1.entity_uid, valid_from=t1, valid_to=t2)


@pytest.mark.db
def test_detail_touching_intervals_allowed(make_entity, make_detail):
    ent = make_entity()
    t0 = timezone.now()
    t1 = t0 + timedelta(minutes=1)
    t2 = t1 + timedelta(minutes=1)

    make_detail(ent, detail_code="EMAIL", valid_from=t0, valid_to=t1)
    make_detail(ent, detail_code="EMAIL", valid_from=t1, valid_to=t2)
