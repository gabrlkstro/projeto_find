from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    """Perfil do usuário com foto redimensionável."""

    TAMANHOS_VALIDOS = {
        'pequeno': 150,
        'medio': 300,
        'grande': 500,
        'original': None,
    }

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(default='profile_pics/user.svg', upload_to="profile_pics")
    telefone = models.CharField(max_length=20, blank=True, null=True)
    cidade = models.CharField(max_length=100, blank=True, null=True)
    estado = models.CharField(max_length=2, blank=True, null=True)
    data_nascimento = models.DateField(null=True, blank=True)
    cep = models.CharField(max_length=9, blank=True, null=True)

    class Meta:
        db_table = 'mainpage_profile'

    def __str__(self):
        return f'Perfil de {self.user.username}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._processar_imagem()

    def _processar_imagem(self, tamanho_max=300):
        """Processa a imagem do perfil (compatível com armazenamento local e Cloudinary)."""
        from PIL import Image as PILImage
        from io import BytesIO
        from django.core.files.base import ContentFile

        if not self.image:
            return

        # Ignora imagens padrão (SVG / PNG default)
        nomes_padrao = ('profile_pics/user.png', 'profile_pics/user.svg')
        if self.image.name in nomes_padrao or self.image.name.endswith('.svg'):
            return

        try:
            # Abre a imagem via storage (funciona com local e Cloudinary)
            self.image.open('rb')
            img = PILImage.open(self.image)
            img.load()  # força leitura completa antes de fechar
            self.image.close()
        except Exception:
            return

        try:
            if img.mode in ('RGBA', 'P', 'LA'):
                img = img.convert('RGB')

            # Crop quadrado centralizado
            largura, altura = img.size
            if largura != altura:
                lado = min(largura, altura)
                left = (largura - lado) // 2
                top = (altura - lado) // 2
                img = img.crop((left, top, left + lado, top + lado))

            # Redimensiona se necessário
            if tamanho_max and img.size[0] > tamanho_max:
                img = img.resize((tamanho_max, tamanho_max), PILImage.LANCZOS)

            # Salva em buffer na memória
            buffer = BytesIO()
            img.save(buffer, format='JPEG', quality=85, optimize=True)
            buffer.seek(0)

            # Re-salva pelo storage backend (Cloudinary ou local)
            nome_arquivo = self.image.name
            self.image.save(nome_arquivo, ContentFile(buffer.read()), save=False)
            # Atualiza só o campo image sem chamar save() de novo (evita loop)
            Profile.objects.filter(pk=self.pk).update(image=self.image.name)
        except Exception:
            pass

    def redimensionar(self, tamanho='medio'):
        tamanho_px = self.TAMANHOS_VALIDOS.get(tamanho, 300)
        if tamanho_px is not None:
            self._processar_imagem(tamanho_max=tamanho_px)
