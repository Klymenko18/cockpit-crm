from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable

from django.core.management.base import BaseCommand, CommandParser
from django.utils.dateparse import parse_datetime

from apps.core.services.scd2 import update_entity_detail


class Command(BaseCommand):
    """Ingest entity details (SCD2) from CSV or NDJSON.

    CSV columns:
      entity_uid, detail_code, value_json, change_ts (optional)
    - value_json must be a JSON string, e.g. {"email":"a@b.com"} or "UK" etc.
    """

    help = __doc__

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--file", required=True)
        parser.add_argument("--format", choices=["csv", "ndjson"], required=True)
        parser.add_argument("--actor", default="batch")

    def handle(self, *args, **opts):
        path = Path(opts["file"])
        ftype = opts["format"]
        actor = opts["actor"]

        rows = self._iter_csv(path) if ftype == "csv" else self._iter_ndjson(path)

        total = created = updated = noop = 0
        for row in rows:
            value = row["value_json"]
            try:
                value_obj = json.loads(value) if isinstance(value, str) else value
            except Exception as e:
                raise SystemExit(f"Bad value_json: {value!r} ({e})")

            res = update_entity_detail(
                entity_uid=row["entity_uid"],
                detail_code=row["detail_code"],
                value_json=value_obj,
                change_ts=parse_datetime(row.get("change_ts") or ""),
                actor=actor,
            )
            total += 1
            created += res.status == "created"
            updated += res.status == "updated"
            noop += res.status == "noop"

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
