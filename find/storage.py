"""
Storage backend que salva arquivos de mídia no banco de dados.
Funciona com MySQL (Railway), SQLite ou qualquer DB configurado.
Assim as imagens persistem mesmo no Render (filesystem efêmero).
"""
import mimetypes
from io import BytesIO

from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.http import Http404, HttpResponse
from django.utils.crypto import get_random_string


class DatabaseStorage(Storage):
    """Storage backend que persiste arquivos no banco de dados."""

    def _get_model(self):
        from items.models import ArquivoMidia
        return ArquivoMidia

    def _save(self, name, content):
        ArquivoMidia = self._get_model()

        data = content.read()
        content_type = getattr(content, 'content_type', None)
        if not content_type:
            content_type, _ = mimetypes.guess_type(name)
            content_type = content_type or 'application/octet-stream'

        ArquivoMidia.objects.update_or_create(
            nome=name,
            defaults={
                'conteudo': data,
                'content_type': content_type,
                'tamanho': len(data),
            },
        )
        return name

    def _open(self, name, mode='rb'):
        ArquivoMidia = self._get_model()
        try:
            arquivo = ArquivoMidia.objects.get(nome=name)
            return ContentFile(arquivo.conteudo)
        except ArquivoMidia.DoesNotExist:
            raise FileNotFoundError(f"Arquivo não encontrado: {name}")

    def exists(self, name):
        ArquivoMidia = self._get_model()
        return ArquivoMidia.objects.filter(nome=name).exists()

    def url(self, name):
        return f'/media-db/{name}'

    def delete(self, name):
        ArquivoMidia = self._get_model()
        ArquivoMidia.objects.filter(nome=name).delete()

    def size(self, name):
        ArquivoMidia = self._get_model()
        try:
            return ArquivoMidia.objects.get(nome=name).tamanho
        except ArquivoMidia.DoesNotExist:
            return 0

    def get_available_name(self, name, max_length=None):
        """Gera nome único se já existir."""
        if not self.exists(name):
            return name

        # Adiciona sufixo aleatório
        import os
        base, ext = os.path.splitext(name)
        while True:
            novo_nome = f"{base}_{get_random_string(7)}{ext}"
            if not self.exists(novo_nome):
                return novo_nome


def serve_db_media(request, path):
    """View que serve arquivos armazenados no banco de dados."""
    from items.models import ArquivoMidia

    try:
        arquivo = ArquivoMidia.objects.only('conteudo', 'content_type').get(nome=path)
    except ArquivoMidia.DoesNotExist:
        raise Http404("Arquivo não encontrado.")

    response = HttpResponse(arquivo.conteudo, content_type=arquivo.content_type)
    response['Cache-Control'] = 'public, max-age=86400'  # cache 24h no browser
    return response
