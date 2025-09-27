from __future__ import annotations

from django.db import models
from django.utils import timezone


class AuditLog(models.Model):
    """
    Minimal audit trail record used by SCD2 services.

    Fields:
        change_ts: When the change happened (application-time).
        actor: Who initiated the change (e.g., username, "api").
        action: Short code describing the change (e.g., "OPEN_ENTITY").
        entity_uid: Logical entity UUID if applicable.
        detail_code: Detail key if applicable.
        before: Optional JSON snapshot before the change.
        after: Optional JSON snapshot after the change.
    """
    id = models.BigAutoField(primary_key=True)

    change_ts = models.DateTimeField(default=timezone.now, db_index=True)
    actor = models.CharField(max_length=128, db_index=True)
    # Keep blank/default so adding this field to an existing table won't prompt for a default.
    action = models.CharField(max_length=64, db_index=True, blank=True, default="")

    entity_uid = models.UUIDField(null=True, blank=True, db_index=True)
    detail_code = models.CharField(max_length=100, null=True, blank=True, db_index=True)

    before = models.JSONField(null=True, blank=True)
    after = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = "audit_log"
        ordering = ["-change_ts"]
        verbose_name = "Audit log entry"
        verbose_name_plural = "Audit log entries"

    def __str__(self) -> str:
        return f"{self.change_ts} {self.actor} {self.action}"
