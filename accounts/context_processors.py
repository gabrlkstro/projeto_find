def user_roles(request):
    """
    Context processor para disponibilizar permissões do usuário em todos os templates.
    """
    if not request.user.is_authenticated:
        return {'is_bolsista_user': False, 'is_admin_user': False}
    
    is_admin = request.user.groups.filter(name="Administradores").exists() or request.user.is_staff
    is_bolsista = request.user.groups.filter(name="Bolsistas").exists() or is_admin
    
    return {
        'is_bolsista_user': is_bolsista,
        'is_admin_user': is_admin
    }
