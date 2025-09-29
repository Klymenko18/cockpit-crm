from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from django.core.management.base import BaseCommand, CommandParser
from django.utils.dateparse import parse_datetime

from apps.core.services.scd2 import update_entity


class Command(BaseCommand):
    """Ingest entities (SCD2) from CSV or NDJSON.

    CSV columns:
      entity_uid, display_name, entity_type, change_ts (optional ISO-8601)
    NDJSON keys are the same per line.

    Usage:
      manage.py ingest_entities --file data.csv --format csv
      manage.py ingest_entities --file data.ndjson --format ndjson --actor batch
    """

    help = __doc__

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--file", required=True, help="Path to CSV or NDJSON file.")
        parser.add_argument("--format", choices=["csv", "ndjson"], required=True)
        parser.add_argument("--actor", default="batch", help="Audit actor label.")

    def handle(self, *args, **opts):
        path = Path(opts["file"])
        ftype = opts["format"]
        actor = opts["actor"]

        if ftype == "csv":
            rows = self._iter_csv(path)
        else:
            rows = self._iter_ndjson(path)

        total = created = updated = noop = 0
        for row in rows:
            total += 1
            change_ts = parse_datetime(row.get("change_ts") or "")  
            res = update_entity(
                entity_uid=row["entity_uid"],
                display_name=row["display_name"],
                entity_type=row["entity_type"],
                change_ts=change_ts,
                actor=actor,
            )
            if res.status == "created":
                created += 1
            elif res.status == "updated":
                updated += 1
            else:
                noop += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Ingest complete: total={total} created={created} updated={updated} noop={noop}"
            )
        )

    def _iter_csv(self, path: Path) -> Iterable[Dict[str, Any]]:
        with path.open("r", newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                yield row

    def _iter_ndjson(self, path: Path) -> Iterable[Dict[str, Any]]:
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    yield json.loads(line)
