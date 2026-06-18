"""Testes para os models do app chats."""
import pytest
from datetime import date

from django.contrib.auth.models import User

from chats.models import Chat, Mensagem
from items.models import Item


# ──────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────
@pytest.fixture
def dono(db):
    return User.objects.create_user(username="dono", password="Str0ngP@ss!")


@pytest.fixture
def interessado(db):
    return User.objects.create_user(username="interessado", password="Str0ngP@ss!")


@pytest.fixture
def item(dono):
    return Item.objects.create(
        titulo="Chave de carro",
        descricao="Chave Toyota",
        status="achado",
        local="Estacionamento",
        data=date.today(),
        usuario=dono,
    )


@pytest.fixture
def chat(item, dono, interessado):
    return Chat.objects.create(
        item=item,
        criado_por=interessado,
        dono_item=dono,
        status="ativo",
    )


@pytest.fixture
def mensagem(chat, interessado):
    return Mensagem.objects.create(
        chat=chat,
        remetente=interessado,
        conteudo="Olá, essa chave é minha!",
        tipo="texto",
    )


# ──────────────────────────────────────────────────────────────
# Chat
# ──────────────────────────────────────────────────────────────
class TestChatModel:

    def test_criar_chat(self, chat):
        assert chat.pk is not None
        assert chat.status == "ativo"

    def test_chat_str_com_item(self, chat):
        assert "Chave de carro" in str(chat)

    def test_chat_str_sem_item(self, chat):
        chat.item = None
        chat.save()
        assert "Item removido" in str(chat)

    def test_chat_status_choices(self, chat):
        assert chat.status in ["ativo", "fechado"]

    def test_fechar_chat(self, chat):
        chat.status = "fechado"
        chat.save()
        chat.refresh_from_db()
        assert chat.status == "fechado"

    def test_chat_relacionamentos(self, chat, item, dono, interessado):
        assert chat.item == item
        assert chat.criado_por == interessado
        assert chat.dono_item == dono

    def test_chat_item_set_null(self, chat, item):
        """Quando o item for deletado, chat.item deve ser NULL."""
        item.delete()
        chat.refresh_from_db()
        assert chat.item is None


# ──────────────────────────────────────────────────────────────
# Mensagem
# ──────────────────────────────────────────────────────────────
class TestMensagemModel:

    def test_criar_mensagem(self, mensagem):
        assert mensagem.pk is not None
        assert mensagem.conteudo == "Olá, essa chave é minha!"

    def test_mensagem_str(self, mensagem):
        assert str(mensagem) == f"Mensagem {mensagem.id}"

    def test_mensagem_tipo_padrao(self, mensagem):
        assert mensagem.tipo == "texto"

    def test_mensagem_nao_lida_por_padrao(self, mensagem):
        assert mensagem.lida is False

    def test_marcar_como_lida(self, mensagem):
        mensagem.lida = True
        mensagem.save()
        mensagem.refresh_from_db()
        assert mensagem.lida is True

    def test_mensagem_pertence_ao_chat(self, chat, mensagem):
        assert mensagem.chat == chat
        assert mensagem in chat.mensagens.all()

    def test_mensagem_deletada_com_chat(self, chat, mensagem):
        """Mensagens devem ser deletadas quando o chat for deletado (CASCADE)."""
        msg_id = mensagem.id
        chat.delete()
        assert not Mensagem.objects.filter(id=msg_id).exists()

    def test_multiplas_mensagens_no_chat(self, chat, dono, interessado):
        Mensagem.objects.create(chat=chat, remetente=interessado, conteudo="Msg 1")
        Mensagem.objects.create(chat=chat, remetente=dono, conteudo="Msg 2")
        Mensagem.objects.create(chat=chat, remetente=interessado, conteudo="Msg 3")
        assert chat.mensagens.count() == 3

    def test_data_envio_auto(self, mensagem):
        assert mensagem.data_envio is not None
