from datetime import datetime

from django.db.models import Q, F
from django.utils.dateparse import parse_datetime
from django.utils import timezone

from rest_framework import status, serializers
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiTypes,
    inline_serializer,
)

from apps.core.services.scd2 import (
    update_entity,
    update_entity_detail,
    close_entity,
    close_entity_detail,
)
from apps.core.models import Entity, EntityDetail, EntityType
from apps.core.serializers import (
    EntitySnapshotSerializer,
    EntityUpsertSerializer,
    EntityDetailUpsertSerializer,
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
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        qs = Entity.objects.filter(is_current=True)
        q = request.query_params.get("q")
        if q:
            qs = qs.filter(display_name__icontains=q)
        type_code = request.query_params.get("type")
        if type_code:
            qs = qs.filter(entity_type__code=type_code)
        detail_code = request.query_params.get("detail_code")
        detail_value = request.query_params.get("detail_value")
        if detail_code:
            sub = EntityDetail.objects.filter(
                entity_uid=F("entity_uid"),
                detail_code=detail_code,
                is_current=True,
            ).values("entity_uid")
            if detail_value is not None:
                qs = qs.filter(
                    entity_uid__in=EntityDetail.objects.filter(
                        detail_code=detail_code, is_current=True, value_json=detail_value
                    ).values("entity_uid")
                )
            else:
                qs = qs.filter(entity_uid__in=sub)
        data = EntitySnapshotSerializer(qs.order_by("display_name")[:200], many=True).data
        return Response(data)

    def post(self, request):
        s = EntityUpsertSerializer(
            data=request.data,
            context={"actor": request.user if request.user.is_authenticated else "api"},
        )
        s.is_valid(raise_exception=True)
        res = s.save()

        details = request.data.get("details")
        det_res = []
        if isinstance(details, list):
            for d in details:
                ds = EntityDetailUpsertSerializer(
                    data={
                        "entity_uid": s.validated_data["entity_uid"],
                        "detail_code": d["detail_code"],
                        "value_json": d["value_json"],
                        "change_ts": d.get("change_ts"),
                    },
                    context={
                        "actor": request.user if request.user.is_authenticated else "api"
                    },
                )
                ds.is_valid(raise_exception=True)
                det_res.append(ds.save())
        out = {"entity": res}
        if det_res:
            out["details"] = det_res
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
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, entity_uid):
        obj = Entity.objects.filter(entity_uid=entity_uid, is_current=True).first()
        if not obj:
            return Response({"detail": "not found"}, status=404)
        return Response(EntitySnapshotSerializer(obj).data)

    def patch(self, request, entity_uid):
        data = request.data.copy()
        data["entity_uid"] = str(entity_uid)
        if "entity_type" in data and not EntityType.objects.filter(code=data["entity_type"]).exists():
            return Response({"detail": "invalid entity_type"}, status=400)
        res = {}
        upd = {}
        if set(data.keys()) & {"display_name", "entity_type", "change_ts"}:
            if "entity_type" in data:
                et = EntityType.objects.get(code=data["entity_type"])
            else:
                et = Entity.objects.get(entity_uid=entity_uid, is_current=True).entity_type
            s = EntityUpsertSerializer(
                data={
                    "entity_uid": entity_uid,
                    "display_name": data.get("display_name")
                    or Entity.objects.get(entity_uid=entity_uid, is_current=True).display_name,
                    "entity_type": et.code,
                    "change_ts": data.get("change_ts"),
                },
                context={
                    "actor": request.user if request.user.is_authenticated else "api"
                },
            )
            s.is_valid(raise_exception=True)
            upd = s.save()
        details = data.get("details")
        det_res = []
        if isinstance(details, list):
            for d in details:
                ds = EntityDetailUpsertSerializer(
                    data={
                        "entity_uid": entity_uid,
                        "detail_code": d["detail_code"],
                        "value_json": d["value_json"],
                        "change_ts": d.get("change_ts"),
                    },
                    context={
                        "actor": request.user if request.user.is_authenticated else "api"
                    },
                )
                ds.is_valid(raise_exception=True)
                det_res.append(ds.save())
        res["entity"] = upd or {"status": "noop"}
        if det_res:
            res["details"] = det_res
        return Response(res)

    def delete(self, request, entity_uid):
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
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, entity_uid):
        qs = (
            EntityDetail.objects.filter(entity_uid=entity_uid, is_current=True)
            .values("detail_code", "value_json")
        )
        return Response({r["detail_code"]: r["value_json"] for r in qs})

    def post(self, request, entity_uid):
        payloads = request.data if isinstance(request.data, list) else [request.data]
        out = []
        for d in payloads:
            ds = EntityDetailUpsertSerializer(
                data={
                    "entity_uid": entity_uid,
                    "detail_code": d["detail_code"],
                    "value_json": d["value_json"],
                    "change_ts": d.get("change_ts"),
                },
                context={
                    "actor": request.user if request.user.is_authenticated else "api"
                },
            )
            ds.is_valid(raise_exception=True)
            out.append(ds.save())
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
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, entity_uid, detail_code):
        obj = EntityDetail.objects.filter(
            entity_uid=entity_uid, detail_code=detail_code, is_current=True
        ).first()
        if not obj:
            return Response({"detail": "not found"}, status=404)
        return Response({"detail_code": detail_code, "value_json": obj.value_json})

    def patch(self, request, entity_uid, detail_code):
        ds = EntityDetailUpsertSerializer(
            data={
                "entity_uid": entity_uid,
                "detail_code": detail_code,
                "value_json": request.data["value_json"],
                "change_ts": request.data.get("change_ts"),
            },
            context={"actor": request.user if request.user.is_authenticated else "api"},
        )
        ds.is_valid(raise_exception=True)
        return Response(ds.save())

    def delete(self, request, entity_uid, detail_code):
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
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, entity_uid):
        ent = list(
            Entity.objects.filter(entity_uid=entity_uid)
            .order_by("valid_from")
            .values()
        )
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
