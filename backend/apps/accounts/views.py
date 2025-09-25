from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiTypes
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import IsSelfOrAdmin
from .serializers import (
    UserListSerializer,
    UserDetailSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    PasswordChangeSerializer,
)

User = get_user_model()

@extend_schema_view(
    post=extend_schema(tags=["users"], summary="Register a new user", request=UserCreateSerializer, responses={201: UserDetailSerializer}),
    get=extend_schema(tags=["users"], summary="List users (admin only)", responses={200: UserListSerializer(many=True)}),
)
class UsersListCreate(APIView):
    """
    POST /users/  -> registration (AllowAny)
    GET  /users/  -> list (IsAdminUser)
    """
    def get_permissions(self):
        if self.request.method == "POST":
            return [AllowAny()]
        return [IsAdminUser()]

    def post(self, request):
        s = UserCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = s.save()
        return Response(UserDetailSerializer(user).data, status=status.HTTP_201_CREATED)

    def get(self, request):
        qs = User.objects.all().order_by("id")
        return Response(UserListSerializer(qs, many=True).data)


@extend_schema_view(
    get=extend_schema(tags=["users"], summary="Get user by id (self or admin)", responses={200: UserDetailSerializer}),
    patch=extend_schema(tags=["users"], summary="Update user by id (self or admin)", request=UserUpdateSerializer, responses={200: UserDetailSerializer}),
    delete=extend_schema(tags=["users"], summary="Deactivate user (admin only)", responses={200: OpenApiTypes.OBJECT}),
)
class UserRetrieveUpdateDelete(APIView):
    permission_classes = [IsAuthenticated, IsSelfOrAdmin]

    def get_object(self, pk):
        return User.objects.filter(pk=pk).first()

    def get(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response({"detail": "not found"}, status=404)
        self.check_object_permissions(request, obj)
        return Response(UserDetailSerializer(obj).data)

    def patch(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response({"detail": "not found"}, status=404)
        self.check_object_permissions(request, obj)
        s = UserUpdateSerializer(obj, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        s.save()
        return Response(UserDetailSerializer(obj).data)

    def delete(self, request, pk):
        if not request.user.is_staff:
            return Response({"detail": "Admin only."}, status=403)
        obj = self.get_object(pk)
        if not obj:
            return Response({"detail": "not found"}, status=404)
        obj.is_active = False
        obj.save(update_fields=["is_active"])
        return Response({"status": "deactivated"})


@extend_schema(
    tags=["users"],
    summary="Get my profile",
    responses={200: UserDetailSerializer},
)
class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserDetailSerializer(request.user).data)


@extend_schema(
    tags=["users"],
    summary="Update my profile",
    request=UserUpdateSerializer,
    responses={200: UserDetailSerializer},
)
class MeUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        s = UserUpdateSerializer(request.user, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        s.save()
        return Response(UserDetailSerializer(request.user).data)


@extend_schema(
    tags=["users"],
    summary="Change my password",
    request=PasswordChangeSerializer,
    responses={200: OpenApiTypes.OBJECT},
)
class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        s = PasswordChangeSerializer(data=request.data, context={"request": request})
        s.is_valid(raise_exception=True)
        s.save()
        return Response({"status": "password_changed"})
