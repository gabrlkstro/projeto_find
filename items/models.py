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
    image_hash = models.CharField(max_length=64, blank=True, null=True, db_index=True)
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
        self._gerar_image_hash()

    def _gerar_image_hash(self):
        """Gera pHash da imagem para busca visual."""
        if not self.imagem:
            return
        try:
            import imagehash
            from PIL import Image as PILImage
            import os

            img_path = self.imagem.path
            if not os.path.isfile(img_path):
                return

            img = PILImage.open(img_path)
            phash = str(imagehash.phash(img, hash_size=16))

            if self.image_hash != phash:
                Item.objects.filter(pk=self.pk).update(image_hash=phash)
                self.image_hash = phash
        except Exception:
            pass

    @staticmethod
    def buscar_por_imagem(imagem_file, limite=20):
        """
        Busca itens visualmente similares a uma imagem enviada.
        Retorna lista de (item, similaridade%) ordenada por relevância.
        """
        import imagehash
        from PIL import Image as PILImage

        img = PILImage.open(imagem_file)
        query_hash = imagehash.phash(img, hash_size=16)

        itens_com_hash = Item.objects.exclude(
            image_hash__isnull=True
        ).exclude(image_hash='').select_related('usuario', 'categoria')

        resultados = []
        for item in itens_com_hash:
            try:
                item_hash = imagehash.hex_to_hash(item.image_hash)
                distancia = query_hash - item_hash
                similaridade = max(0, 100 - (distancia / 256 * 100))
                if similaridade >= 30:
                    resultados.append((item, round(similaridade, 1)))
            except Exception:
                continue

        resultados.sort(key=lambda x: x[1], reverse=True)
        return resultados[:limite]

    def __str__(self):
        return self.titulo
