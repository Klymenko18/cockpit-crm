from django.core.management.base import BaseCommand

from apps.crm.models import EntityType


class Command(BaseCommand):
    help = "seed entity types"

    def handle(self, *args, **kwargs):
        EntityType.objects.get_or_create(
            code="PERSON", defaults={"name": "Person", "is_active": True}
        )
        EntityType.objects.get_or_create(
            code="INSTITUTION", defaults={"name": "Institution", "is_active": True}
        )
        self.stdout.write("ok")
