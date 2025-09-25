"""Add SCD2 invariants for Entity:
- partial UNIQUE index guaranteeing a single current row per entity_uid
- GiST exclusion constraint preventing overlapping validity windows
- ensure btree_gist extension exists
"""

from django.db import migrations

SQL_ENABLE_BTREE_GIST = "CREATE EXTENSION IF NOT EXISTS btree_gist;"

SQL_ENTITY_UNIQ_CURRENT = """
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE c.relname = 'entity_current_uniq'
      AND n.nspname = current_schema()
  ) THEN
    CREATE UNIQUE INDEX entity_current_uniq
      ON public.entity(entity_uid)
      WHERE is_current IS TRUE;
  END IF;
END $$;
"""

SQL_ENTITY_NO_OVERLAP = """
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'entity_no_overlap'
  ) THEN
    ALTER TABLE public.entity
      ADD CONSTRAINT entity_no_overlap
      EXCLUDE USING gist (
        entity_uid WITH =,
        tstzrange(valid_from, COALESCE(valid_to, 'infinity')) WITH &&
      );
  END IF;
END $$;
"""

class Migration(migrations.Migration):
    """
    Migration wiring. If your previous migration name differs,
    update the dependency below accordingly.
    """
    dependencies = [
        ("core", "0010_merge_20250925_1217"),
    ]
    operations = [
        migrations.RunSQL(SQL_ENABLE_BTREE_GIST),
        migrations.RunSQL(
            SQL_ENTITY_UNIQ_CURRENT,
            reverse_sql="DROP INDEX IF EXISTS public.entity_current_uniq;"
        ),
        migrations.RunSQL(
            SQL_ENTITY_NO_OVERLAP,
            reverse_sql="ALTER TABLE public.entity DROP CONSTRAINT IF EXISTS entity_no_overlap;"
        ),
    ]
