from django.urls import path

from .views import (
    MeUpdateView,
    MeView,
    PasswordChangeView,
    UserRetrieveUpdateDelete,
    UsersListCreate,
)

app_name = "accounts"

urlpatterns = [
    path(
        "users", UsersListCreate.as_view(), name="users_list_create"
    ),
    path(
        "users/<int:pk>", UserRetrieveUpdateDelete.as_view(), name="users_rud"
    ),  
    path("users/me", MeView.as_view(), name="users_me"), 
    path("users/me/update", MeUpdateView.as_view(), name="users_me_update"),  
    path(
        "users/me/password", PasswordChangeView.as_view(), name="users_me_password"
    ),  
]
