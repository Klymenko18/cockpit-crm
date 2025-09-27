from django.urls import path
from apps.core.views import (
    EntitiesListCreate, EntityRetrievePatch, EntityHistory,
    EntitiesAsOf, DiffView,
    EntityDetailListCreate, EntityDetailRetrievePatchDelete,
)

app_name = "core"

urlpatterns = [
    # /api/v1/entities  (GET list, POST create)
    path("entities", EntitiesListCreate.as_view(), name="entities_list_create"),

    # /api/v1/entities/{entity_uid}  (GET snapshot, PATCH SCD2 update, DELETE close current — якщо у тебе є)
    path("entities/<uuid:entity_uid>", EntityRetrievePatch.as_view(), name="entity_retrieve_patch"),

    # /api/v1/entities/{entity_uid}/history  (GET combined history)
    path("entities/<uuid:entity_uid>/history", EntityHistory.as_view(), name="entities_history"),

    # /api/v1/entities/{entity_uid}/details  (GET/POST current details list or upsert)
    path("entities/<uuid:entity_uid>/details", EntityDetailListCreate.as_view(), name="entity_detail_list_create"),

    # /api/v1/entities/{entity_uid}/details/{detail_code}  (GET current by code, PATCH SCD2, DELETE close current)
    path("entities/<uuid:entity_uid>/details/<str:detail_code>", EntityDetailRetrievePatchDelete.as_view(), name="entity_detail_rpd"),

    # /api/v1/entities-asof?as_of=YYYY-MM-DD
    path("entities-asof", EntitiesAsOf.as_view(), name="entities_asof"),

    # /api/v1/diff?from=YYYY-MM-DD&to=YYYY-MM-DD
    path("diff", DiffView.as_view(), name="diff"),
]
