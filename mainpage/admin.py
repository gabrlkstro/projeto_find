from django.contrib import admin
from .models import (
    Profile,
    Categoria,
    Item,
    Chat,
    Mensagem
)

admin.site.register(Profile)
admin.site.register(Categoria)
admin.site.register(Item)
admin.site.register(Chat)
admin.site.register(Mensagem)
