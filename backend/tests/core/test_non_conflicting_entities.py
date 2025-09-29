from datetime import timedelta

from django.utils import timezone


def test_entities_with_different_uids_can_overlap(make_entity):
    t0 = timezone.now()
    t1 = t0 + timedelta(minutes=5)
    make_entity(valid_from=t0, valid_to=t1)
    make_entity(valid_from=t0, valid_to=t1)
