"""
API REST completa para o app mobile (React Native).
Todos os endpoints do app apontam para /api/
"""
import json
import datetime

from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404
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
        "data": str(item.data) if item.data else "",
        "imagem": imagem_url,
        "slug": item.slug,
        "usuario": item.usuario.username,
        "usuario_id": item.usuario_id,
        "categoria": item.categoria.nome if item.categoria else None,
        "categoria_id": item.categoria_id,
        "criado_em": item.criado_em.isoformat() if item.criado_em else "",
    }


def _mensagem_to_dict(msg, request_user_id=None):
    return {
        "id": msg.id,
        "conteudo": msg.conteudo,
        "remetente": msg.remetente.username,
        "remetente_id": msg.remetente_id,
        "is_me": msg.remetente_id == request_user_id if request_user_id else False,
        "data_envio": msg.data_envio.isoformat() if msg.data_envio else "",
        "lida": msg.lida,
    }


def _chat_to_dict(chat, request_user):
    """Serializa um chat com informações do outro participante."""
    # Determina quem é o 'outro' usuário
    if request_user.id == chat.criado_por_id:
        outro = chat.dono_item
    else:
        outro = chat.criado_por

    # Iniciais do outro usuário
    nome_outro = outro.get_full_name() or outro.username
    partes = nome_outro.strip().split(" ")
    if len(partes) > 1:
        iniciais = (partes[0][0] + partes[-1][0]).upper()
    else:
        iniciais = partes[0][:2].upper()

    # Última mensagem
    ultima = chat.mensagens.order_by("-data_envio").first()
    nao_lidas = chat.mensagens.filter(lida=False).exclude(remetente=request_user).count()

    return {
        "id": chat.id,
        "item": {
            "id": chat.item.id if chat.item else None,
            "titulo": chat.item.titulo if chat.item else "Item removido",
        },
        "outro_usuario": {
            "id": outro.id,
            "username": outro.username,
            "nome": nome_outro,
            "iniciais": iniciais,
        },
        "status": chat.status,
        "nao_lidas": nao_lidas,
        "ultima_mensagem": ultima.conteudo if ultima else "",
        "ultima_hora": ultima.data_envio.isoformat() if ultima else "",
        "atualizado_em": chat.atualizado_em.isoformat() if chat.atualizado_em else "",
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
    data_nascimento = payload.get("data_nascimento") or None

    if not username:
        return Response({"ok": False, "detail": "Username é obrigatório."}, status=400)
    if len(password) < 8:
        return Response({"ok": False, "detail": "A senha deve ter pelo menos 8 caracteres."}, status=400)
    if User.objects.filter(username=username).exists():
        return Response({"ok": False, "detail": "Username já está em uso."}, status=400)
    if email and User.objects.filter(email=email).exists():
        return Response({"ok": False, "detail": "E-mail já está em uso."}, status=400)

    parts = full_name.split(" ", 1)
    user = User.objects.create_user(
        username=username, email=email, password=password,
        first_name=parts[0] if parts else "",
        last_name=parts[1] if len(parts) > 1 else "",
        is_active=True,
    )
    profile, _ = Profile.objects.get_or_create(user=user)

    if data_nascimento:
        try:
            from datetime import date as _date
            profile.data_nascimento = _date.fromisoformat(data_nascimento)
            profile.save(update_fields=["data_nascimento"])
        except (ValueError, TypeError):
            pass

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
    if profile.image:
        try:
            foto_url = request.build_absolute_uri(profile.image.url)
        except Exception:
            pass
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
            "data_nascimento": str(profile.data_nascimento) if profile.data_nascimento else '',
            "foto": foto_url,
        }
    })


@api_view(["POST", "PUT", "PATCH"])
@permission_classes([IsAuthenticated])
def api_update_profile(request):
    """
    Atualiza o perfil do usuário autenticado.
    
    Aceita os campos: full_name, first_name, last_name, username,
    telefone, cidade, estado, cep, image (arquivo), tamanho.
    
    O parâmetro 'tamanho' define a resolução da foto de perfil:
      - 'pequeno' (150px)
      - 'medio' (300px) — padrão
      - 'grande' (500px)
      - 'original' (sem redimensionar)
    """
    user = request.user
    profile, _ = Profile.objects.get_or_create(user=user)
    data = request.data

    # Atualiza campos do User
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    full_name = data.get("full_name")

    if full_name:
        parts = full_name.strip().split(" ", 1)
        user.first_name = parts[0]
        user.last_name = parts[1] if len(parts) > 1 else ""
    else:
        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name

    username = data.get("username")
    if username and username != user.username:
        if User.objects.filter(username=username).exclude(id=user.id).exists():
            return Response({"ok": False, "detail": "Username já está em uso."}, status=400)
        user.username = username

    user.save()

    # Atualiza campos do Profile
    if "telefone" in data:
        profile.telefone = data["telefone"]
    if "cidade" in data:
        profile.cidade = data["cidade"]
    if "estado" in data:
        profile.estado = data["estado"]
    if "cep" in data:
        profile.cep = data["cep"]

    # Foto de perfil via upload
    nova_foto = request.FILES.get("image")
    if nova_foto:
        profile.image = nova_foto

    profile.save()

    # Redimensiona para o tamanho solicitado (se enviou foto ou pediu redimensionamento)
    tamanho = (data.get("tamanho") or "medio").strip().lower()
    if nova_foto or "tamanho" in data:
        profile.redimensionar(tamanho)

    # Monta URL da foto atualizada
    foto_url = None
    if profile.image:
        try:
            foto_url = request.build_absolute_uri(profile.image.url)
        except Exception:
            pass

    return Response({
        "ok": True,
        "detail": "Perfil atualizado com sucesso.",
        "data": {
            "username": user.username,
            "email": user.email,
            "full_name": f"{user.first_name} {user.last_name}".strip(),
            "first_name": user.first_name,
            "last_name": user.last_name,
            "telefone": getattr(profile, 'telefone', '') or '',
            "cidade": getattr(profile, 'cidade', '') or '',
            "estado": getattr(profile, 'estado', '') or '',
            "data_nascimento": str(profile.data_nascimento) if profile.data_nascimento else '',
            "foto": foto_url,
            "tamanho_aplicado": tamanho,
            "tamanhos_disponiveis": list(Profile.TAMANHOS_VALIDOS.keys()),
        }
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_resize_photo(request):
    """
    Redimensiona a foto de perfil existente para um tamanho escolhido.
    Enviar: { "tamanho": "pequeno" | "medio" | "grande" | "original" }
    """
    user = request.user
    profile, _ = Profile.objects.get_or_create(user=user)

    if not profile.image or profile.image.name == 'profile_pics/user.png':
        return Response({"ok": False, "detail": "Nenhuma foto de perfil para redimensionar."}, status=400)

    tamanho = (request.data.get("tamanho") or "medio").strip().lower()
    if tamanho not in Profile.TAMANHOS_VALIDOS:
        return Response({
            "ok": False,
            "detail": f"Tamanho inválido. Use: {', '.join(Profile.TAMANHOS_VALIDOS.keys())}",
        }, status=400)

    profile.redimensionar(tamanho)

    foto_url = None
    try:
        foto_url = request.build_absolute_uri(profile.image.url)
    except Exception:
        pass

    return Response({
        "ok": True,
        "detail": f"Foto redimensionada para '{tamanho}'.",
        "data": {
            "foto": foto_url,
            "tamanho_aplicado": tamanho,
        }
    })


@api_view(["GET"])
@permission_classes([AllowAny])
def api_photo_sizes(request):
    """Retorna os tamanhos de foto de perfil disponíveis."""
    return Response({
        "ok": True,
        "data": {
            nome: {"label": nome.capitalize(), "pixels": px}
            for nome, px in Profile.TAMANHOS_VALIDOS.items()
        }
    })

# ─── ITENS ────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([AllowAny])
def api_items(request):
    """Lista itens com filtros e paginação."""
    q = (request.GET.get("q") or "").strip()
    status = (request.GET.get("status") or "todos").strip().lower()
    categoria_id = request.GET.get("categoria")
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
    if categoria_id and str(categoria_id).isdigit():
        qs = qs.filter(categoria_id=int(categoria_id))

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


@api_view(["PUT", "PATCH"])
@permission_classes([IsAuthenticated])
def api_edit_item(request, item_id):
    """Edita um item do usuário autenticado."""
    item = get_object_or_404(Item, id=item_id, usuario=request.user)
    data = request.POST if request.POST else request.data

    if "titulo" in data and data["titulo"]:
        item.titulo = data["titulo"].strip()
    if "descricao" in data:
        item.descricao = data["descricao"].strip()
    if "local" in data:
        item.local = data["local"].strip()
    if "status" in data and data["status"] in ["perdido", "achado", "devolvido"]:
        item.status = data["status"]
    if "categoria" in data:
        try:
            item.categoria = Categoria.objects.get(id=data["categoria"])
        except (Categoria.DoesNotExist, ValueError, TypeError):
            pass
    if "data" in data:
        item.data = data["data"]
    if request.FILES.get("imagem"):
        item.imagem = request.FILES["imagem"]

    item.save()
    return Response({"ok": True, "data": _item_to_dict(item, request)})


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def api_delete_item(request, item_id):
    """Deleta um item do usuário autenticado."""
    item = get_object_or_404(Item, id=item_id, usuario=request.user)
    item.delete()
    return Response({"ok": True, "detail": "Item deletado com sucesso."})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_change_item_status(request, item_id):
    """Altera o status de um item do usuário autenticado."""
    item = get_object_or_404(Item, id=item_id, usuario=request.user)
    novo_status = (request.data.get("status") or "").strip().lower()

    if novo_status not in ["perdido", "achado", "devolvido"]:
        return Response({"ok": False, "detail": "Status inválido. Use: perdido, achado ou devolvido."}, status=400)

    item.status = novo_status
    item.save(update_fields=["status", "atualizado_em"])
    return Response({"ok": True, "data": _item_to_dict(item, request)})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def api_my_items(request):
    """Lista os itens do usuário autenticado."""
    try:
        page = max(1, int(request.GET.get("page", 1)))
        per_page = min(100, max(1, int(request.GET.get("per_page", 20))))
    except (TypeError, ValueError):
        page, per_page = 1, 20

    qs = Item.objects.filter(usuario=request.user).select_related("categoria").order_by("-id")
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
    """Lista os chats do usuário autenticado."""
    chats = (
        Chat.objects
        .filter(Q(criado_por=request.user) | Q(dono_item=request.user))
        .select_related("item", "criado_por", "dono_item")
        .prefetch_related("mensagens")
        .order_by("-atualizado_em", "-criado_em")
    )

    return Response({
        "ok": True,
        "results": [_chat_to_dict(chat, request.user) for chat in chats],
    })


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

    chat, created = Chat.objects.get_or_create(
        item=item,
        criado_por=request.user,
        dono_item=item.usuario,
        defaults={"status": "ativo"},
    )

    if not created and chat.status != "ativo":
        chat.status = "ativo"
        chat.save(update_fields=["status"])

    return Response({
        "ok": True,
        "data": {
            "id": chat.id,
            "item_id": item.id,
            "created": created,
            "chat": _chat_to_dict(chat, request.user),
        }
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def api_chat_messages(request, chat_id):
    """Retorna as mensagens de um chat."""
    try:
        chat = Chat.objects.select_related("criado_por", "dono_item").get(id=chat_id)
    except Chat.DoesNotExist:
        return Response({"ok": False, "detail": "Chat não encontrado."}, status=404)

    if request.user.id not in (chat.criado_por_id, chat.dono_item_id):
        return Response({"ok": False, "detail": "Acesso negado."}, status=403)

    # Marca como lidas as mensagens do outro usuário
    Mensagem.objects.filter(chat=chat, lida=False).exclude(remetente=request.user).update(lida=True)

    mensagens = (
        Mensagem.objects
        .filter(chat=chat)
        .select_related("remetente")
        .order_by("data_envio")
    )

    return Response({
        "ok": True,
        "chat_id": chat.id,
        "status": chat.status,
        "results": [_mensagem_to_dict(m, request.user.id) for m in mensagens],
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_chat_send(request, chat_id):
    """Envia uma mensagem em um chat."""
    try:
        chat = Chat.objects.select_related("criado_por", "dono_item").get(id=chat_id)
    except Chat.DoesNotExist:
        return Response({"ok": False, "detail": "Chat não encontrado."}, status=404)

    if request.user.id not in (chat.criado_por_id, chat.dono_item_id):
        return Response({"ok": False, "detail": "Acesso negado."}, status=403)

    if chat.status != "ativo":
        return Response({"ok": False, "detail": "Esse chat está fechado."}, status=400)

    conteudo = (request.data.get("conteudo") or request.data.get("texto") or "").strip()
    if not conteudo:
        return Response({"ok": False, "detail": "Mensagem vazia."}, status=400)

    from django.utils import timezone
    msg = Mensagem.objects.create(
        chat=chat,
        remetente=request.user,
        conteudo=conteudo,
        tipo="texto",
        lida=False,
    )

    chat.atualizado_em = timezone.now()
    chat.save(update_fields=["atualizado_em"])

    return Response({
        "ok": True,
        "data": _mensagem_to_dict(msg, request.user.id),
    }, status=201)
