from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('menu/', views.menu_view, name='menu'),
    path('tela/', views.screen_user, name='screen_user'),
    path('redefinir-senha/', auth_views.PasswordResetView.as_view(template_name='mainpage/password_reset.html'),name='password_reset'),
    path('redefinir-senha/enviado/', auth_views.PasswordResetDoneView.as_view(template_name='mainpage/password_reset_done.html'), name='password_reset_done'),
    path('redefinir-senha/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='mainpage/password_reset_confirm.html'), name='password_reset_confirm'),
    path('redefinir-senha/concluido/', auth_views.PasswordResetCompleteView.as_view(template_name='mainpage/password_reset_complete.html'), name='password_reset_complete'),
    path('upload-photo/', views.upload_photo, name='upload_photo'),
    path('perfil/atualizar/', views.update_profile, name='update_profile'),
    path('perfil/item/novo/', views.register_item, name='register_item'),
    path('itens/', views.list_item, name='item_list'),
    path('item/<int:id>/', views.item_detail, name='item_detail'),
    path('item/editar/<int:id>/', views.edit_item, name='item_edit'),
    path('item/deletar/<int:id>/', views.delete_item, name='item_delete'),
]
