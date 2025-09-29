import os
import uuid

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.core.models import Entity, EntityDetail, EntityType


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def now():
    return timezone.now()


@pytest.fixture
def person_type(db):
    return EntityType.objects.create(code="PERSON", name="Person")


@pytest.fixture
def make_entity(db, person_type, now):
    def _make_entity(
        entity_uid=None,
        display_name="John Doe",
        valid_from=None,
        valid_to=None,
        is_current=True,
        hashdiff="hash-entity-v1",
    ):
        return Entity.objects.create(
            entity_uid=entity_uid or str(uuid.uuid4()),
            display_name=display_name,
            entity_type=person_type,
            valid_from=valid_from or now,
            valid_to=valid_to,
            is_current=is_current,
            hashdiff=hashdiff,
        )

    return _make_entity


@pytest.fixture
def make_detail(db, now):
    def _make_detail(
        entity,
        detail_code="EMAIL",
        value_json=None,
        valid_from=None,
        valid_to=None,
        is_current=True,
        hashdiff="hash-detail-v1",
    ):
        return EntityDetail.objects.create(
            entity_uid=entity.entity_uid,
            detail_code=detail_code,
            value_json=value_json if value_json is not None else {"email": "john@example.com"},
            valid_from=valid_from or now,
            valid_to=valid_to,
            is_current=is_current,
            hashdiff=hashdiff,
        )

    return _make_detail

collect_ignore_glob = [
    "tests/test_health.py",
    "tests/common/test_health_*.py",
    "tests/common/test_apps_registry.py",
    "tests/common/test_settings_loaded.py",
    "tests/common/test_urls_reverse.py",
    "tests/core/test_admin_registration.py",
    "tests/core/test_hash_module_dynamic.py",
]
