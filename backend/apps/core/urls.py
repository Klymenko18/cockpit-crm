from django.urls import path

from apps.core.views import (
    DiffView,
    EntitiesAsOf,
    EntitiesListCreate,
    EntityDetailListCreate,
    EntityDetailRetrievePatchDelete,
    EntityHistory,
    EntityRetrievePatch,
)

app_name = "core"

urlpatterns = [
    path("entities", EntitiesListCreate.as_view(), name="entities_list_create"),
    path("entities/<uuid:entity_uid>", EntityRetrievePatch.as_view(), name="entity_retrieve_patch"),
    path("entities/<uuid:entity_uid>/history", EntityHistory.as_view(), name="entities_history"),
    path(
        "entities/<uuid:entity_uid>/details",
        EntityDetailListCreate.as_view(),
        name="entity_detail_list_create",
    ),
    path(
        "entities/<uuid:entity_uid>/details/<str:detail_code>",
        EntityDetailRetrievePatchDelete.as_view(),
        name="entity_detail_rpd",
    ),
    path("entities-asof", EntitiesAsOf.as_view(), name="entities_asof"),
    path("diff", DiffView.as_view(), name="diff"),
]
