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
def test_entity_serializers_serialize_instance(make_entity):
    e = make_entity(display_name="Ser Alice")
    ser_classes = _collect_serializers_for(Entity)
    if not ser_classes:
        pytest.skip("No serializers for Entity in apps.core.serializers")

    for S in ser_classes:
        s = S(instance=e)
        data = s.data  
        assert isinstance(data, dict) and data, f"{S.__name__} returned empty data"
        assert any(isinstance(k, str) for k in data.keys())


@pytest.mark.django_db
def test_entity_serializers_many(make_entity):
    e1 = make_entity(display_name="E1")
    e2 = make_entity(display_name="E2")
    ser_classes = _collect_serializers_for(Entity)
    if not ser_classes:
        pytest.skip("No serializers for Entity in apps.core.serializers")

    for S in ser_classes:
        s = S(
            instance=Entity.objects.filter(entity_uid__in=[e1.entity_uid, e2.entity_uid]), many=True
        )
        data = s.data
        assert isinstance(data, list) and len(data) == 2
