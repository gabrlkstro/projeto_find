"""
Management command para criar categorias padrão no banco de dados.
Uso: python manage.py criar_categorias
"""
from django.core.management.base import BaseCommand
from items.models import Categoria


class Command(BaseCommand):
    help = 'Cria categorias padrão de itens no banco de dados se não existirem'

    def handle(self, *args, **options):
        categorias_padrao = [
            {"nome": "Eletrônicos", "descricao": "Celulares, notebooks, fones, carregadores"},
            {"nome": "Documentos", "descricao": "RG, CPF, CNH, cartões, carteiras"},
            {"nome": "Objetos Pessoais", "descricao": "Chaves, mochilas, óculos, bolsas"},
            {"nome": "Vestuário", "descricao": "Roupas, calçados, casacos, bonés"},
            {"nome": "Livros e Papelaria", "descricao": "Livros, cadernos, estojos, agendas"},
            {"nome": "Outros", "descricao": "Outros objetos não especificados"},
        ]

        self.stdout.write("Verificando/Criando categorias padrão...")
        criadas = 0
        existentes = 0

        for cat in categorias_padrao:
            obj, created = Categoria.objects.get_or_create(
                nome=cat["nome"],
                defaults={"descricao": cat["descricao"]}
            )
            if created:
                criadas += 1
                self.stdout.write(self.style.SUCCESS(f"  ✓ Categoria '{cat['nome']}' criada."))
            else:
                existentes += 1
                self.stdout.write(f"  - Categoria '{cat['nome']}' já existe.")

        self.stdout.write(self.style.SUCCESS(f"\nConcluído! {criadas} criadas, {existentes} já existiam."))
