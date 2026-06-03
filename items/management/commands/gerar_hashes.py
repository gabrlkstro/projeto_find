"""
Management command para gerar image_hash de todos os itens que têm imagem.
Uso: python manage.py gerar_hashes
"""
from django.core.management.base import BaseCommand
from items.models import Item


class Command(BaseCommand):
    help = 'Gera hashes visuais (pHash) para itens existentes com imagem'

    def handle(self, *args, **options):
        itens = Item.objects.filter(imagem__isnull=False).exclude(imagem='')
        total = itens.count()
        self.stdout.write(f"Processando {total} itens com imagem...")

        sucesso = 0
        for i, item in enumerate(itens, 1):
            try:
                item._gerar_image_hash()
                if item.image_hash:
                    sucesso += 1
                    self.stdout.write(f"  [{i}/{total}] ✓ {item.titulo} → {item.image_hash[:16]}...")
                else:
                    self.stdout.write(f"  [{i}/{total}] ✗ {item.titulo} → sem hash")
            except Exception as e:
                self.stdout.write(f"  [{i}/{total}] ✗ {item.titulo} → erro: {e}")

        self.stdout.write(self.style.SUCCESS(f"\nConcluído! {sucesso}/{total} hashes gerados."))
