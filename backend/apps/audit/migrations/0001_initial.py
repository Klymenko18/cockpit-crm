from __future__ import annotations

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Initial migration for the audit app: minimal immutable audit trail table.
    """

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="AuditLog",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                (
                    "change_ts",
                    models.DateTimeField(default=django.utils.timezone.now, db_index=True),
                ),
                ("actor", models.CharField(max_length=128, db_index=True)),
                ("action", models.CharField(max_length=64, blank=True, default="", db_index=True)),
                ("entity_uid", models.UUIDField(null=True, blank=True, db_index=True)),
                (
                    "detail_code",
                    models.CharField(max_length=100, null=True, blank=True, db_index=True),
                ),
                ("before", models.JSONField(null=True, blank=True)),
                ("after", models.JSONField(null=True, blank=True)),
            ],
            options={
                "db_table": "audit_log",
                "ordering": ["-change_ts"],
                "verbose_name": "Audit log entry",
                "verbose_name_plural": "Audit log entries",
            },
        ),
    ]
