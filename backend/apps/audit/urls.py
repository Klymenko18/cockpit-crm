from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AuditLogViewSet

router = DefaultRouter(trailing_slash=False)
router.register("logs", AuditLogViewSet, basename="audit-logs")

urlpatterns = [
    path("", include(router.urls)),
]
