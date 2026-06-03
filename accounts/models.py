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
    image = models.ImageField(default='profile_pics/user.png', upload_to="profile_pics")
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
        from PIL import Image as PILImage
        import os

        if not self.image or self.image.name == 'profile_pics/user.png':
            return
        try:
            img_path = self.image.path
        except Exception:
            return
        if not os.path.isfile(img_path):
            return
        try:
            img = PILImage.open(img_path)
            if img.mode in ('RGBA', 'P', 'LA'):
                img = img.convert('RGB')
            largura, altura = img.size
            if largura != altura:
                lado = min(largura, altura)
                left = (largura - lado) // 2
                top = (altura - lado) // 2
                img = img.crop((left, top, left + lado, top + lado))
            if tamanho_max and img.size[0] > tamanho_max:
                img = img.resize((tamanho_max, tamanho_max), PILImage.LANCZOS)
            img.save(img_path, 'JPEG', quality=85, optimize=True)
        except Exception:
            pass

    def redimensionar(self, tamanho='medio'):
        tamanho_px = self.TAMANHOS_VALIDOS.get(tamanho, 300)
        if tamanho_px is not None:
            self._processar_imagem(tamanho_max=tamanho_px)
