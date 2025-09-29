from django.http import HttpResponse, JsonResponse
from django.utils import timezone


def _payload():
    return {"status": "ok", "ts": timezone.now().isoformat()}


def health_view(request):
    if request.method == "OPTIONS":
        resp = HttpResponse(status=200)
        resp["Allow"] = "GET, HEAD, OPTIONS"
        return resp
    return JsonResponse(_payload())


live_view = health_view
ready_view = health_view
