from django.db import models


class AuditLog(models.Model):
    """
    Minimal audit log for SCD2 operations.

    Fields:
        change_ts: When the change occurred (application-time).
        actor: Who initiated the change (username, "api", etc.).
        action: Short action code (OPEN_ENTITY, CLOSE_ENTITY, OPEN_DETAIL, CLOSE_DETAIL).
        entity_uid: Stable UUID of the logical entity.
        detail_code: Key of the detail if the change was on entity details.
        before: Previous state as JSON.
        after: New state as JSON.
    """

    change_ts = models.DateTimeField()
    actor = models.CharField(max_length=200)
    action = models.CharField(max_length=50)
    entity_uid = models.UUIDField()
    detail_code = models.CharField(max_length=100, null=True, blank=True)
    before = models.JSONField(null=True, blank=True)
    after = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = "audit_log"

    def __str__(self) -> str:
        base = f"{self.action}::{self.entity_uid}"
        return f"{base}::{self.detail_code}" if self.detail_code else base
