from django.contrib.auth.models import Group

def criar_grupos_padrao(sender=None, **kwargs):
    """Cria os grupos padrão do sistema: Bolsistas, Administradores e Usuários."""
    Group.objects.get_or_create(name="Bolsistas")
    Group.objects.get_or_create(name="Administradores")
    Group.objects.get_or_create(name="Usuários")
