# Generated manually for adding SCD2 constraints & indexes on Entity
from django.db import migrations, models
from django.db.models import F, Q, Func, Value
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.fields import RangeOperators


def make_tstzrange(lower, upper):
    # Helper for readability (not used directly in migration operations)
    return Func(lower, Func(upper, Value("infinity"), function="COALESCE"), function="TSTZRANGE")


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0010_merge_20250925_1217"),
    ]

    operations = [
        # Partial unique "current row" per entity_uid
        migrations.AddConstraint(
            model_name="entity",
            constraint=models.UniqueConstraint(
                fields=["entity_uid"],
                condition=Q(is_current=True),
                name="entity_current_uniq",
            ),
        ),
        # No overlap constraint on validity windows for the same entity_uid
        migrations.AddConstraint(
            model_name="entity",
            constraint=ExclusionConstraint(
                name="entity_no_overlap",
                index_type="GIST",
                expressions=[
                    (F("entity_uid"), "="),
                    (
                        Func(
                            F("valid_from"),
                            Func(F("valid_to"), Value("infinity"), function="COALESCE"),
                            function="TSTZRANGE",
                        ),
                        RangeOperators.OVERLAPS,
                    ),
                ],
            ),
        ),
        # Helpful covering indexes for common filters
        migrations.AddIndex(
            model_name="entity",
            index=models.Index(
                fields=["entity_uid", "is_current"],
                name="entity_uid_current_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="entitydetail",
            index=models.Index(
                fields=["entity_uid", "detail_code", "is_current"],
                name="entitydetail_uid_code_current_idx",
            ),
        ),
    ]
