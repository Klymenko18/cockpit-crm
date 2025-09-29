# -*- coding: utf-8 -*-
import pytest
from django.apps import apps as django_apps
from rest_framework import serializers as drf_serializers

serializers_mod = pytest.importorskip("apps.core.serializers")
Entity = django_apps.get_model("core", "Entity")
EntityDetail = django_apps.get_model("core", "EntityDetail")


def _collect_serializers_for(model_cls):
    found = []
    for name in dir(serializers_mod):
        obj = getattr(serializers_mod, name)
        if isinstance(obj, type) and issubclass(obj, drf_serializers.BaseSerializer):
            Meta = getattr(obj, "Meta", None)
            if Meta is not None and getattr(Meta, "model", None) is model_cls:
                found.append(obj)
    return found


@pytest.mark.django_db
def test_detail_serializers_serialize_instance(make_entity, make_detail):
    e = make_entity(display_name="Ser Bob")
    d = make_detail(e, detail_code="EMAIL", value_json={"email": "serbob@example.com"})
    ser_classes = _collect_serializers_for(EntityDetail)
    if not ser_classes:
        pytest.skip("No serializers for EntityDetail in apps.core.serializers")

    for S in ser_classes:
        s = S(instance=d)
        data = s.data
        assert isinstance(data, dict) and data
        assert any(isinstance(k, str) for k in data.keys())


@pytest.mark.django_db
def test_detail_serializers_many(make_entity, make_detail):
    e = make_entity(display_name="Ser Carol")
    d1 = make_detail(e, detail_code="EMAIL", value_json={"email": "c1@example.com"})
    d2 = make_detail(e, detail_code="PHONE", value_json={"phone": "+123"})
    ser_classes = _collect_serializers_for(EntityDetail)
    if not ser_classes:
        pytest.skip("No serializers for EntityDetail in apps.core.serializers")

    for S in ser_classes:
        s = S(instance=EntityDetail.objects.filter(pk__in=[d1.pk, d2.pk]), many=True)
        data = s.data
        assert isinstance(data, list) and len(data) == 2
