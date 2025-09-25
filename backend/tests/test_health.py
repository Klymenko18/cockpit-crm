import os
import pytest
from django.test import Client


@pytest.mark.django_db
def test_health_endpoint(settings):
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.ci")
    client = Client()
    resp = client.get("/health/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"