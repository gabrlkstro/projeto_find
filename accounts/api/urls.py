"""URLs da API de contas e perfil."""
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

urlpatterns = [
    path("token/", TokenObtainPairView.as_view(), name="api_token"),
    path("token/refresh/", TokenRefreshView.as_view(), name="api_token_refresh"),
    path("register/", views.api_register, name="api_register"),
    path("profile/", views.api_profile, name="api_profile"),
    path("profile/update/", views.api_update_profile, name="api_update_profile"),
    path("profile/resize-photo/", views.api_resize_photo, name="api_resize_photo"),
    path("profile/photo-sizes/", views.api_photo_sizes, name="api_photo_sizes"),
]
