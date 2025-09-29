# -*- coding: utf-8 -*-
import pytest
from django.apps import apps as django_apps
from rest_framework import serializers as drf_serializers

serializers_mod = pytest.importorskip("apps.core.serializers")
Entity = django_apps.get_model("core", "Entity")
EntityDetail = django_apps.get_model("core", "EntityDetail")


def _collect_serializers():
    classes = []
    for name in dir(serializers_mod):
        obj = getattr(serializers_mod, name)
        if isinstance(obj, type) and issubclass(obj, drf_serializers.BaseSerializer):
            classes.append(obj)
    return classes


@pytest.mark.django_db
def test_any_core_serializer_handles_instance(make_entity, make_detail):
    ser_classes = _collect_serializers()
    if not ser_classes:
        pytest.skip("No serializers in apps.core.serializers")

    e = make_entity(display_name="ShapeEntity")
    d = make_detail(e, detail_code="EMAIL")

    for S in ser_classes:
        Meta = getattr(S, "Meta", None)
        model = getattr(Meta, "model", None) if Meta else None
        if model is None:
            S()
            continue
        instance = None
        if model is Entity:
            instance = e
        elif model is EntityDetail:
            instance = d
        if instance is not None:
            s = S(instance=instance)
            data = s.data
            assert data and isinstance(data, dict)
