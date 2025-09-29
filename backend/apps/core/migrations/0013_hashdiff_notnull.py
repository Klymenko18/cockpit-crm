from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0012_noop_sync"),
    ]

    operations = [
        migrations.RunSQL(
            """
            CREATE EXTENSION IF NOT EXISTS pgcrypto;
            UPDATE public.entity e
            SET hashdiff = digest( (to_jsonb(e) - 'hashdiff')::text, 'sha256')
            WHERE hashdiff IS NULL;
            UPDATE public.entity_detail d
            SET hashdiff = digest( (to_jsonb(d) - 'hashdiff')::text, 'sha256')
            WHERE hashdiff IS NULL;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.AlterField(
            model_name="entity",
            name="hashdiff",
            field=models.BinaryField(null=False),
        ),
        migrations.AlterField(
            model_name="entitydetail",
            name="hashdiff",
            field=models.BinaryField(null=False),
        ),
    ]
