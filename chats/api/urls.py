"""URLs da API de chats."""
from django.urls import path
from . import views

urlpatterns = [
    path("chats/", views.api_chats, name="api_chats"),
    path("chats/iniciar/<int:item_id>/", views.api_chat_start, name="api_chat_start"),
    path("chats/<int:chat_id>/mensagens/", views.api_chat_messages, name="api_chat_messages"),
    path("chats/<int:chat_id>/enviar/", views.api_chat_send, name="api_chat_send"),
]
