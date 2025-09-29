from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from django.db.models import F, Q, Value
from django.db.models.functions import Coalesce
from django.utils.dateparse import parse_date, parse_datetime
from django.utils.timezone import make_aware, now
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Entity, EntityDetail


def _parse_as_of(raw: Optional[str]):
    """
    Parse `as_of` from query string. Accepts ISO date or datetime.
    If only a date is provided, uses start of that day in current timezone.
    """
    if not raw:
        return now()
    dt = parse_datetime(raw)
    if dt:
        return dt if dt.tzinfo else make_aware(dt)
    d = parse_date(raw)
    if d:
        return make_aware(type(now())(d.year, d.month, d.day))
    return now()


@dataclass
class AsOfEntity:
    entity_uid: str
    display_name: str
    entity_type: Optional[str]
    valid_from: Any
    valid_to: Any
    details: List[Dict[str, Any]]


class EntitiesAsOfView(APIView):
    """
    Return current snapshot *as of* a timestamp across Entities and their Details.

    Query params:
      - as_of: ISO date or datetime (optional; defaults to now)
      - q: free-text search on display_name (optional)
      - type: filter by EntityType.code (optional)
      - detail_code: require a current detail with this code as of (optional)
    """

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="As-of snapshot of entities and details",
        parameters=[
            OpenApiParameter(
                "as_of", str, OpenApiParameter.QUERY, description="ISO date or datetime"
            ),
            OpenApiParameter("q", str, OpenApiParameter.QUERY, description="Search display_name"),
            OpenApiParameter("type", str, OpenApiParameter.QUERY, description="EntityType code"),
            OpenApiParameter(
                "detail_code",
                str,
                OpenApiParameter.QUERY,
                description="Filter entities that have this detail as-of",
            ),
        ],
        responses={200: dict},
        tags=["entities"],
    )
    def get(self, request, *args, **kwargs):
        as_of = _parse_as_of(request.query_params.get("as_of"))
        q = request.query_params.get("q")
        type_code = request.query_params.get("type")
        detail_code = request.query_params.get("detail_code")

        entities_qs = (
            Entity.objects.select_related("entity_type")
            .filter(valid_from__lte=as_of)
            .filter(Q(valid_to__isnull=True) | Q(valid_to__gt=as_of))
        )
        if q:
            entities_qs = entities_qs.filter(display_name__icontains=q)
        if type_code:
            entities_qs = entities_qs.filter(entity_type__code=type_code)

        if detail_code:
            exists_detail = EntityDetail.objects.filter(
                entity_uid=F("entity__entity_uid"),
                detail_code=detail_code,
                valid_from__lte=as_of,
            ).filter(Q(valid_to__isnull=True) | Q(valid_to__gt=as_of))
            entities_qs = entities_qs.filter(exists_detail.exists())

    
        result: List[AsOfEntity] = []
        entity_uids = list(entities_qs.values_list("entity_uid", flat=True))
        details_by_uid: Dict[str, List[Dict[str, Any]]] = {}

        if entity_uids:
            details_qs = (
                EntityDetail.objects.filter(entity_uid__in=entity_uids, valid_from__lte=as_of)
                .filter(Q(valid_to__isnull=True) | Q(valid_to__gt=as_of))
                .order_by("entity_uid", "detail_code", "valid_from")
            )
            for d in details_qs:
                details_by_uid.setdefault(str(d.entity_uid), []).append(
                    {
                        "detail_code": d.detail_code,
                        "value_json": d.value_json,
                        "valid_from": d.valid_from,
                        "valid_to": d.valid_to,
                    }
                )

        for e in entities_qs.order_by("entity_uid", "valid_from"):
            result.append(
                AsOfEntity(
                    entity_uid=str(e.entity_uid),
                    display_name=e.display_name,
                    entity_type=e.entity_type.code if e.entity_type_id else None,
                    valid_from=e.valid_from,
                    valid_to=e.valid_to,
                    details=details_by_uid.get(str(e.entity_uid), []),
                ).__dict__
            )

        return Response(
            {"as_of": as_of, "count": len(result), "results": result}, status=status.HTTP_200_OK
        )


class DiffView(APIView):
    """
    Return list of changes (Entity and Detail) between two timestamps.

    Semantics:
      - OPEN events where valid_from is in [from, to)
      - CLOSE events where valid_to is in (from, to] (strict on left to avoid double-count)
    """

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Change diff between two instants",
        parameters=[
            OpenApiParameter(
                "from", str, OpenApiParameter.QUERY, description="ISO date/datetime (inclusive)"
            ),
            OpenApiParameter(
                "to", str, OpenApiParameter.QUERY, description="ISO date/datetime (exclusive)"
            ),
        ],
        responses={200: dict},
        tags=["entities"],
    )
    def get(self, request, *args, **kwargs):
        raw_from = request.query_params.get("from")
        raw_to = request.query_params.get("to")
        if not raw_from or not raw_to:
            return Response(
                {"detail": "Query params 'from' and 'to' are required (ISO date or datetime)."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ts_from = _parse_as_of(raw_from)
        ts_to = _parse_as_of(raw_to)
        if ts_to <= ts_from:
            return Response(
                {"detail": "'to' must be greater than 'from'."}, status=status.HTTP_400_BAD_REQUEST
            )

        changes: List[Dict[str, Any]] = []

       
        for e in Entity.objects.filter(valid_from__gte=ts_from, valid_from__lt=ts_to):
            changes.append(
                {
                    "kind": "entity",
                    "op": "OPEN",
                    "entity_uid": str(e.entity_uid),
                    "at": e.valid_from,
                    "after": {
                        "display_name": e.display_name,
                        "entity_type": e.entity_type.code if e.entity_type_id else None,
                    },
                }
            )
     
        for e in Entity.objects.filter(valid_to__gt=ts_from, valid_to__lte=ts_to):
            changes.append(
                {
                    "kind": "entity",
                    "op": "CLOSE",
                    "entity_uid": str(e.entity_uid),
                    "at": e.valid_to,
                }
            )

        
        for d in EntityDetail.objects.filter(valid_from__gte=ts_from, valid_from__lt=ts_to):
            changes.append(
                {
                    "kind": "detail",
                    "op": "OPEN",
                    "entity_uid": str(d.entity_uid),
                    "detail_code": d.detail_code,
                    "at": d.valid_from,
                    "after": {"value_json": d.value_json},
                }
            )
   
        for d in EntityDetail.objects.filter(valid_to__gt=ts_from, valid_to__lte=ts_to):
            changes.append(
                {
                    "kind": "detail",
                    "op": "CLOSE",
                    "entity_uid": str(d.entity_uid),
                    "detail_code": d.detail_code,
                    "at": d.valid_to,
                }
            )

        changes.sort(key=lambda x: (x["at"], x["kind"], x["op"]))
        return Response(
            {"from": ts_from, "to": ts_to, "count": len(changes), "results": changes},
            status=status.HTTP_200_OK,
        )
