from django.urls import path
from .views import (
    UsersListCreate,
    UserRetrieveUpdateDelete,
    MeView,
    MeUpdateView,
    PasswordChangeView,
)

app_name = "accounts"

urlpatterns = [
    path("users/", UsersListCreate.as_view(), name="users_list_create"),            # POST register, GET list (admin)
    path("users/<int:pk>/", UserRetrieveUpdateDelete.as_view(), name="users_rud"),  # GET/PATCH self or admin, DELETE admin
    path("users/me/", MeView.as_view(), name="users_me"),                           # GET my profile
    path("users/me/update/", MeUpdateView.as_view(), name="users_me_update"),       # PATCH my profile
    path("users/me/password/", PasswordChangeView.as_view(), name="users_me_password"),  # POST change password
]
