"""Management command: batch ingest Entities with idempotent SCD2 semantics.

Supports NDJSON (default) and CSV.
"""

import csv
import json
from pathlib import Path
from typing import Any, Dict

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.core.services.scd2 import scd2_upsert_entity


class Command(BaseCommand):
    help = "Batch ingest of Entities (SCD2 idempotent). Supports NDJSON (default) and CSV."

    def add_arguments(self, parser):
        parser.add_argument("--file", required=True, help="Path to NDJSON/CSV file")
        parser.add_argument("--format", choices=["ndjson", "csv"], default="ndjson")
        parser.add_argument(
            "--ts-field", default=None, help="Optional ISO8601 field used as change_ts"
        )
        parser.add_argument("--uid-field", default="entity_uid", help="Field name for entity_uid")
        parser.add_argument(
            "--display-name-field", default="display_name", help="Field containing display name"
        )
        parser.add_argument(
            "--entity-type-id-field", default="entity_type_id", help="Field for entity_type_id"
        )

    def handle(self, *args, **opts):
        """Ingest rows and perform SCD2 upserts."""
        path = Path(opts["file"])
        if not path.exists():
            raise CommandError(f"File not found: {path}")

        fmt = opts["format"]
        ts_field = opts["ts_field"]
        uid_field = opts["uid_field"]
        dn_field = opts["display_name_field"]
        et_field = opts["entity_type_id_field"]

        created = closed = noop = 0

        def _ingest_one(row: Dict[str, Any]):
            nonlocal created, closed, noop
            uid = row[uid_field]
            business = {
                "display_name": row.get(dn_field, ""),
                "entity_type_id": row.get(et_field),
            }
            ts = timezone.now()
            if ts_field and row.get(ts_field):
                ts = timezone.make_aware(timezone.datetime.fromisoformat(row[ts_field]))
            res = scd2_upsert_entity(entity_uid=uid, change_ts=ts, business=business)
            if res.created:
                created += 1
                if res.closed_prev:
                    closed += 1
            else:
                noop += 1

        if fmt == "ndjson":
            with path.open("r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    _ingest_one(json.loads(line))
        else:
            with path.open("r", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    _ingest_one(row)

        self.stdout.write(
            self.style.SUCCESS(f"Done. created={created}, closed_prev={closed}, noop={noop}")
        )
