from django.db.models import F, Q
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiTypes,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.models import Entity, EntityDetail, EntityType
from apps.core.serializers import (
    EntityDetailUpsertSerializer,
    EntitySnapshotSerializer,
    EntityUpsertSerializer,
)
from apps.core.services.scd2 import (
    close_entity,
    close_entity_detail,
    update_entity,
    update_entity_detail,
)


@extend_schema_view(
    get=extend_schema(
        tags=["entities"],
        summary="List current entities",
        parameters=[
            OpenApiParameter("q", OpenApiTypes.STR, OpenApiParameter.QUERY),
            OpenApiParameter("type", OpenApiTypes.STR, OpenApiParameter.QUERY),
            OpenApiParameter("detail_code", OpenApiTypes.STR, OpenApiParameter.QUERY),
            OpenApiParameter("detail_value", OpenApiTypes.STR, OpenApiParameter.QUERY),
        ],
        responses={200: EntitySnapshotSerializer(many=True)},
    ),
    post=extend_schema(
        tags=["entities"],
        summary="Create entity (SCD2 open)",
        request=EntityUpsertSerializer,
        responses={201: OpenApiTypes.OBJECT},
    ),
)
class EntitiesListCreate(APIView):
    """Collection endpoint for entities.

    GET returns up to 200 current entities with optional filtering by name,
    type code, and presence/value of a specific detail.

    POST performs an SCD2 idempotent upsert for the entity and, optionally,
    for a list of details in the `details` array.
    """

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        queryset = Entity.objects.filter(is_current=True)
        q = request.query_params.get("q")
        if q:
            queryset = queryset.filter(display_name__icontains=q)

        type_code = request.query_params.get("type")
        if type_code:
            queryset = queryset.filter(entity_type__code=type_code)

        detail_code = request.query_params.get("detail_code")
        detail_value = request.query_params.get("detail_value")
        if detail_code:
            sub = EntityDetail.objects.filter(
                entity_uid=F("entity_uid"),
                detail_code=detail_code,
                is_current=True,
            ).values("entity_uid")
            if detail_value is not None:
                queryset = queryset.filter(
                    entity_uid__in=EntityDetail.objects.filter(
                        detail_code=detail_code, is_current=True, value_json=detail_value
                    ).values("entity_uid")
                )
            else:
                queryset = queryset.filter(entity_uid__in=sub)

        data = EntitySnapshotSerializer(queryset.order_by("display_name")[:200], many=True).data
        return Response(data)

    def post(self, request):
        """Create entity and optional details via SCD2 upsert semantics."""
        serializer = EntityUpsertSerializer(
            data=request.data,
            context={"actor": request.user if request.user.is_authenticated else "api"},
        )
        serializer.is_valid(raise_exception=True)
        entity_result = serializer.save()

        details = request.data.get("details")
        detail_results = []
        if isinstance(details, list):
            for d in details:
                detail_serializer = EntityDetailUpsertSerializer(
                    data={
                        "entity_uid": serializer.validated_data["entity_uid"],
                        "detail_code": d["detail_code"],
                        "value_json": d["value_json"],
                        "change_ts": d.get("change_ts"),
                    },
                    context={"actor": request.user if request.user.is_authenticated else "api"},
                )
                detail_serializer.is_valid(raise_exception=True)
                detail_results.append(detail_serializer.save())

        out = {"entity": entity_result}
        if detail_results:
            out["details"] = detail_results
        return Response(out, status=status.HTTP_201_CREATED)


@extend_schema_view(
    get=extend_schema(
        tags=["entities"],
        summary="Get current snapshot by entity_uid",
        responses={200: EntitySnapshotSerializer},
    ),
    patch=extend_schema(
        tags=["entities"],
        summary="Patch entity with SCD2 transition",
        request=EntityUpsertSerializer,
        responses={200: OpenApiTypes.OBJECT},
    ),
    delete=extend_schema(
        tags=["entities"],
        summary="Close current entity version (soft delete)",
        parameters=[OpenApiParameter("change_ts", OpenApiTypes.DATETIME, OpenApiParameter.QUERY)],
        responses={200: OpenApiTypes.OBJECT},
    ),
)
class EntityRetrievePatch(APIView):
    """Item endpoint for a single entity addressed by `entity_uid`."""

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, entity_uid):
        """Return the current entity snapshot or 404 if none exists."""
        obj = Entity.objects.filter(entity_uid=entity_uid, is_current=True).first()
        if not obj:
            return Response({"detail": "not found"}, status=404)
        return Response(EntitySnapshotSerializer(obj).data)

    def patch(self, request, entity_uid):
        """Apply SCD2 upsert to entity and optional details."""
        data = request.data.copy()
        data["entity_uid"] = str(entity_uid)

        if (
            "entity_type" in data
            and not EntityType.objects.filter(code=data["entity_type"]).exists()
        ):
            return Response({"detail": "invalid entity_type"}, status=400)

        result = {}
        entity_result = {}

        if set(data.keys()) & {"display_name", "entity_type", "change_ts"}:
            if "entity_type" in data:
                et = EntityType.objects.get(code=data["entity_type"])
            else:
                et = Entity.objects.get(entity_uid=entity_uid, is_current=True).entity_type

            serializer = EntityUpsertSerializer(
                data={
                    "entity_uid": entity_uid,
                    "display_name": data.get("display_name")
                    or Entity.objects.get(entity_uid=entity_uid, is_current=True).display_name,
                    "entity_type": et.code,
                    "change_ts": data.get("change_ts"),
                },
                context={"actor": request.user if request.user.is_authenticated else "api"},
            )
            serializer.is_valid(raise_exception=True)
            entity_result = serializer.save()

        details = data.get("details")
        detail_results = []
        if isinstance(details, list):
            for d in details:
                detail_serializer = EntityDetailUpsertSerializer(
                    data={
                        "entity_uid": entity_uid,
                        "detail_code": d["detail_code"],
                        "value_json": d["value_json"],
                        "change_ts": d.get("change_ts"),
                    },
                    context={"actor": request.user if request.user.is_authenticated else "api"},
                )
                detail_serializer.is_valid(raise_exception=True)
                detail_results.append(detail_serializer.save())

        result["entity"] = entity_result or {"status": "noop"}
        if detail_results:
            result["details"] = detail_results
        return Response(result)

    def delete(self, request, entity_uid):
        """Close the current entity version (SCD2 soft delete)."""
        ts_raw = request.query_params.get("change_ts")
        change_ts = parse_datetime(ts_raw) if ts_raw else timezone.now()
        status_s, _ = close_entity(
            change_ts=change_ts,
            actor=str(request.user if request.user.is_authenticated else "api"),
            entity_uid=entity_uid,
        )
        return Response({"status": status_s})


@extend_schema_view(
    get=extend_schema(
        tags=["details"],
        summary="List current details for entity",
        responses={200: OpenApiTypes.OBJECT},
    ),
    post=extend_schema(
        tags=["details"],
        summary="Create or upsert details (one or list)",
        request=EntityDetailUpsertSerializer(many=True),
        responses={201: EntityDetailUpsertSerializer(many=True)},
    ),
)
class EntityDetailListCreate(APIView):
    """Collection of details for a given entity."""

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, entity_uid):
        """Return a flat dict of current details `{code: value}` for the entity."""
        queryset = EntityDetail.objects.filter(entity_uid=entity_uid, is_current=True).values(
            "detail_code", "value_json"
        )
        return Response({r["detail_code"]: r["value_json"] for r in queryset})

    def post(self, request, entity_uid):
        """Create or upsert one or multiple details for the entity."""
        payloads = request.data if isinstance(request.data, list) else [request.data]
        out = []
        for d in payloads:
            detail_serializer = EntityDetailUpsertSerializer(
                data={
                    "entity_uid": entity_uid,
                    "detail_code": d["detail_code"],
                    "value_json": d["value_json"],
                    "change_ts": d.get("change_ts"),
                },
                context={"actor": request.user if request.user.is_authenticated else "api"},
            )
            detail_serializer.is_valid(raise_exception=True)
            out.append(detail_serializer.save())
        return Response(out, status=status.HTTP_201_CREATED)


@extend_schema_view(
    get=extend_schema(
        tags=["details"],
        summary="Get current detail by code",
        responses={200: OpenApiTypes.OBJECT},
    ),
    patch=extend_schema(
        tags=["details"],
        summary="Patch detail with SCD2 transition",
        request=EntityDetailUpsertSerializer,
        responses={200: OpenApiTypes.OBJECT},
    ),
    delete=extend_schema(
        tags=["details"],
        summary="Close current detail version (soft delete)",
        parameters=[OpenApiParameter("change_ts", OpenApiTypes.DATETIME, OpenApiParameter.QUERY)],
        responses={200: OpenApiTypes.OBJECT},
    ),
)
class EntityDetailRetrievePatchDelete(APIView):
    """Item endpoint for a single detail identified by `detail_code`."""

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, entity_uid, detail_code):
        """Return the current value of the detail or 404 if not present."""
        obj = EntityDetail.objects.filter(
            entity_uid=entity_uid, detail_code=detail_code, is_current=True
        ).first()
        if not obj:
            return Response({"detail": "not found"}, status=404)
        return Response({"detail_code": detail_code, "value_json": obj.value_json})

    def patch(self, request, entity_uid, detail_code):
        """Apply SCD2 upsert to a single detail."""
        detail_serializer = EntityDetailUpsertSerializer(
            data={
                "entity_uid": entity_uid,
                "detail_code": detail_code,
                "value_json": request.data["value_json"],
                "change_ts": request.data.get("change_ts"),
            },
            context={"actor": request.user if request.user.is_authenticated else "api"},
        )
        detail_serializer.is_valid(raise_exception=True)
        return Response(detail_serializer.save())

    def delete(self, request, entity_uid, detail_code):
        """Close the current detail version (SCD2 soft delete)."""
        ts_raw = request.query_params.get("change_ts")
        change_ts = parse_datetime(ts_raw) if ts_raw else timezone.now()
        status_s, _ = close_entity_detail(
            change_ts=change_ts,
            actor=str(request.user if request.user.is_authenticated else "api"),
            entity_uid=entity_uid,
            detail_code=detail_code,
        )
        return Response({"status": status_s})


@extend_schema(
    tags=["entities"],
    summary="Combined history for an entity",
    responses={200: OpenApiTypes.OBJECT},
)
class EntityHistory(APIView):
    """Return the full version history for an entity and its details."""

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, entity_uid):
        ent = list(Entity.objects.filter(entity_uid=entity_uid).order_by("valid_from").values())
        det = list(
            EntityDetail.objects.filter(entity_uid=entity_uid)
            .order_by("detail_code", "valid_from")
            .values()
        )
        if not ent and not det:
            return Response({"detail": "not found"}, status=404)
        return Response({"entity": ent, "details": det})


@extend_schema(
    tags=["asof"],
    summary="As-of snapshot for all entities",
    parameters=[
        OpenApiParameter("as_of", OpenApiTypes.DATETIME, OpenApiParameter.QUERY, required=True)
    ],
    responses={
        200: inline_serializer(
            name="AsOfEntitySnapshot",
            fields={
                "entity_uid": serializers.UUIDField(),
                "display_name": serializers.CharField(),
                "entity_type": serializers.CharField(),
                "valid_from": serializers.DateTimeField(),
                "valid_to": serializers.DateTimeField(allow_null=True),
                "details": serializers.DictField(child=serializers.JSONField()),
            },
            many=True,
        )
    },
)
class EntitiesAsOf(APIView):
    """Return the state of all entities at a given point in time."""

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        as_of_raw = request.query_params.get("as_of")
        if not as_of_raw:
            return Response({"detail": "as_of required"}, status=400)
        dt = parse_datetime(as_of_raw)
        if not dt:
            return Response({"detail": "invalid datetime"}, status=400)
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt)

        alive_qs = (
            Entity.objects.filter(valid_from__lte=dt)
            .filter(Q(valid_to__gt=dt) | Q(valid_to__isnull=True))
            .order_by("entity_uid", "-valid_from")
        )

        latest = {}
        for e in alive_qs:
            if e.entity_uid not in latest:
                latest[e.entity_uid] = e

        data = []
        for e in latest.values():
            details = (
                EntityDetail.objects.filter(entity_uid=e.entity_uid, valid_from__lte=dt)
                .filter(Q(valid_to__gt=dt) | Q(valid_to__isnull=True))
                .values("detail_code", "value_json")
            )
            data.append(
                {
                    "entity_uid": e.entity_uid,
                    "display_name": e.display_name,
                    "entity_type": e.entity_type.code,
                    "valid_from": e.valid_from,
                    "valid_to": e.valid_to,
                    "details": {r["detail_code"]: r["value_json"] for r in details},
                }
            )
        return Response(data)


@extend_schema(
    tags=["diff"],
    summary="Diff of changes between timestamps",
    parameters=[
        OpenApiParameter("from", OpenApiTypes.DATETIME, OpenApiParameter.QUERY, required=True),
        OpenApiParameter("to", OpenApiTypes.DATETIME, OpenApiParameter.QUERY, required=True),
    ],
    responses={200: OpenApiTypes.OBJECT},
)
class DiffView(APIView):
    """Return audit log entries within the given time window."""

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        from_raw = request.query_params.get("from")
        to_raw = request.query_params.get("to")
        if not from_raw or not to_raw:
            return Response({"detail": "from/to required"}, status=400)
        df = parse_datetime(from_raw)
        dt = parse_datetime(to_raw)
        if not df or not dt:
            return Response({"detail": "invalid datetime"}, status=400)
        if timezone.is_naive(df):
            df = timezone.make_aware(df)
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt)
        from apps.audit.models import AuditLog

        logs = (
            AuditLog.objects.filter(change_ts__gte=df, change_ts__lt=dt)
            .order_by("change_ts")
            .values()
        )
        return Response({"changes": list(logs)})
