from django.db import migrations

LOCK_IN_SQL = r"""
CREATE EXTENSION IF NOT EXISTS btree_gist;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE INDEX IF NOT EXISTS entity_entity__d227b0_idx ON public.entity (entity_uid, valid_from);
CREATE INDEX IF NOT EXISTS entity_entity__df9f7a_idx ON public.entity (entity_type_id, is_current);
CREATE INDEX IF NOT EXISTS entity_display_name_trgm ON public.entity USING gin (display_name gin_trgm_ops);

CREATE INDEX IF NOT EXISTS entity_deta_entity__b35e2e_idx ON public.entity_detail (entity_uid, detail_code, valid_from);
CREATE INDEX IF NOT EXISTS entity_detail_value_json_gin ON public.entity_detail USING gin (value_json jsonb_path_ops);

CREATE UNIQUE INDEX IF NOT EXISTS entity_uid_current_uniq
    ON public.entity (entity_uid) WHERE is_current IS TRUE;

CREATE UNIQUE INDEX IF NOT EXISTS entity_detail_current_uniq
    ON public.entity_detail (entity_uid, detail_code) WHERE is_current IS TRUE;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'entity_no_overlap'
    ) THEN
        ALTER TABLE public.entity
        ADD CONSTRAINT entity_no_overlap
        EXCLUDE USING gist (
            entity_uid WITH =,
            tstzrange(valid_from, COALESCE(valid_to, 'infinity'::timestamptz)) WITH &&
        );
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'entity_detail_no_overlap'
    ) THEN
        ALTER TABLE public.entity_detail
        ADD CONSTRAINT entity_detail_no_overlap
        EXCLUDE USING gist (
            entity_uid WITH =,
            detail_code WITH =,
            tstzrange(valid_from, COALESCE(valid_to, 'infinity'::timestamptz)) WITH &&
        );
    END IF;
END $$;
"""


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(LOCK_IN_SQL, reverse_sql=""),
    ]
