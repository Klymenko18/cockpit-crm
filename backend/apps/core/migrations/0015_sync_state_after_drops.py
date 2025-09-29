from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0014_remove_entity_entity_current_uniq_and_more"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
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
            ],
            state_operations=[
                migrations.RemoveConstraint(
                    model_name="entity",
                    name="entity_current_uniq",
                ),
                migrations.RemoveConstraint(
                    model_name="entity",
                    name="entity_no_overlap",
                ),
                migrations.RemoveIndex(
                    model_name="entity",
                    name="entity_uid_current_idx",
                ),
                migrations.RemoveIndex(
                    model_name="entitydetail",
                    name="entitydetail_uid_code_current_idx",
                ),
            ],
        ),
    ]
