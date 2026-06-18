"""Testes para os models do app accounts."""
import pytest
from django.contrib.auth.models import User

from accounts.models import Profile


# ──────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────
@pytest.fixture
def user(db):
    """Cria um usuário de teste."""
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="Str0ngP@ss!",
        first_name="Test",
        last_name="User",
    )


# ──────────────────────────────────────────────────────────────
# Profile — criação e __str__
# ──────────────────────────────────────────────────────────────
class TestProfileModel:
    """Testes para o model Profile."""

    def test_profile_criado_via_signal(self, user):
        """O signal post_save deve criar um Profile automaticamente."""
        assert Profile.objects.filter(user=user).exists()

    def test_profile_str(self, user):
        profile = Profile.objects.get(user=user)
        assert str(profile) == f"Perfil de {user.username}"

    def test_profile_imagem_padrao(self, user):
        profile = Profile.objects.get(user=user)
        assert "user.svg" in profile.image.name or "user.png" in profile.image.name

    def test_profile_campos_opcionais_vazios(self, user):
        """Campos opcionais devem aceitar valores nulos por padrão."""
        profile = Profile.objects.get(user=user)
        assert profile.telefone is None
        assert profile.cidade is None
        assert profile.estado is None
        assert profile.data_nascimento is None
        assert profile.cep is None

    def test_profile_atualizar_telefone(self, user):
        profile = Profile.objects.get(user=user)
        profile.telefone = "(85) 99999-0000"
        profile.save()
        profile.refresh_from_db()
        assert profile.telefone == "(85) 99999-0000"

    def test_profile_atualizar_localizacao(self, user):
        profile = Profile.objects.get(user=user)
        profile.cidade = "Fortaleza"
        profile.estado = "CE"
        profile.cep = "60000-000"
        profile.save()
        profile.refresh_from_db()
        assert profile.cidade == "Fortaleza"
        assert profile.estado == "CE"
        assert profile.cep == "60000-000"

    def test_profile_tamanhos_validos(self):
        """Verifica que TAMANHOS_VALIDOS contém os tamanhos esperados."""
        expected_keys = {"pequeno", "medio", "grande", "original"}
        assert set(Profile.TAMANHOS_VALIDOS.keys()) == expected_keys
        assert Profile.TAMANHOS_VALIDOS["pequeno"] == 150
        assert Profile.TAMANHOS_VALIDOS["medio"] == 300
        assert Profile.TAMANHOS_VALIDOS["grande"] == 500
        assert Profile.TAMANHOS_VALIDOS["original"] is None

    def test_profile_um_para_um_com_user(self, user):
        """Cada user deve ter exatamente um profile."""
        assert Profile.objects.filter(user=user).count() == 1

    def test_profile_deletado_com_user(self, user):
        """Profile deve ser deletado quando o User for deletado (CASCADE)."""
        user_id = user.id
        user.delete()
        assert not Profile.objects.filter(user_id=user_id).exists()
