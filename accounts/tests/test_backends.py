"""Testes para o backend de autenticação customizado."""
import pytest
from django.contrib.auth import authenticate
from django.contrib.auth.models import User


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="maria",
        email="maria@example.com",
        password="Senh@Segura123",
    )


class TestEmailOrUsernameBackend:
    """Testes para o EmailOrUsernameModelBackend."""

    def test_login_com_username(self, user):
        result = authenticate(username="maria", password="Senh@Segura123")
        assert result is not None
        assert result.pk == user.pk

    def test_login_com_email(self, user):
        result = authenticate(username="maria@example.com", password="Senh@Segura123")
        assert result is not None
        assert result.pk == user.pk

    def test_login_case_insensitive_username(self, user):
        result = authenticate(username="MARIA", password="Senh@Segura123")
        assert result is not None
        assert result.pk == user.pk

    def test_login_case_insensitive_email(self, user):
        result = authenticate(username="MARIA@EXAMPLE.COM", password="Senh@Segura123")
        assert result is not None
        assert result.pk == user.pk

    def test_senha_errada_retorna_none(self, user):
        result = authenticate(username="maria", password="senhaerrada")
        assert result is None

    def test_usuario_inexistente_retorna_none(self, db):
        result = authenticate(username="naoexiste", password="qualquer")
        assert result is None
