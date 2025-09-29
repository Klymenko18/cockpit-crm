from django.db import migrations

SQL = r"""
ALTER TABLE public.entity
    ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now(),
    ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();

ALTER TABLE public.entity_detail
    ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now(),
    ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();
"""


class Migration(migrations.Migration):
    dependencies = [("core", "0002_schema_lock_in")]
    operations = [migrations.RunSQL(SQL, reverse_sql="")]
