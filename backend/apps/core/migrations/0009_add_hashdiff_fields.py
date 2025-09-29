import hashlib
import json

from django.contrib.postgres.fields import JSONField
from django.db import migrations, models
from django.db.models import F


def _norm_str(s: str) -> str:
    if s is None:
        return ""
    return " ".join(str(s).strip().split()).lower()


def _norm_json(v):
    return json.dumps(v, sort_keys=True, separators=(",", ":"))


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def forwards(apps, schema_editor):
    Entity = apps.get_model("core", "Entity")
    EntityDetail = apps.get_model("core", "EntityDetail")
    for e in Entity.objects.all().only("id", "display_name", "entity_type_id"):
        base = {
            "display_name": _norm_str(e.display_name),
            "entity_type_id": e.entity_type_id,
        }
        e.hashdiff = _sha256(json.dumps(base, sort_keys=True, separators=(",", ":")))
        e.save(update_fields=["hashdiff"])

    for d in EntityDetail.objects.all().only("id", "value_json"):
        base = _norm_json(d.value_json)
        d.hashdiff = _sha256(base)
        d.save(update_fields=["hashdiff"])


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0007_enable_extensions"),
    ]

    operations = [
        migrations.AddField(
            model_name="entity",
            name="hashdiff",
            field=models.CharField(max_length=64, null=True, blank=True, db_index=True),
        ),
        migrations.AddField(
            model_name="entitydetail",
            name="hashdiff",
            field=models.CharField(max_length=64, null=True, blank=True, db_index=True),
        ),
        migrations.RunPython(forwards, backwards),
    ]
