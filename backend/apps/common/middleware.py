import uuid
from typing import Optional

from django.utils.deprecation import MiddlewareMixin

_TRACE_HEADER = "HTTP_X_REQUEST_ID"
_RESP_HEADER = "X-Request-ID"


class TraceIdMiddleware(MiddlewareMixin):
    def process_request(self, request):
        rid = request.META.get(_TRACE_HEADER) or str(uuid.uuid4())
        request.trace_id = rid

    def process_response(self, request, response):
        rid = getattr(request, "trace_id", None) or str(uuid.uuid4())
        response[_RESP_HEADER] = rid
        return response


class TraceIdFilter:
    def __init__(self, *args, **kwargs):
        pass

    def filter(self, record):
        record.trace_id = getattr(getattr(record, "request", None), "trace_id", None) or ""
        record.status_code = getattr(record, "status_code", "") or ""
        record.path = getattr(getattr(record, "request", None), "path", "") or ""
        return True
