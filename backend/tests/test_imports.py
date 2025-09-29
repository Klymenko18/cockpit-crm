import importlib


def test_imports_smoke():
    modules = [
        "apps.accounts.permissions",
        "apps.accounts.serializers",
        "apps.accounts.views",
        "apps.audit.admin",
        "apps.audit.models",
        "apps.core.admin",
        "apps.core.serializers",
        "apps.core.services.scd2",
        "apps.core.utils.hashdiff",
        "apps.core.views",
    ]
    for m in modules:
        importlib.import_module(m)
