"""API views para autenticação e perfil de usuário."""
import json
from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import Profile


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
    """Atualiza o perfil do usuário autenticado com suporte a tamanho de foto."""
    user = request.user
    profile, _ = Profile.objects.get_or_create(user=user)
    data = request.data

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

    if "telefone" in data:
        profile.telefone = data["telefone"]
    if "cidade" in data:
        profile.cidade = data["cidade"]
    if "estado" in data:
        profile.estado = data["estado"]
    if "cep" in data:
        profile.cep = data["cep"]
    if "data_nascimento" in data:
        raw = (data["data_nascimento"] or "").strip()
        if raw:
            try:
                from datetime import date as _date
                profile.data_nascimento = _date.fromisoformat(raw)
            except (ValueError, TypeError):
                return Response(
                    {"ok": False, "detail": "Formato de data inválido. Use AAAA-MM-DD."},
                    status=400,
                )
        else:
            profile.data_nascimento = None

    nova_foto = request.FILES.get("image")
    if nova_foto:
        profile.image = nova_foto
    profile.save()

    tamanho = (data.get("tamanho") or "medio").strip().lower()
    if nova_foto or "tamanho" in data:
        profile.redimensionar(tamanho)

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
    """Redimensiona a foto de perfil existente."""
    user = request.user
    profile, _ = Profile.objects.get_or_create(user=user)

    if not profile.image or profile.image.name == 'profile_pics/user.png':
        return Response({"ok": False, "detail": "Nenhuma foto de perfil para redimensionar."}, status=400)

    tamanho = (request.data.get("tamanho") or "medio").strip().lower()
    if tamanho not in Profile.TAMANHOS_VALIDOS:
        return Response({"ok": False, "detail": f"Tamanho inválido. Use: {', '.join(Profile.TAMANHOS_VALIDOS.keys())}"}, status=400)

    profile.redimensionar(tamanho)
    foto_url = None
    try:
        foto_url = request.build_absolute_uri(profile.image.url)
    except Exception:
        pass

    return Response({"ok": True, "detail": f"Foto redimensionada para '{tamanho}'.", "data": {"foto": foto_url, "tamanho_aplicado": tamanho}})


@api_view(["GET"])
@permission_classes([AllowAny])
def api_photo_sizes(request):
    """Retorna os tamanhos de foto de perfil disponíveis."""
    return Response({
        "ok": True,
        "data": {nome: {"label": nome.capitalize(), "pixels": px} for nome, px in Profile.TAMANHOS_VALIDOS.items()}
    })
