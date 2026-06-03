from django.db import models
from django.contrib.auth.models import User
from items.models import Item


class Chat(models.Model):
    STATUS_CHOICES = [
        ('ativo', 'Ativo'),
        ('fechado', 'Fechado'),
    ]

    item = models.ForeignKey(Item, on_delete=models.SET_NULL, null=True, blank=True, related_name='chats')
    criado_por = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chats_criados')
    dono_item = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chats_como_dono')
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ativo')

    class Meta:
        db_table = 'mainpage_chat'

    def __str__(self):
        if self.item:
            return f"Chat #{self.id} - {self.item.titulo}"
        return f"Chat #{self.id} - Item removido"


class Mensagem(models.Model):
    TIPO_CHOICES = [
        ('texto', 'Texto'),
        ('imagem', 'Imagem'),
    ]

    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='mensagens')
    remetente = models.ForeignKey(User, on_delete=models.CASCADE)
    conteudo = models.TextField(max_length=200)
    data_envio = models.DateTimeField(auto_now_add=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='texto')
    lida = models.BooleanField(default=False)

    class Meta:
        db_table = 'mainpage_mensagem'

    def __str__(self):
        return f"Mensagem {self.id}"
