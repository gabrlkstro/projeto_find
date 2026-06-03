from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


class Profile(models.Model):
    """Perfil do usuário com foto redimensionável."""

    # Tamanhos pré-definidos que o app pode solicitar
    TAMANHOS_VALIDOS = {
        'pequeno': 150,
        'medio': 300,
        'grande': 500,
        'original': None,  # mantém o tamanho original
    }

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(default='profile_pics/user.png', upload_to="profile_pics")
    telefone = models.CharField(max_length=20, blank=True, null=True)
    cidade = models.CharField(max_length=100, blank=True, null=True)
    estado = models.CharField(max_length=2, blank=True, null=True)
    data_nascimento = models.DateField(null=True, blank=True)
    cep = models.CharField(max_length=9, blank=True, null=True)

    def __str__(self):
        return f'Perfil de {self.user.username}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._processar_imagem()

    def _processar_imagem(self, tamanho_max=300):
        """
        Redimensiona e otimiza a foto de perfil.
        - Recorta para quadrado (centralizado)
        - Redimensiona para tamanho_max x tamanho_max
        - Converte para JPEG otimizado
        Pula se for a imagem padrão ou se o arquivo não existir.
        """
        from PIL import Image as PILImage
        import os

        if not self.image:
            return

        # Não processa a imagem padrão
        if self.image.name == 'profile_pics/user.png':
            return

        try:
            img_path = self.image.path
        except Exception:
            return

        if not os.path.isfile(img_path):
            return

        try:
            img = PILImage.open(img_path)

            # Converte para RGB (remove canal alpha de PNGs)
            if img.mode in ('RGBA', 'P', 'LA'):
                img = img.convert('RGB')

            # Recorta para quadrado (centralizado)
            largura, altura = img.size
            if largura != altura:
                lado = min(largura, altura)
                left = (largura - lado) // 2
                top = (altura - lado) // 2
                img = img.crop((left, top, left + lado, top + lado))

            # Redimensiona se necessário
            if tamanho_max and img.size[0] > tamanho_max:
                img = img.resize((tamanho_max, tamanho_max), PILImage.LANCZOS)

            # Salva como JPEG otimizado
            img.save(img_path, 'JPEG', quality=85, optimize=True)

        except Exception:
            pass  # Se falhar o processamento, mantém a imagem original

    def redimensionar(self, tamanho='medio'):
        """
        Redimensiona a foto de perfil para um tamanho pré-definido.
        Tamanhos: 'pequeno' (150px), 'medio' (300px), 'grande' (500px), 'original'.
        """
        tamanho_px = self.TAMANHOS_VALIDOS.get(tamanho, 300)
        if tamanho_px is not None:
            self._processar_imagem(tamanho_max=tamanho_px)


class Categoria(models.Model):
    nome = models.CharField(max_length=45)
    descricao = models.CharField(max_length=45, blank=True)

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


class Chat(models.Model):
    STATUS_CHOICES = [
        ('ativo', 'Ativo'),
        ('fechado', 'Fechado'),
    ]

    item = models.ForeignKey(
        Item,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chats'
    )

    criado_por = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chats_criados')
    dono_item = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chats_como_dono')

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ativo')

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

    def __str__(self):
        return f"Mensagem {self.id}"
