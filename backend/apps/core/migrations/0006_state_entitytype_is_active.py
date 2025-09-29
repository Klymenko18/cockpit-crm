from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("core", "0005_alter_entitytype_id")]
    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AddField(
                    model_name="entitytype",
                    name="is_active",
                    field=models.BooleanField(default=True),
                ),
            ],
        )
    ]
