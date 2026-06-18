"""Testes para a API REST do app chats."""
import pytest
from datetime import date

from django.contrib.auth.models import User
from rest_framework.test import APIClient

from chats.models import Chat, Mensagem
from items.models import Item


# ──────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────
@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def dono(db):
    return User.objects.create_user(
        username="dono_chat",
        email="dono@chat.com",
        password="Str0ngP@ss!",
    )


@pytest.fixture
def interessado(db):
    return User.objects.create_user(
        username="interessado_chat",
        email="interessado@chat.com",
        password="Str0ngP@ss!",
    )


@pytest.fixture
def terceiro(db):
    return User.objects.create_user(
        username="terceiro",
        email="terceiro@chat.com",
        password="Str0ngP@ss!",
    )


@pytest.fixture
def item(dono):
    return Item.objects.create(
        titulo="Relógio Fossil",
        descricao="Relógio prata",
        status="achado",
        local="Parque",
        data=date.today(),
        usuario=dono,
    )


@pytest.fixture
def auth_dono(dono):
    client = APIClient()
    resp = client.post("/api/token/", {"username": "dono_chat", "password": "Str0ngP@ss!"})
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")
    return client


@pytest.fixture
def auth_interessado(interessado):
    client = APIClient()
    resp = client.post("/api/token/", {"username": "interessado_chat", "password": "Str0ngP@ss!"})
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")
    return client


@pytest.fixture
def auth_terceiro(terceiro):
    client = APIClient()
    resp = client.post("/api/token/", {"username": "terceiro", "password": "Str0ngP@ss!"})
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")
    return client


@pytest.fixture
def chat(item, dono, interessado):
    return Chat.objects.create(
        item=item,
        criado_por=interessado,
        dono_item=dono,
        status="ativo",
    )


# ──────────────────────────────────────────────────────────────
# Iniciar chat
# ──────────────────────────────────────────────────────────────
class TestApiChatStart:

    def test_iniciar_chat(self, auth_interessado, item):
        resp = auth_interessado.post(f"/api/chats/iniciar/{item.id}/")
        assert resp.status_code == 200
        assert resp.data["ok"] is True
        assert resp.data["data"]["created"] is True

    def test_nao_pode_iniciar_chat_proprio_item(self, auth_dono, item):
        resp = auth_dono.post(f"/api/chats/iniciar/{item.id}/")
        assert resp.status_code == 400

    def test_iniciar_chat_item_inexistente(self, auth_interessado, db):
        resp = auth_interessado.post("/api/chats/iniciar/99999/")
        assert resp.status_code == 404

    def test_iniciar_chat_duplicado_retorna_existente(self, auth_interessado, item, chat):
        resp = auth_interessado.post(f"/api/chats/iniciar/{item.id}/")
        assert resp.status_code == 200
        assert resp.data["data"]["created"] is False
        assert resp.data["data"]["id"] == chat.id

    def test_nao_autenticado(self, api_client, item):
        resp = api_client.post(f"/api/chats/iniciar/{item.id}/")
        assert resp.status_code == 401


# ──────────────────────────────────────────────────────────────
# Listar chats
# ──────────────────────────────────────────────────────────────
class TestApiChatsList:

    def test_listar_chats_do_dono(self, auth_dono, chat):
        resp = auth_dono.get("/api/chats/")
        assert resp.status_code == 200
        assert len(resp.data["results"]) >= 1

    def test_listar_chats_do_interessado(self, auth_interessado, chat):
        resp = auth_interessado.get("/api/chats/")
        assert resp.status_code == 200
        assert len(resp.data["results"]) >= 1

    def test_terceiro_nao_ve_chat(self, auth_terceiro, chat):
        resp = auth_terceiro.get("/api/chats/")
        assert resp.status_code == 200
        assert len(resp.data["results"]) == 0


# ──────────────────────────────────────────────────────────────
# Mensagens do chat
# ──────────────────────────────────────────────────────────────
class TestApiChatMessages:

    def test_ver_mensagens(self, auth_interessado, chat):
        Mensagem.objects.create(
            chat=chat,
            remetente=chat.criado_por,
            conteudo="Oi, achei um relógio!",
        )
        resp = auth_interessado.get(f"/api/chats/{chat.id}/mensagens/")
        assert resp.status_code == 200
        assert len(resp.data["results"]) == 1

    def test_terceiro_nao_ve_mensagens(self, auth_terceiro, chat):
        resp = auth_terceiro.get(f"/api/chats/{chat.id}/mensagens/")
        assert resp.status_code == 403

    def test_chat_inexistente(self, auth_interessado, db):
        resp = auth_interessado.get("/api/chats/99999/mensagens/")
        assert resp.status_code == 404

    def test_marca_como_lida_ao_buscar(self, auth_dono, chat, interessado):
        """Quando o dono busca mensagens, as do interessado devem ser marcadas como lidas."""
        msg = Mensagem.objects.create(
            chat=chat,
            remetente=interessado,
            conteudo="Mensagem não lida",
            lida=False,
        )
        auth_dono.get(f"/api/chats/{chat.id}/mensagens/")
        msg.refresh_from_db()
        assert msg.lida is True


# ──────────────────────────────────────────────────────────────
# Enviar mensagem
# ──────────────────────────────────────────────────────────────
class TestApiChatSend:

    def test_enviar_mensagem(self, auth_interessado, chat):
        resp = auth_interessado.post(f"/api/chats/{chat.id}/enviar/", {
            "conteudo": "Esse relógio é meu!",
        }, format="json")
        assert resp.status_code == 201
        assert resp.data["ok"] is True
        assert resp.data["data"]["conteudo"] == "Esse relógio é meu!"

    def test_enviar_mensagem_vazia(self, auth_interessado, chat):
        resp = auth_interessado.post(f"/api/chats/{chat.id}/enviar/", {
            "conteudo": "",
        }, format="json")
        assert resp.status_code == 400

    def test_enviar_mensagem_chat_fechado(self, auth_interessado, chat):
        chat.status = "fechado"
        chat.save()
        resp = auth_interessado.post(f"/api/chats/{chat.id}/enviar/", {
            "conteudo": "Tentando enviar",
        }, format="json")
        assert resp.status_code == 400

    def test_terceiro_nao_envia(self, auth_terceiro, chat):
        resp = auth_terceiro.post(f"/api/chats/{chat.id}/enviar/", {
            "conteudo": "Invasor",
        }, format="json")
        assert resp.status_code == 403

    def test_dono_tambem_envia(self, auth_dono, chat):
        resp = auth_dono.post(f"/api/chats/{chat.id}/enviar/", {
            "conteudo": "Pode vir buscar!",
        }, format="json")
        assert resp.status_code == 201
