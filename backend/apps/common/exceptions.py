import uuid

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    trace_id = str(uuid.uuid4())

    if response is None:
        return Response(
            {
                "error": {
                    "code": "server_error",
                    "message": str(exc),
                    "trace_id": trace_id,
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    data = {
        "error": {
            "code": response.status_code,
            "message": response.data,
            "trace_id": trace_id,
        }
    }
    return Response(data, status=response.status_code)
