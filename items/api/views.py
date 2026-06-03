"""API views para itens e categorias."""
import datetime
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from items.models import Item, Categoria


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


@api_view(["GET"])
@permission_classes([AllowAny])
def api_items(request):
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

    return Response({"ok": True, "results": [_item_to_dict(i, request) for i in items_page], "page": page, "has_more": has_more})


@api_view(["GET"])
@permission_classes([AllowAny])
def api_item_detail(request, item_id):
    try:
        item = Item.objects.select_related("usuario", "categoria").get(id=item_id)
    except Item.DoesNotExist:
        return Response({"ok": False, "detail": "Item não encontrado."}, status=404)
    return Response({"ok": True, "data": _item_to_dict(item, request)})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_create_item(request):
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
    item = get_object_or_404(Item, id=item_id, usuario=request.user)
    item.delete()
    return Response({"ok": True, "detail": "Item deletado com sucesso."})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_change_item_status(request, item_id):
    item = get_object_or_404(Item, id=item_id, usuario=request.user)
    novo_status = (request.data.get("status") or "").strip().lower()
    if novo_status not in ["perdido", "achado", "devolvido"]:
        return Response({"ok": False, "detail": "Status inválido."}, status=400)
    item.status = novo_status
    item.save(update_fields=["status", "atualizado_em"])
    return Response({"ok": True, "data": _item_to_dict(item, request)})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def api_my_items(request):
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
    return Response({"ok": True, "results": [_item_to_dict(i, request) for i in items_page], "page": page, "has_more": has_more})


@api_view(["GET"])
@permission_classes([AllowAny])
def api_stats(request):
    total = Item.objects.count()
    return Response({"ok": True, "data": {
        "total": total,
        "perdidos": Item.objects.filter(status="perdido").count(),
        "encontrados": Item.objects.filter(status="achado").count(),
        "devolvidos": Item.objects.filter(status="devolvido").count(),
    }})


@api_view(["GET"])
@permission_classes([AllowAny])
def api_categories(request):
    cats = Categoria.objects.all().values("id", "nome")
    return Response({"ok": True, "results": list(cats)})
