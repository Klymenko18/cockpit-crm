from django.db import migrations, models
import uuid

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_hashdiff_notnull'),
    ]

    operations = [
        # 1) Дропи — через IF EXISTS, щоб міграція не падала, якщо вже дропнуто
        migrations.RunSQL(
            "ALTER TABLE public.entity DROP CONSTRAINT IF EXISTS entity_current_uniq;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            "ALTER TABLE public.entity DROP CONSTRAINT IF EXISTS entity_no_overlap;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            "DROP INDEX IF EXISTS entity_uid_current_idx;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            "DROP INDEX IF EXISTS entitydetail_uid_code_current_idx;",
            reverse_sql=migrations.RunSQL.noop,
        ),

        # 2) Конвертація hashdiff: bytea -> varchar(64) (hex)
        migrations.RunSQL(
            """
            -- entity
            ALTER TABLE public.entity
            ALTER COLUMN hashdiff TYPE varchar(64)
            USING encode(hashdiff, 'hex');
            ALTER TABLE public.entity
            ALTER COLUMN hashdiff SET NOT NULL;

            -- entity_detail
            ALTER TABLE public.entity_detail
            ALTER COLUMN hashdiff TYPE varchar(64)
            USING encode(hashdiff, 'hex');
            ALTER TABLE public.entity_detail
            ALTER COLUMN hashdiff SET NOT NULL;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),

        # 3) Залишаємо AlterField, щоб Django зафіксував цільовий стан моделей
        migrations.AlterField(
            model_name='entity',
            name='entity_uid',
            field=models.UUIDField(default=uuid.uuid4, editable=False),
        ),
        migrations.AlterField(
            model_name='entity',
            name='hashdiff',
            field=models.CharField(max_length=64),
        ),
        migrations.AlterField(
            model_name='entitydetail',
            name='entity_uid',
            field=models.UUIDField(),
        ),
        migrations.AlterField(
            model_name='entitydetail',
            name='hashdiff',
            field=models.CharField(max_length=64),
        ),
        migrations.AlterField(
            model_name='entitytype',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
