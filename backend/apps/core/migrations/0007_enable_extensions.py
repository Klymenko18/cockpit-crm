from django.db import migrations

SQL_ENABLE_EXTENSIONS = """
CREATE EXTENSION IF NOT EXISTS btree_gist;
-- Опційно для пошуку по тексту:
-- CREATE EXTENSION IF NOT EXISTS pg_trgm;
"""

SQL_DISABLE_EXTENSIONS = """
-- Якщо треба відкочувати, можна дропнути (не обов'язково):
-- DROP EXTENSION IF EXISTS pg_trgm;
-- DROP EXTENSION IF EXISTS btree_gist;
"""


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0006_state_entitytype_is_active"),
    ]

    operations = [
        migrations.RunSQL(
            sql=SQL_ENABLE_EXTENSIONS,
            reverse_sql=SQL_DISABLE_EXTENSIONS,
        ),
    ]
