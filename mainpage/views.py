from datetime import date

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import ProfileupdateForm
from .models import Categoria, Item, Profile, Chat, Mensagem


def home(request):
    return render(request, "mainpage/index.html")


def login_view(request):
    if request.method == "POST":
        email_or_username = request.POST.get("username")
        password = request.POST.get("password")

        # tenta achar usuário pelo email
        try:
            user_obj = User.objects.get(email=email_or_username)
            username = user_obj.username
        except User.DoesNotExist:
            username = email_or_username

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f"Bem-vindo, {user.username}!")
            return redirect("menu")
        else:
            messages.error(request, "Usuário, e-mail ou senha incorretos.")

    return render(request, "mainpage/login.html")


def logout_view(request):
    logout(request)
    messages.info(request, "Você saiu da conta.")
    return redirect("login")


def register_view(request):
    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        data_nascimento = request.POST.get("data_nascimento")
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        # valida data + idade mínima
        dn_value = None
        if data_nascimento:
            try:
                dn_value = date.fromisoformat(data_nascimento)
            except ValueError:
                messages.error(request, "Data de nascimento inválida.")
                return redirect("register")

            hoje = date.today()
            if dn_value > hoje:
                messages.error(request, "Data de nascimento inválida.")
                return redirect("register")

            idade = hoje.year - dn_value.year - (
                (hoje.month, hoje.day) < (dn_value.month, dn_value.day)
            )
            if idade < 13:
                messages.error(request, "Você precisa ter pelo menos 13 anos para criar uma conta.")
                return redirect("register")

        # valida senha
        if password != confirm_password:
            messages.error(request, "As senhas não coincidem.")
            return redirect("register")

        # valida username
        if User.objects.filter(username=username).exists():
            messages.error(request, "Nome de usuário já existe.")
            return redirect("register")

        # cria usuário
        name_parts = full_name.split(" ", 1)
        first_name = name_parts[0] if name_parts else ""
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        # ✅ SE VOCÊ TEM SIGNAL: não crie Profile aqui
        # só atualize o que precisa
        try:
            profile = user.profile
        except Profile.DoesNotExist:
            # fallback caso o signal não esteja carregando
            profile = Profile.objects.create(user=user)

        if dn_value:
            profile.data_nascimento = dn_value
            profile.save(update_fields=["data_nascimento"])

        messages.success(request, "Conta criada com sucesso! Faça login.")
        return redirect("login")

    return render(request, "mainpage/register.html")


@login_required(login_url="login")
def menu_view(request):
    categorias = Categoria.objects.all()

    q = (request.GET.get("q") or "").strip()
    status = (request.GET.get("status") or "todos").strip()
    categoria = (request.GET.get("categoria") or "todas").strip()

    itens = Item.objects.all().order_by("-id")

    # busca
    if q:
        itens = itens.filter(
            Q(titulo__icontains=q) |
            Q(descricao__icontains=q) |
            Q(local__icontains=q)
        )

    # status
    if status in ["perdido", "achado"]:
        itens = itens.filter(status=status)

    # categoria
    if categoria.isdigit():
        itens = itens.filter(categoria_id=int(categoria))

    # contadores (sempre do sistema inteiro)
    total_itens = Item.objects.all().count()
    perdidos = Item.objects.filter(status="perdido").count()
    encontrados = Item.objects.filter(status="achado").count()

    return render(request, "mainpage/menu.html", {
        "categorias": categorias,
        "itens": itens,
        "total_itens": total_itens,
        "perdidos": perdidos,
        "encontrados": encontrados,
        "correspondencias": 0,
        "q": q,
        "status": status,
        "categoria": categoria,
    })


@login_required(login_url="login")
def screen_user(request):
    user = request.user
    itens = Item.objects.filter(usuario=user).order_by("-id")
    categorias = Categoria.objects.all()

    context = {
        "nome": user.get_full_name() or user.username,
        "email": user.email,
        "itens": itens,
        "total": itens.count(),
        "perdidos": itens.filter(status="perdido").count(),
        "encontrados": itens.filter(status="achado").count(),
        "categorias": categorias,
    }
    return render(request, "mainpage/user.html", context)


@login_required(login_url="login")
def register_item(request):
    user = request.user
    next_url = request.GET.get("next") or "screen_user"

    if request.method != "POST":
        return redirect(next_url)

    titulo = (request.POST.get("titulo") or "").strip()
    descricao = request.POST.get("descricao")
    categoria_id = request.POST.get("categoria")
    status = request.POST.get("status")
    data_item = request.POST.get("data")
    local = request.POST.get("local")
    imagem = request.FILES.get("imagem")

    if not titulo or len(titulo) < 3:
        messages.error(request, "O nome do item é obrigatório e deve ter pelo menos 3 caracteres.")
        return redirect(next_url)

    categoria = Categoria.objects.filter(id=categoria_id).first() if categoria_id else None

    Item.objects.create(
        titulo=titulo,
        descricao=descricao,
        categoria=categoria,
        status=status,
        usuario=user,
        data=data_item,
        local=local,
        imagem=imagem,
    )

    messages.success(request, "Item cadastrado com sucesso!")
    return redirect(next_url)


@login_required(login_url="login")
def edit_item(request, id):
    item = get_object_or_404(Item, id=id, usuario=request.user)
    categorias = Categoria.objects.all()

    next_url = request.GET.get("next") or reverse("screen_user")

    if request.method == "POST":
        item.titulo = request.POST.get("titulo", item.titulo)
        item.descricao = request.POST.get("descricao", item.descricao)
        item.local = request.POST.get("local", item.local)
        item.status = request.POST.get("status", item.status)
        item.data = request.POST.get("data", item.data)

        categoria_id = request.POST.get("categoria")
        if categoria_id:
            item.categoria_id = categoria_id

        if request.FILES.get("imagem"):
            item.imagem = request.FILES.get("imagem")

        item.save()
        messages.success(request, "Item atualizado com sucesso!")
        return redirect(next_url)

    return render(request, "mainpage/item_edit.html", {
        "item": item,
        "categorias": categorias,
        "next": next_url,
    })


@login_required(login_url="login")
def delete_item(request, id):
    item = get_object_or_404(Item, id=id, usuario=request.user)
    next_url = request.GET.get("next") or "screen_user"

    if request.method == "POST":
        item.delete()
        messages.success(request, "Item deletado com sucesso!")
        return redirect(next_url)

    return render(request, "mainpage/item_confirm_delete.html", {
        "item": item,
        "next": next_url,
    })


@login_required(login_url="login")
def list_item(request):
    categorias = Categoria.objects.all()

    q = (request.GET.get("q") or "").strip()
    status = (request.GET.get("status") or "todos").strip()
    categoria = (request.GET.get("categoria") or "todas").strip()
    page = int(request.GET.get("page", 1))

    itens = Item.objects.all().order_by("-id")

    if q:
        itens = itens.filter(
            Q(titulo__icontains=q) |
            Q(descricao__icontains=q) |
            Q(local__icontains=q)
        )

    if status in ["perdido", "achado"]:
        itens = itens.filter(status=status)

    if categoria.isdigit():
        itens = itens.filter(categoria_id=int(categoria))

    per_page = 8
    start = (page - 1) * per_page
    end = start + per_page
    itens_list = list(itens[start:end + 1])
    has_more = len(itens_list) > per_page
    itens_page = itens_list[:per_page]

    total_itens = Item.objects.all().count()
    perdidos = Item.objects.filter(status="perdido").count()
    encontrados = Item.objects.filter(status="achado").count()

    return render(request, "mainpage/item_list.html", {
        "categorias": categorias,
        "itens": itens_page,
        "total_itens": total_itens,
        "perdidos": perdidos,
        "encontrados": encontrados,
        "q": q,
        "status": status,
        "categoria": categoria,
        "has_more": has_more,
        "next_page": page + 1,
    })


@login_required
def upload_photo(request):
    if request.method == "POST":
        profile, _ = Profile.objects.get_or_create(user=request.user)

        form = ProfileupdateForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Foto atualizada com sucesso!")
        else:
            messages.error(request, "Erro ao processar a imagem.")

    return redirect("screen_user")


@login_required
def update_profile(request):
    if request.method == "POST":
        user = request.user
        profile, _ = Profile.objects.get_or_create(user=user)

        nome = request.POST.get("nome")
        if nome:
            user.first_name = nome
            user.save(update_fields=["first_name"])

        profile.telefone = request.POST.get("telefone")
        profile.cidade = request.POST.get("cidade")
        profile.estado = request.POST.get("estado")
        profile.cep = request.POST.get("cep")

        if request.FILES.get("image"):
            profile.image = request.FILES.get("image")

        profile.save()
        messages.success(request, "Perfil atualizado com sucesso!")
        return redirect("screen_user")

    return redirect("screen_user")


def item_detail(request, slug):
    item = get_object_or_404(Item, slug=slug)
    next_url = request.GET.get("next") or ""
    return render(request, "mainpage/item_detail.html", {
        "item": item,
        "next": next_url,
    })


@login_required(login_url="login")
def view_item(request, id):
    item = get_object_or_404(Item, id=id)
    next_url = request.GET.get("next") or "menu"
    return render(request, "mainpage/item_detail.html", {
        "item": item,
        "next": next_url,
    })


def _usuario_participa(chat, user):
    return user.id in (chat.criado_por_id, chat.dono_item_id)


@login_required(login_url='login')
def chat_start(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    next_url = request.GET.get('next') or reverse('item_detail', kwargs={'slug': item.slug})

    # não deixa criar chat consigo mesmo
    if item.usuario_id == request.user.id:
        messages.error(request, "Você não pode iniciar um chat com você mesmo.")
        return redirect(next_url)

    chat, _ = Chat.objects.get_or_create(
        item=item,
        criado_por=request.user,
        dono_item=item.usuario,
        defaults={'status': 'ativo'}
    )

    # se existir fechado e você quiser reabrir ao iniciar:
    if chat.status != 'ativo':
        chat.status = 'ativo'
        chat.save(update_fields=['status'])

    return redirect('chat_detail', chat_id=chat.id)


@login_required(login_url="login")
def chats_list(request):
    chats = (
        Chat.objects
        .filter(Q(criado_por=request.user) | Q(dono_item=request.user))
        .select_related("item", "criado_por", "dono_item")
        .order_by("-atualizado_em", "-criado_em")
    )
    return render(request, "mainpage/chats_list.html", {"chats": chats})


@login_required(login_url="login")
def chat_detail(request, chat_id):
    chat = get_object_or_404(
        Chat.objects.select_related("item", "criado_por", "dono_item"),
        id=chat_id,
    )

    if not _usuario_participa(chat, request.user):
        messages.error(request, "Você não tem acesso a esse chat.")
        return redirect("chats_list")

    chat.mensagens.filter(lida=False).exclude(remetente=request.user).update(lida=True)

    mensagens = chat.mensagens.select_related("remetente").order_by("data_envio")

    return render(request, "mainpage/chat_detail.html", {
        "chat": chat,
        "mensagens": mensagens,
    })


@login_required(login_url="login")
@require_POST
def chat_send_message(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)

    if not _usuario_participa(chat, request.user):
        messages.error(request, "Você não tem acesso a esse chat.")
        return redirect("chats_list")

    if chat.status != "ativo":
        messages.error(request, "Esse chat está fechado.")
        return redirect("chat_detail", chat_id=chat.id)

    conteudo = (request.POST.get("conteudo") or "").strip()
    if not conteudo:
        messages.error(request, "Digite uma mensagem.")
        return redirect("chat_detail", chat_id=chat.id)

    Mensagem.objects.create(
        chat=chat,
        remetente=request.user,
        conteudo=conteudo,
        tipo="texto",
        lida=False,
    )

    chat.atualizado_em = timezone.now()
    chat.save(update_fields=["atualizado_em"])

    return redirect("chat_detail", chat_id=chat.id)


@login_required(login_url="login")
@require_POST
def chat_close(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)

    if not _usuario_participa(chat, request.user):
        messages.error(request, "Você não tem acesso a esse chat.")
        return redirect("chats_list")

    if request.user.id != chat.dono_item_id:
        messages.error(request, "Apenas o dono do item pode fechar o chat.")
        return redirect("chat_detail", chat_id=chat.id)

    chat.status = "fechado"
    chat.save(update_fields=["status"])

    messages.info(request, "Chat fechado.")
    return redirect("chat_detail", chat_id=chat.id)

@login_required(login_url="login")
def items_perdidos(request):
    categorias = Categoria.objects.all()

    q = (request.GET.get("q") or "").strip()
    categoria = (request.GET.get("categoria") or "todas").strip()
    page = int(request.GET.get("page", 1))

    itens = Item.objects.filter(status="perdido").order_by("-id")

    if q:
        itens = itens.filter(
            Q(titulo__icontains=q) |
            Q(descricao__icontains=q) |
            Q(local__icontains=q)
        )

    if categoria.isdigit():
        itens = itens.filter(categoria_id=int(categoria))

    per_page = 8
    start = (page - 1) * per_page
    end = start + per_page
    itens_list = list(itens[start:end + 1])
    has_more = len(itens_list) > per_page
    itens_page = itens_list[:per_page]

    total_itens = Item.objects.all().count()
    perdidos = Item.objects.filter(status="perdido").count()
    encontrados = Item.objects.filter(status="achado").count()

    return render(request, "mainpage/item_list.html", {
        "categorias": categorias,
        "itens": itens_page,
        "total_itens": total_itens,
        "perdidos": perdidos,
        "encontrados": encontrados,
        "q": q,
        "status": "perdido",
        "categoria": categoria,
        "page_title": "Itens Perdidos",
        "has_more": has_more,
        "next_page": page + 1,
    })


@login_required(login_url="login")
def items_encontrados(request):
    categorias = Categoria.objects.all()

    q = (request.GET.get("q") or "").strip()
    categoria = (request.GET.get("categoria") or "todas").strip()
    page = int(request.GET.get("page", 1))

    itens = Item.objects.filter(status="achado").order_by("-id")

    if q:
        itens = itens.filter(
            Q(titulo__icontains=q) |
            Q(descricao__icontains=q) |
            Q(local__icontains=q)
        )

    if categoria.isdigit():
        itens = itens.filter(categoria_id=int(categoria))

    per_page = 8
    start = (page - 1) * per_page
    end = start + per_page
    itens_list = list(itens[start:end + 1])
    has_more = len(itens_list) > per_page
    itens_page = itens_list[:per_page]

    total_itens = Item.objects.all().count()
    perdidos = Item.objects.filter(status="perdido").count()
    encontrados = Item.objects.filter(status="achado").count()

    return render(request, "mainpage/item_list.html", {
        "categorias": categorias,
        "itens": itens_page,
        "total_itens": total_itens,
        "perdidos": perdidos,
        "encontrados": encontrados,
        "q": q,
        "status": "achado",
        "categoria": categoria,
        "page_title": "Itens Encontrados",
        "has_more": has_more,
        "next_page": page + 1,
    })

