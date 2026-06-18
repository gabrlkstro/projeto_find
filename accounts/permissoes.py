from rest_framework.permissions import BasePermission
from django.core.exceptions import PermissionDenied
from django.contrib.auth.views import redirect_to_login

class IsBolsista(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.groups.filter(name="Bolsistas").exists()
        )

class IsAdministrador(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            (request.user.groups.filter(name="Administradores").exists() or request.user.is_staff)
        )

class IsBolsistaOuAdmin(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return (
            request.user.groups.filter(name="Bolsistas").exists() or
            request.user.groups.filter(name="Administradores").exists() or
            request.user.is_staff
        )

def check_bolsista_ou_admin(user):
    if not user.is_authenticated:
        return False
    return (
        user.groups.filter(name="Bolsistas").exists() or
        user.groups.filter(name="Administradores").exists() or
        user.is_staff
    )

def bolsista_required(view_func):
    """
    Decorator para views Django tradicionais.
    Exige que o usuário seja bolsista ou administrador.
    Redireciona para a página de login se não estiver autenticado.
    Lança PermissionDenied (403) se logado mas sem a permissão.
    """
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path(), login_url='login')
        if check_bolsista_ou_admin(request.user):
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return _wrapped_view
