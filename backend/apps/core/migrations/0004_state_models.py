import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_add_timestamps"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name="EntityType",
                    fields=[
                        ("id", models.BigAutoField(primary_key=True, serialize=False)),
                        ("name", models.CharField(max_length=100, unique=True)),
                        ("code", models.CharField(max_length=50, unique=True)),
                    ],
                    options={"db_table": "entity_type"},
                ),
                migrations.CreateModel(
                    name="Entity",
                    fields=[
                        ("id", models.BigAutoField(primary_key=True, serialize=False)),
                        (
                            "entity_uid",
                            models.UUIDField(default=uuid.uuid4, editable=False, db_index=True),
                        ),
                        ("display_name", models.CharField(max_length=500)),
                        ("valid_from", models.DateTimeField()),
                        ("valid_to", models.DateTimeField(blank=True, null=True)),
                        ("is_current", models.BooleanField(default=True)),
                        ("hashdiff", models.BinaryField()),
                        ("created_at", models.DateTimeField(auto_now_add=True)),
                        ("updated_at", models.DateTimeField(auto_now=True)),
                        (
                            "entity_type",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.PROTECT, to="core.entitytype"
                            ),
                        ),
                    ],
                    options={
                        "db_table": "entity",
                        "indexes": [
                            models.Index(
                                fields=["entity_uid", "valid_from"],
                                name="entity_entity__d227b0_idx",
                            ),
                            models.Index(
                                fields=["entity_type", "is_current"],
                                name="entity_entity__df9f7a_idx",
                            ),
                        ],
                    },
                ),
                migrations.CreateModel(
                    name="EntityDetail",
                    fields=[
                        ("id", models.BigAutoField(primary_key=True, serialize=False)),
                        ("entity_uid", models.UUIDField(db_index=True)),
                        ("detail_code", models.CharField(max_length=100)),
                        ("value_json", models.JSONField()),
                        ("valid_from", models.DateTimeField()),
                        ("valid_to", models.DateTimeField(blank=True, null=True)),
                        ("is_current", models.BooleanField(default=True)),
                        ("hashdiff", models.BinaryField()),
                        ("created_at", models.DateTimeField(auto_now_add=True)),
                        ("updated_at", models.DateTimeField(auto_now=True)),
                    ],
                    options={
                        "db_table": "entity_detail",
                        "indexes": [
                            models.Index(
                                fields=["entity_uid", "detail_code", "valid_from"],
                                name="entity_deta_entity__b35e2e_idx",
                            ),
                        ],
                    },
                ),
            ],
        )
    ]
