"""API views para o sistema de chat."""
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from items.models import Item
from chats.models import Chat, Mensagem


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
    if request_user.id == chat.criado_por_id:
        outro = chat.dono_item
    else:
        outro = chat.criado_por

    nome_outro = outro.get_full_name() or outro.username
    partes = nome_outro.strip().split(" ")
    if len(partes) > 1:
        iniciais = (partes[0][0] + partes[-1][0]).upper()
    else:
        iniciais = partes[0][:2].upper()

    ultima = chat.mensagens.order_by("-data_envio").first()
    nao_lidas = chat.mensagens.filter(lida=False).exclude(remetente=request_user).count()

    return {
        "id": chat.id,
        "item": {"id": chat.item.id if chat.item else None, "titulo": chat.item.titulo if chat.item else "Item removido"},
        "outro_usuario": {"id": outro.id, "username": outro.username, "nome": nome_outro, "iniciais": iniciais},
        "status": chat.status,
        "nao_lidas": nao_lidas,
        "ultima_mensagem": ultima.conteudo if ultima else "",
        "ultima_hora": ultima.data_envio.isoformat() if ultima else "",
        "atualizado_em": chat.atualizado_em.isoformat() if chat.atualizado_em else "",
    }


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def api_chats(request):
    chats = (
        Chat.objects
        .filter(Q(criado_por=request.user) | Q(dono_item=request.user))
        .select_related("item", "criado_por", "dono_item")
        .prefetch_related("mensagens")
        .order_by("-atualizado_em", "-criado_em")
    )
    return Response({"ok": True, "results": [_chat_to_dict(chat, request.user) for chat in chats]})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_chat_start(request, item_id):
    try:
        item = Item.objects.get(id=item_id)
    except Item.DoesNotExist:
        return Response({"ok": False, "detail": "Item não encontrado."}, status=404)
    if item.usuario == request.user:
        return Response({"ok": False, "detail": "Você não pode abrir chat no seu próprio item."}, status=400)
    chat, created = Chat.objects.get_or_create(
        item=item, criado_por=request.user, dono_item=item.usuario, defaults={"status": "ativo"},
    )
    if not created and chat.status != "ativo":
        chat.status = "ativo"
        chat.save(update_fields=["status"])
    return Response({"ok": True, "data": {"id": chat.id, "item_id": item.id, "created": created, "chat": _chat_to_dict(chat, request.user)}})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def api_chat_messages(request, chat_id):
    try:
        chat = Chat.objects.select_related("criado_por", "dono_item").get(id=chat_id)
    except Chat.DoesNotExist:
        return Response({"ok": False, "detail": "Chat não encontrado."}, status=404)
    if request.user.id not in (chat.criado_por_id, chat.dono_item_id):
        return Response({"ok": False, "detail": "Acesso negado."}, status=403)
    Mensagem.objects.filter(chat=chat, lida=False).exclude(remetente=request.user).update(lida=True)
    mensagens = Mensagem.objects.filter(chat=chat).select_related("remetente").order_by("data_envio")
    return Response({"ok": True, "chat_id": chat.id, "status": chat.status, "results": [_mensagem_to_dict(m, request.user.id) for m in mensagens]})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_chat_send(request, chat_id):
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
    msg = Mensagem.objects.create(chat=chat, remetente=request.user, conteudo=conteudo, tipo="texto", lida=False)
    chat.atualizado_em = timezone.now()
    chat.save(update_fields=["atualizado_em"])
    return Response({"ok": True, "data": _mensagem_to_dict(msg, request.user.id)}, status=201)
