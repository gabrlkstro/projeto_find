"""URLs da API de itens e categorias."""
from django.urls import path
from . import views

urlpatterns = [
    path("items/", views.api_items, name="api_items"),
    path("items/<int:item_id>/", views.api_item_detail, name="api_item_detail"),
    path("items/criar/", views.api_create_item, name="api_create_item"),
    path("items/<int:item_id>/editar/", views.api_edit_item, name="api_edit_item"),
    path("items/<int:item_id>/deletar/", views.api_delete_item, name="api_delete_item"),
    path("items/<int:item_id>/status/", views.api_change_item_status, name="api_change_item_status"),
    path("meus-itens/", views.api_my_items, name="api_my_items"),
    path("stats/", views.api_stats, name="api_stats"),
    path("categorias/", views.api_categories, name="api_categories"),
]
