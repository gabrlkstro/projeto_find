"""URLs da API REST para o app mobile."""
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import api_views

urlpatterns = [
    # ─── Auth ───────────────────────────────────────────────
    path("token/", TokenObtainPairView.as_view(), name="api_token"),
    path("token/refresh/", TokenRefreshView.as_view(), name="api_token_refresh"),
    path("register/", api_views.api_register, name="api_register"),
    path("profile/", api_views.api_profile, name="api_profile"),
    path("profile/update/", api_views.api_update_profile, name="api_update_profile"),
    path("profile/resize-photo/", api_views.api_resize_photo, name="api_resize_photo"),
    path("profile/photo-sizes/", api_views.api_photo_sizes, name="api_photo_sizes"),

    # ─── Itens ──────────────────────────────────────────────
    path("items/", api_views.api_items, name="api_items"),
    path("items/<int:item_id>/", api_views.api_item_detail, name="api_item_detail"),
    path("items/criar/", api_views.api_create_item, name="api_create_item"),
    path("items/<int:item_id>/editar/", api_views.api_edit_item, name="api_edit_item"),
    path("items/<int:item_id>/deletar/", api_views.api_delete_item, name="api_delete_item"),
    path("items/<int:item_id>/status/", api_views.api_change_item_status, name="api_change_item_status"),
    path("meus-itens/", api_views.api_my_items, name="api_my_items"),
    path("stats/", api_views.api_stats, name="api_stats"),
    path("categorias/", api_views.api_categories, name="api_categories"),

    # ─── Chats ──────────────────────────────────────────────
    path("chats/", api_views.api_chats, name="api_chats"),
    path("chats/iniciar/<int:item_id>/", api_views.api_chat_start, name="api_chat_start"),
    path("chats/<int:chat_id>/mensagens/", api_views.api_chat_messages, name="api_chat_messages"),
    path("chats/<int:chat_id>/enviar/", api_views.api_chat_send, name="api_chat_send"),
]
