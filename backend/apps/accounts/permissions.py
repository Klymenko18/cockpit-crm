from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsSelfOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_staff:
            return True
        return obj.pk == user.pk
