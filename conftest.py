"""
Configuração global do pytest para o projeto Find.
- Usa FileSystemStorage em vez do DatabaseStorage (evita travamento nos testes)
- Desabilita processamento de imagem no Profile (evita I/O pesado)
"""
import django
from django.conf import settings


def pytest_configure(config):
    """Ajusta settings ANTES do Django inicializar para os testes."""
    # Usa storage padrão do filesystem nos testes (rápido e sem dependência de DB)
    settings.STORAGES = {
        'default': {
            'BACKEND': 'django.core.files.storage.FileSystemStorage',
        },
        'staticfiles': {
            'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
        },
    }
    # Usa hasher MD5 rápido para acelerar criação de usuários nos testes
    settings.PASSWORD_HASHERS = [
        'django.contrib.auth.hashers.MD5PasswordHasher',
    ]


def pytest_collection_modifyitems(config, items):
    """Desabilita processamento de imagem nos testes para evitar lentidão."""
    from unittest.mock import patch

    # Patch aplicado globalmente durante a coleta — fica ativo em todos os testes
    patcher = patch('accounts.models.Profile._processar_imagem', return_value=None)
    patcher.start()
    config._profile_patcher = patcher


def pytest_unconfigure(config):
    """Remove patches ao finalizar."""
    patcher = getattr(config, '_profile_patcher', None)
    if patcher:
        patcher.stop()
