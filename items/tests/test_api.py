"""Testes para a API REST do app items."""
import pytest
from datetime import date

from django.contrib.auth.models import User
from rest_framework.test import APIClient

from items.models import Categoria, Item


# ──────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────
@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="itemapi",
        email="itemapi@example.com",
        password="Str0ngP@ss!",
    )


@pytest.fixture
def other_user(db):
    return User.objects.create_user(
        username="outrousuario",
        email="outro@example.com",
        password="Str0ngP@ss!",
    )


@pytest.fixture
def auth_client(api_client, user):
    resp = api_client.post("/api/token/", {"username": "itemapi", "password": "Str0ngP@ss!"})
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")
    return api_client


@pytest.fixture
def other_auth_client(api_client, other_user):
    client = APIClient()
    resp = client.post("/api/token/", {"username": "outrousuario", "password": "Str0ngP@ss!"})
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")
    return client


@pytest.fixture
def categoria(db):
    return Categoria.objects.create(nome="Eletrônicos")


@pytest.fixture
def item(user, categoria):
    return Item.objects.create(
        titulo="Notebook Dell",
        descricao="Notebook prateado",
        status="perdido",
        local="Biblioteca",
        data=date.today(),
        usuario=user,
        categoria=categoria,
    )


# ──────────────────────────────────────────────────────────────
# Listar itens (público)
# ──────────────────────────────────────────────────────────────
class TestApiListItems:

    def test_listar_itens_publico(self, api_client, item):
        resp = api_client.get("/api/items/")
        assert resp.status_code == 200
        assert resp.data["ok"] is True
        assert len(resp.data["results"]) >= 1

    def test_filtrar_por_status(self, api_client, item):
        resp = api_client.get("/api/items/?status=perdido")
        assert resp.status_code == 200
        for it in resp.data["results"]:
            assert it["status"] == "perdido"

    def test_filtrar_por_busca_texto(self, api_client, item):
        resp = api_client.get("/api/items/?q=Notebook")
        assert resp.status_code == 200
        assert len(resp.data["results"]) >= 1

    def test_busca_sem_resultados(self, api_client, item):
        resp = api_client.get("/api/items/?q=xyzinexistente123")
        assert resp.status_code == 200
        assert len(resp.data["results"]) == 0

    def test_filtrar_por_categoria(self, api_client, item, categoria):
        resp = api_client.get(f"/api/items/?categoria={categoria.id}")
        assert resp.status_code == 200
        assert len(resp.data["results"]) >= 1

    def test_paginacao(self, api_client, user, categoria):
        for i in range(25):
            Item.objects.create(
                titulo=f"Item {i}",
                descricao="desc",
                status="perdido",
                local="Local",
                data=date.today(),
                usuario=user,
                categoria=categoria,
            )
        resp = api_client.get("/api/items/?page=1&per_page=10")
        assert resp.status_code == 200
        assert len(resp.data["results"]) == 10
        assert resp.data["has_more"] is True


# ──────────────────────────────────────────────────────────────
# Detalhe de item (público)
# ──────────────────────────────────────────────────────────────
class TestApiItemDetail:

    def test_detalhe_item_existente(self, api_client, item):
        resp = api_client.get(f"/api/items/{item.id}/")
        assert resp.status_code == 200
        assert resp.data["data"]["titulo"] == "Notebook Dell"

    def test_detalhe_item_inexistente(self, api_client, db):
        resp = api_client.get("/api/items/99999/")
        assert resp.status_code == 404


# ──────────────────────────────────────────────────────────────
# Criar item (autenticado)
# ──────────────────────────────────────────────────────────────
class TestApiCreateItem:

    def test_criar_item_autenticado(self, auth_client, categoria):
        resp = auth_client.post("/api/items/criar/", {
            "titulo": "Carteira Marrom",
            "descricao": "Carteira de couro",
            "status": "achado",
            "local": "Praça do Ferreira",
            "categoria": categoria.id,
            "data": str(date.today()),
        }, format="json")
        assert resp.status_code == 201
        assert resp.data["ok"] is True
        assert resp.data["data"]["titulo"] == "Carteira Marrom"

    def test_criar_item_sem_titulo(self, auth_client):
        resp = auth_client.post("/api/items/criar/", {
            "titulo": "",
            "descricao": "desc",
            "status": "perdido",
        }, format="json")
        assert resp.status_code == 400

    def test_criar_item_nao_autenticado(self, api_client, db):
        resp = api_client.post("/api/items/criar/", {
            "titulo": "teste",
            "status": "perdido",
        }, format="json")
        assert resp.status_code == 401

    def test_criar_item_status_invalido_vira_perdido(self, auth_client):
        resp = auth_client.post("/api/items/criar/", {
            "titulo": "Item Status Invalido",
            "status": "invalido",
            "data": str(date.today()),
        }, format="json")
        assert resp.status_code == 201
        assert resp.data["data"]["status"] == "perdido"


# ──────────────────────────────────────────────────────────────
# Editar item (dono)
# ──────────────────────────────────────────────────────────────
class TestApiEditItem:

    def test_editar_item_proprio(self, auth_client, item):
        resp = auth_client.patch(f"/api/items/{item.id}/editar/", {
            "titulo": "Notebook Dell Atualizado",
        }, format="json")
        assert resp.status_code == 200
        assert resp.data["data"]["titulo"] == "Notebook Dell Atualizado"

    def test_editar_item_de_outro_usuario(self, other_auth_client, item):
        resp = other_auth_client.patch(f"/api/items/{item.id}/editar/", {
            "titulo": "Hackeado",
        }, format="json")
        assert resp.status_code == 404


# ──────────────────────────────────────────────────────────────
# Deletar item (dono)
# ──────────────────────────────────────────────────────────────
class TestApiDeleteItem:

    def test_deletar_item_proprio(self, auth_client, item):
        resp = auth_client.delete(f"/api/items/{item.id}/deletar/")
        assert resp.status_code == 200
        assert not Item.objects.filter(id=item.id).exists()

    def test_deletar_item_de_outro_usuario(self, other_auth_client, item):
        resp = other_auth_client.delete(f"/api/items/{item.id}/deletar/")
        assert resp.status_code == 404
        assert Item.objects.filter(id=item.id).exists()


# ──────────────────────────────────────────────────────────────
# Mudar status
# ──────────────────────────────────────────────────────────────
class TestApiChangeItemStatus:

    def test_mudar_status_para_achado_dono(self, auth_client, item):
        resp = auth_client.post(f"/api/items/{item.id}/status/", {
            "status": "achado",
        }, format="json")
        assert resp.status_code == 200
        assert resp.data["data"]["status"] == "achado"

    def test_mudar_status_para_devolvido_dono_barrado(self, auth_client, item):
        resp = auth_client.post(f"/api/items/{item.id}/status/", {
            "status": "devolvido",
        }, format="json")
        assert resp.status_code == 403

    def test_mudar_status_invalido(self, auth_client, item):
        resp = auth_client.post(f"/api/items/{item.id}/status/", {
            "status": "invalido",
        }, format="json")
        assert resp.status_code == 400

    def test_mudar_status_item_de_outro(self, other_auth_client, item):
        resp = other_auth_client.post(f"/api/items/{item.id}/status/", {
            "status": "devolvido",
        }, format="json")
        assert resp.status_code == 404

    def test_mudar_status_bolsista_pode_devolver(self, api_client, other_user, item):
        from django.contrib.auth.models import Group
        grupo_bolsistas, _ = Group.objects.get_or_create(name="Bolsistas")
        other_user.groups.add(grupo_bolsistas)
        
        # Authenticate other_user
        resp = api_client.post("/api/token/", {"username": other_user.username, "password": "Str0ngP@ss!"})
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")
        
        resp = api_client.post(f"/api/items/{item.id}/status/", {
            "status": "devolvido",
            "nome_recebedor": "Maria Silva"
        }, format="json")
        assert resp.status_code == 200
        assert resp.data["data"]["status"] == "devolvido"


# ──────────────────────────────────────────────────────────────
# Meus itens
# ──────────────────────────────────────────────────────────────
class TestApiMyItems:

    def test_meus_itens_retorna_apenas_meus(self, auth_client, item, other_user):
        Item.objects.create(
            titulo="Item do Outro",
            descricao="desc",
            status="perdido",
            local="Local",
            data=date.today(),
            usuario=other_user,
        )
        resp = auth_client.get("/api/meus-itens/")
        assert resp.status_code == 200
        for it in resp.data["results"]:
            assert it["usuario"] == "itemapi"


# ──────────────────────────────────────────────────────────────
# Estatísticas e Categorias (público)
# ──────────────────────────────────────────────────────────────
class TestApiStatsCategories:

    def test_stats(self, api_client, item):
        resp = api_client.get("/api/stats/")
        assert resp.status_code == 200
        assert resp.data["ok"] is True
        assert "total" in resp.data["data"]
        assert "perdidos" in resp.data["data"]
        assert "encontrados" in resp.data["data"]
        assert "devolvidos" in resp.data["data"]

    def test_categorias(self, api_client, categoria):
        resp = api_client.get("/api/categorias/")
        assert resp.status_code == 200
        assert len(resp.data["results"]) >= 1
