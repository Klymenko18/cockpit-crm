migrations.RunSQL(
    sql="""
    CREATE UNIQUE INDEX IF NOT EXISTS entity_uid_current_uniq
    ON entity (entity_uid)
    WHERE is_current = true;
    """,
    reverse_sql="DROP INDEX IF EXISTS entity_uid_current_uniq;",
),
migrations.RunSQL(
    sql="""
    ALTER TABLE entity
    ADD CONSTRAINT entity_no_overlap
    EXCLUDE USING gist (
      entity_uid WITH =,
      tstzrange(valid_from, COALESCE(valid_to, 'infinity')) WITH &&
    );
    """,
    reverse_sql="ALTER TABLE entity DROP CONSTRAINT IF EXISTS entity_no_overlap;",
),
migrations.RunSQL(
    sql="""
    CREATE UNIQUE INDEX IF NOT EXISTS entity_detail_current_uniq
    ON entity_detail (entity_uid, detail_code)
    WHERE is_current = true;
    """,
    reverse_sql="DROP INDEX IF EXISTS entity_detail_current_uniq;",
),
migrations.RunSQL(
    sql="""
    ALTER TABLE entity_detail
    ADD CONSTRAINT entity_detail_no_overlap
    EXCLUDE USING gist (
      entity_uid WITH =,
      detail_code WITH =,
      tstzrange(valid_from, COALESCE(valid_to, 'infinity')) WITH &&
    );
    """,
    reverse_sql="ALTER TABLE entity_detail DROP CONSTRAINT IF EXISTS entity_detail_no_overlap;",
),
migrations.RunSQL(
    sql="""
    CREATE INDEX IF NOT EXISTS entity_detail_value_json_gin
    ON entity_detail
    USING gin (value_json jsonb_path_ops);
    """,
    reverse_sql="DROP INDEX IF EXISTS entity_detail_value_json_gin;",
),
