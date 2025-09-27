from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from apps.common.health import live_view, ready_view

urlpatterns = [
    path("admin/", admin.site.urls),

    # API v1
    path("api/v1/audit/", include("apps.audit.urls")),
    path("api/v1/accounts/", include("apps.accounts.urls")),
    path("api/v1/", include("apps.core.urls")),

    # Auth (JWT)
    path("api/v1/auth/token", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/v1/auth/refresh", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/v1/auth/verify", TokenVerifyView.as_view(), name="token_verify"),

    # OpenAPI / Swagger / Redoc
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/schema/swagger-ui/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/schema/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),

    # Healthchecks
    path("health/live", live_view, name="health-live"),
    path("health/ready", ready_view, name="health-ready"),
]
