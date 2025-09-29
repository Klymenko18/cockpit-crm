from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("audit", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name="auditlog",
                    name="created_at",
                    field=models.DateTimeField(auto_now_add=True),
                ),
                migrations.AddField(
                    model_name="auditlog",
                    name="updated_at",
                    field=models.DateTimeField(auto_now=True),
                ),
            ],
            database_operations=[],  
        ),
    ]
