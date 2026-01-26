from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # HOME / AUTENTICAÇÃO
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),

    # PÁGINAS PRINCIPAIS
    path('menu/', views.menu_view, name='menu'),
    path('tela/', views.screen_user, name='screen_user'),

    # RESET DE SENHA
    path(
        'redefinir-senha/',
        auth_views.PasswordResetView.as_view(
            template_name='mainpage/password_reset.html'
        ),
        name='password_reset'
    ),
    path(
        'redefinir-senha/enviado/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='mainpage/password_reset_done.html'
        ),
        name='password_reset_done'
    ),
    path(
        'redefinir-senha/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='mainpage/password_reset_confirm.html'
        ),
        name='password_reset_confirm'
    ),
    path(
        'redefinir-senha/concluido/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='mainpage/password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),

    # PERFIL
    path('upload-photo/', views.upload_photo, name='upload_photo'),
    path('perfil/atualizar/', views.update_profile, name='update_profile'),

    # ITENS
    path('perfil/item/novo/', views.register_item, name='register_item'),
    path('itens/', views.list_item, name='item_list'),
    path('itens/perdidos/', views.items_perdidos, name='items_perdidos'),
    path('itens/encontrados/', views.items_encontrados, name='items_encontrados'),
    path('item/<slug:slug>/', views.item_detail, name='item_detail'),
    path('item/editar/<int:id>/', views.edit_item, name='item_edit'),
    path('item/deletar/<int:id>/', views.delete_item, name='item_delete'),
    path("meus-itens/", views.my_itens, name="my_itens"),


    # CHAT
    path('chats/', views.chats_list, name='chats_list'),
    path('chats/iniciar/<int:item_id>/', views.chat_start, name='chat_start'),
    path('chats/<int:chat_id>/', views.chat_detail, name='chat_detail'),
    path('chats/<int:chat_id>/mensagens/', views.chat_messages, name='chat_messages'),
    path('chats/<int:chat_id>/enviar/', views.chat_send_message, name='chat_send_message'),
    path('chats/<int:chat_id>/fechar/', views.chat_close, name='chat_close'),

]
