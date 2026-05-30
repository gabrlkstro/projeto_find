"""
API REST completa para o app mobile (React Native).
Todos os endpoints do app apontam para /api/v1/
"""
import json
import datetime

from django.contrib.auth.models import User
from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Item, Categoria, Profile, Chat, Mensagem


# ─── Helpers ──────────────────────────────────────────────────

def _item_to_dict(item, request=None):
    imagem_url = None
    if item.imagem:
        if request:
            imagem_url = request.build_absolute_uri(item.imagem.url)
        else:
            imagem_url = item.imagem.url
    return {
        "id": item.id,
        "titulo": item.titulo,
        "descricao": item.descricao,
        "local": item.local,
        "status": item.status,
        "status_display": item.get_status_display(),
        "data": str(item.data),
        "imagem": imagem_url,
        "slug": item.slug,
        "usuario": item.usuario.username,
        "categoria": item.categoria.nome if item.categoria else None,
    }


def _mensagem_to_dict(msg):
    return {
        "id": msg.id,
        "texto": msg.texto,
        "remetente": msg.remetente.username,
        "criado_em": msg.criado_em.isoformat() if hasattr(msg, 'criado_em') else str(msg.data_envio) if hasattr(msg, 'data_envio') else "",
    }


# ─── AUTH ─────────────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([AllowAny])
def api_register(request):
    """Registra um novo usuário e retorna tokens JWT."""
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        payload = request.POST.dict()

    username = (payload.get("username") or "").strip()
    email = (payload.get("email") or "").strip()
    password = payload.get("password") or ""
    full_name = (payload.get("full_name") or "").strip()

    if not username:
        return Response({"ok": False, "detail": "Username é obrigatório."}, status=400)
    if len(password) < 8:
        return Response({"ok": False, "detail": "A senha deve ter pelo menos 8 caracteres."}, status=400)
    if User.objects.filter(username=username).exists():
        return Response({"ok": False, "detail": "Username já está em uso."}, status=400)

    parts = full_name.split(" ", 1)
    user = User.objects.create_user(
        username=username, email=email, password=password,
        first_name=parts[0] if parts else "",
        last_name=parts[1] if len(parts) > 1 else "",
        is_active=True,
    )
    Profile.objects.get_or_create(user=user)
    refresh = RefreshToken.for_user(user)

    return Response({
        "ok": True,
        "data": {"user": {"username": user.username, "email": user.email}},
        "tokens": {"access": str(refresh.access_token), "refresh": str(refresh)},
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def api_profile(request):
    """Retorna o perfil do usuário autenticado."""
    user = request.user
    profile, _ = Profile.objects.get_or_create(user=user)
    foto_url = None
    if profile.foto:
        foto_url = request.build_absolute_uri(profile.foto.url)
    return Response({
        "ok": True,
        "data": {
            "username": user.username,
            "email": user.email,
            "full_name": f"{user.first_name} {user.last_name}".strip(),
            "first_name": user.first_name,
            "last_name": user.last_name,
            "telefone": getattr(profile, 'telefone', '') or '',
            "cidade": getattr(profile, 'cidade', '') or '',
            "estado": getattr(profile, 'estado', '') or '',
            "foto": foto_url,
        }
    })


# ─── ITENS ────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([AllowAny])
def api_items(request):
    """Lista itens com filtros e paginação."""
    q = (request.GET.get("q") or "").strip()
    status = (request.GET.get("status") or "todos").strip().lower()
    try:
        page = max(1, int(request.GET.get("page", 1)))
        per_page = min(100, max(1, int(request.GET.get("per_page", 20))))
    except (TypeError, ValueError):
        page, per_page = 1, 20

    qs = Item.objects.select_related("usuario", "categoria").order_by("-id")
    if q:
        qs = qs.filter(Q(titulo__icontains=q) | Q(descricao__icontains=q) | Q(local__icontains=q))
    if status in ["perdido", "achado", "devolvido"]:
        qs = qs.filter(status=status)

    start = (page - 1) * per_page
    items_page = list(qs[start:start + per_page + 1])
    has_more = len(items_page) > per_page
    items_page = items_page[:per_page]

    return Response({
        "ok": True,
        "results": [_item_to_dict(i, request) for i in items_page],
        "page": page,
        "has_more": has_more,
    })


@api_view(["GET"])
@permission_classes([AllowAny])
def api_item_detail(request, item_id):
    """Retorna detalhes de um item."""
    try:
        item = Item.objects.select_related("usuario", "categoria").get(id=item_id)
    except Item.DoesNotExist:
        return Response({"ok": False, "detail": "Item não encontrado."}, status=404)
    return Response({"ok": True, "data": _item_to_dict(item, request)})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_create_item(request):
    """Cria um novo item."""
    data = request.POST if request.POST else request.data
    titulo = (data.get("titulo") or "").strip()
    descricao = (data.get("descricao") or "").strip()
    local = (data.get("local") or "").strip()
    status = (data.get("status") or "perdido").strip().lower()
    categoria_id = data.get("categoria")
    data_item = data.get("data") or str(datetime.date.today())

    if not titulo:
        return Response({"ok": False, "detail": "Título é obrigatório."}, status=400)
    if status not in ["perdido", "achado", "devolvido"]:
        status = "perdido"

    categoria = None
    if categoria_id:
        try:
            categoria = Categoria.objects.get(id=categoria_id)
        except Categoria.DoesNotExist:
            pass

    imagem = request.FILES.get("imagem")
    item = Item.objects.create(
        titulo=titulo, descricao=descricao, local=local,
        status=status, categoria=categoria, usuario=request.user,
        data=data_item, imagem=imagem,
    )
    return Response({"ok": True, "data": _item_to_dict(item, request)}, status=201)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def api_my_items(request):
    """Lista os itens do usuário autenticado."""
    try:
        page = max(1, int(request.GET.get("page", 1)))
        per_page = min(100, max(1, int(request.GET.get("per_page", 20))))
    except (TypeError, ValueError):
        page, per_page = 1, 20

    qs = Item.objects.filter(usuario=request.user).order_by("-id")
    start = (page - 1) * per_page
    items_page = list(qs[start:start + per_page + 1])
    has_more = len(items_page) > per_page
    items_page = items_page[:per_page]

    return Response({
        "ok": True,
        "results": [_item_to_dict(i, request) for i in items_page],
        "page": page,
        "has_more": has_more,
    })


@api_view(["GET"])
@permission_classes([AllowAny])
def api_stats(request):
    """Retorna estatísticas gerais do sistema."""
    total = Item.objects.count()
    return Response({
        "ok": True,
        "data": {
            "total": total,
            "perdidos": Item.objects.filter(status="perdido").count(),
            "encontrados": Item.objects.filter(status="achado").count(),
            "devolvidos": Item.objects.filter(status="devolvido").count(),
        }
    })


@api_view(["GET"])
@permission_classes([AllowAny])
def api_categories(request):
    """Lista todas as categorias."""
    cats = Categoria.objects.all().values("id", "nome")
    return Response({"ok": True, "results": list(cats)})


# ─── CHATS ────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def api_chats(request):
    """Lista os chats do usuário."""
    chats = Chat.objects.filter(
        Q(comprador=request.user) | Q(item__usuario=request.user)
    ).select_related("item", "comprador", "item__usuario").order_by("-id")

    result = []
    for chat in chats:
        result.append({
            "id": chat.id,
            "item": {"id": chat.item.id, "titulo": chat.item.titulo},
            "comprador": chat.comprador.username,
            "dono": chat.item.usuario.username,
            "ativo": chat.ativo if hasattr(chat, 'ativo') else True,
        })
    return Response({"ok": True, "results": result})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_chat_start(request, item_id):
    """Inicia ou retorna um chat existente para um item."""
    try:
        item = Item.objects.get(id=item_id)
    except Item.DoesNotExist:
        return Response({"ok": False, "detail": "Item não encontrado."}, status=404)

    if item.usuario == request.user:
        return Response({"ok": False, "detail": "Você não pode abrir chat no seu próprio item."}, status=400)

    chat, created = Chat.objects.get_or_create(item=item, comprador=request.user)
    return Response({
        "ok": True,
        "data": {"id": chat.id, "item_id": item.id, "created": created}
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def api_chat_messages(request, chat_id):
    """Retorna as mensagens de um chat."""
    try:
        chat = Chat.objects.get(id=chat_id)
    except Chat.DoesNotExist:
        return Response({"ok": False, "detail": "Chat não encontrado."}, status=404)

    if request.user not in [chat.comprador, chat.item.usuario]:
        return Response({"ok": False, "detail": "Acesso negado."}, status=403)

    mensagens = Mensagem.objects.filter(chat=chat).order_by("id")
    return Response({
        "ok": True,
        "results": [_mensagem_to_dict(m) for m in mensagens]
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_chat_send(request, chat_id):
    """Envia uma mensagem em um chat."""
    try:
        chat = Chat.objects.get(id=chat_id)
    except Chat.DoesNotExist:
        return Response({"ok": False, "detail": "Chat não encontrado."}, status=404)

    if request.user not in [chat.comprador, chat.item.usuario]:
        return Response({"ok": False, "detail": "Acesso negado."}, status=403)

    texto = (request.data.get("texto") or "").strip()
    if not texto:
        return Response({"ok": False, "detail": "Mensagem vazia."}, status=400)

    msg = Mensagem.objects.create(chat=chat, remetente=request.user, texto=texto)
    return Response({"ok": True, "data": _mensagem_to_dict(msg)}, status=201)
