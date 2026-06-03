from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


class Categoria(models.Model):
    nome = models.CharField(max_length=45)
    descricao = models.CharField(max_length=45, blank=True)

    class Meta:
        db_table = 'mainpage_categoria'

    def __str__(self):
        return self.nome


class Item(models.Model):
    STATUS_CHOICES = [
        ('achado', 'Achado'),
        ('perdido', 'Perdido'),
        ('devolvido', 'Devolvido'),
    ]

    titulo = models.CharField(max_length=45)
    slug = models.SlugField(max_length=60, unique=True, blank=True)
    descricao = models.CharField(max_length=200)
    status = models.CharField(max_length=45, choices=STATUS_CHOICES)
    local = models.CharField(max_length=45)
    data = models.DateField()
    imagem = models.ImageField(upload_to='itens/', blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='itens')
    categoria = models.ForeignKey('Categoria', on_delete=models.SET_NULL, null=True)

    class Meta:
        db_table = 'mainpage_item'

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.titulo)
            slug = base_slug
            contador = 1
            while Item.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{contador}"
                contador += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.titulo
