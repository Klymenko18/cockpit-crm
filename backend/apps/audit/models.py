from django.db import models

class AuditLog(models.Model):
    id = models.BigAutoField(primary_key=True)
    change_ts = models.DateTimeField()
    actor = models.CharField(max_length=255)
    entity_uid = models.UUIDField()
    detail_code = models.CharField(max_length=100, null=True, blank=True)
    operation = models.CharField(max_length=32)
    before = models.JSONField(null=True, blank=True)
    after = models.JSONField(null=True, blank=True)
    request_id = models.CharField(max_length=100, null=True, blank=True)
    trace_id = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "audit_log"
        indexes = [
            models.Index(fields=["entity_uid", "change_ts"], name="audit_entity_ts_idx"),
        ]
