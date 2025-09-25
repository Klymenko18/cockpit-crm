import csv
import json
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from apps.core.models import EntityType
from apps.core.services.scd2 import update_entity, update_entity_detail

class Command(BaseCommand):
    help = "Ingest entities and details from JSONL or CSV"

    def add_arguments(self, parser):
        parser.add_argument("path", type=str)
        parser.add_argument("--actor", type=str, default="ingest")
        parser.add_argument("--format", type=str, choices=["jsonl", "csv"], default=None)

    def handle(self, *args, **opts):
        path = Path(opts["path"])
        if not path.exists():
            raise CommandError("file not found")
        fmt = opts["format"] or ("jsonl" if path.suffix.lower() in [".jsonl", ".ndjson"] else "csv")
        actor = opts["actor"]
        n = 0
        if fmt == "jsonl":
            with path.open("r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    obj = json.loads(line)
                    self._process_obj(obj, actor)
                    n += 1
        else:
            with path.open("r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    obj = {k: (json.loads(v) if k == "value_json" and v else v) for k, v in row.items()}
                    self._process_obj(obj, actor)
                    n += 1
        self.stdout.write(self.style.SUCCESS(f"ingested: {n}"))

    def _process_obj(self, obj, actor):
        kind = obj.get("kind") or obj.get("type")
        if kind == "entity":
            et_code = obj["entity_type"]
            et = EntityType.objects.get(code=et_code)
            update_entity(
                change_ts=timezone.now(),
                actor=actor,
                payload={
                    "entity_uid": obj["entity_uid"],
                    "display_name": obj["display_name"],
                    "entity_type_id": et.id,
                },
            )
        elif kind == "detail":
            update_entity_detail(
                change_ts=timezone.now(),
                actor=actor,
                payload={
                    "entity_uid": obj["entity_uid"],
                    "detail_code": obj["detail_code"],
                    "value_json": obj["value_json"],
                },
            )
        else:
            raise CommandError("row kind must be 'entity' or 'detail'")
