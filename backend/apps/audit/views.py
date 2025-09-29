from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, viewsets

from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only browse & filter access to audit trail.

    Secured as admin-only by default.
    """

    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        "entity_uid": ["exact"],
        "detail_code": ["exact"],
        "change_ts": ["gte", "lte"],
    }
    search_fields = ["actor", "action", "detail_code"]
    ordering_fields = ["change_ts", "id"]
    ordering = ["-change_ts", "-id"]
