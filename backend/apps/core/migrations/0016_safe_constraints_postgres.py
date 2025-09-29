from django.db import migrations

FORWARD_SQL = r"""
CREATE EXTENSION IF NOT EXISTS btree_gist;

DO $$
BEGIN
    -- ========= ENTITY =========
    IF to_regclass('public.entity') IS NOT NULL THEN
        -- Unique current row per entity_uid
        CREATE UNIQUE INDEX IF NOT EXISTS entity_current_unique_idx
        ON public.entity (entity_uid) WHERE is_current;

        -- Exclude overlapping validity intervals (right-open [))
        BEGIN
            ALTER TABLE public.entity
            ADD CONSTRAINT entity_validity_no_overlap
            EXCLUDE USING gist (
                entity_uid WITH =,
                tstzrange(valid_from, COALESCE(valid_to, 'infinity'::timestamptz), '[)') WITH &&
            )
            WHERE (is_current OR valid_to IS NOT NULL)
            DEFERRABLE INITIALLY IMMEDIATE;
        EXCEPTION WHEN duplicate_object THEN
            NULL;
        END;
    END IF;

    -- ======== ENTITY_DETAIL ========
    IF to_regclass('public.entity_detail') IS NOT NULL THEN
        -- Unique current row per (entity_uid, detail_code)
        CREATE UNIQUE INDEX IF NOT EXISTS entity_detail_current_unique_idx
        ON public.entity_detail (entity_uid, detail_code) WHERE is_current;

        -- Exclude overlapping validity intervals for (entity_uid, detail_code) (right-open [))
        BEGIN
            ALTER TABLE public.entity_detail
            ADD CONSTRAINT entity_detail_validity_no_overlap
            EXCLUDE USING gist (
                entity_uid WITH =,
                detail_code WITH =,
                tstzrange(valid_from, COALESCE(valid_to, 'infinity'::timestamptz), '[)') WITH &&
            )
            WHERE (is_current OR valid_to IS NOT NULL)
            DEFERRABLE INITIALLY IMMEDIATE;
        EXCEPTION WHEN duplicate_object THEN
            NULL;
        END;
    END IF;
END
$$;
"""

REVERSE_SQL = r"""
DO $$
BEGIN
    IF to_regclass('public.entity') IS NOT NULL THEN
        ALTER TABLE public.entity
        DROP CONSTRAINT IF EXISTS entity_validity_no_overlap;
        DROP INDEX IF EXISTS entity_current_unique_idx;
    END IF;

    IF to_regclass('public.entity_detail') IS NOT NULL THEN
        ALTER TABLE public.entity_detail
        DROP CONSTRAINT IF EXISTS entity_detail_validity_no_overlap;
        DROP INDEX IF EXISTS entity_detail_current_unique_idx;
    END IF;
END
$$;
"""


def forwards(apps, schema_editor):
    """Apply safe SCD2 constraints only if tables already exist and DB is PostgreSQL."""
    if schema_editor.connection.vendor != "postgresql":
        return
    schema_editor.execute(FORWARD_SQL)


def backwards(apps, schema_editor):
    """Drop SCD2 constraints and indexes if they exist."""
    if schema_editor.connection.vendor != "postgresql":
        return
    schema_editor.execute(REVERSE_SQL)


class Migration(migrations.Migration):
    """
    Adds safe partial unique indexes and exclusion constraints for
    Entity and EntityDetail tables.

    - entity_current_unique_idx
    - entity_detail_current_unique_idx
    - entity_validity_no_overlap
    - entity_detail_validity_no_overlap

    Executed only on PostgreSQL.
    """

    dependencies = [
        ("core", "0015_sync_state_after_drops"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
