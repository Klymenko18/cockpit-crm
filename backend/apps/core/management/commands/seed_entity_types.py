from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.core.models import EntityType


class Command(BaseCommand):
    """
    Seed default EntityType rows.

    Usage:
        python manage.py seed_entity_types
    """

    help = "Seed default entity types (idempotent)."

    DEFAULT_TYPES = [
        ("PERSON", "Natural person"),
        ("INSTITUTION", "Legal entity / institution"),
    ]

    def handle(self, *args, **options):
        created = 0
        for code, name in self.DEFAULT_TYPES:
            obj, was_created = EntityType.objects.get_or_create(code=code, defaults={"name": name})
            created += 1 if was_created else 0
        self.stdout.write(self.style.SUCCESS(f"Seeded EntityType. Newly created: {created}"))
