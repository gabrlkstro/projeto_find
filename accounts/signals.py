from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def adicionar_grupo_usuarios(sender, instance, created, **kwargs):
    if created:
        # Só adiciona ao grupo 'Usuários' se não estiver em nenhum grupo ainda
        if not instance.groups.exists():
            grupo, _ = Group.objects.get_or_create(name="Usuários")
            instance.groups.add(grupo)
