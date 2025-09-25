from django.db import migrations, models

class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="AuditLog",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("change_ts", models.DateTimeField()),
                ("actor", models.CharField(max_length=255)),
                ("entity_uid", models.UUIDField()),
                ("detail_code", models.CharField(blank=True, max_length=100, null=True)),
                ("operation", models.CharField(max_length=32)),
                ("before", models.JSONField(blank=True, null=True)),
                ("after", models.JSONField(blank=True, null=True)),
                ("request_id", models.CharField(blank=True, max_length=100, null=True)),
                ("trace_id", models.CharField(blank=True, max_length=100, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "audit_log"},
        ),
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(fields=["entity_uid", "change_ts"], name="audit_entity_ts_idx"),
        ),
    ]
