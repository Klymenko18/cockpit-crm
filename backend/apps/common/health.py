from django.db import connection
from django.http import JsonResponse

def live_view(_):
    return JsonResponse({"status": "live"}, status=200)

def ready_view(_):
    try:
        connection.ensure_connection()
        return JsonResponse({"status": "ready"}, status=200)
    except Exception as exc:
        return JsonResponse({"status": "not_ready", "error": str(exc)}, status=503)
