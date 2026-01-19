from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Profile, Item, Categoria
from .forms import ProfileupdateForm
from datetime import date

def home(request):
    return render(request, 'mainpage/index.html')

def login_view(request):
    if request.method == 'POST':
        email_or_username = request.POST.get('username')
        password = request.POST.get('password')

        # Tenta achar usuário pelo email
        try:
            user_obj = User.objects.get(email=email_or_username)
            username = user_obj.username
        except User.DoesNotExist:
            # Se não achar email, tenta usar o texto como username mesmo
            username = email_or_username

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'Bem-vindo, {user.username}!')
            return redirect('menu')
        else:
            messages.error(request, 'Usuário, e-mail ou senha incorretos.')

    return render(request, 'mainpage/login.html')

def logout_view(request):
    logout(request)
    messages.info(request, 'Você saiu da conta.')
    return redirect('login')
from datetime import date

def register_view(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        data_nascimento = request.POST.get('data_nascimento')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # 🔒 VALIDAÇÃO DA DATA + IDADE (AQUI 👇)
        if data_nascimento:
            data_nascimento = date.fromisoformat(data_nascimento)
            hoje = date.today()

            # não pode ser futura
            if data_nascimento > hoje:
                messages.error(request, 'Data de nascimento inválida.')
                return redirect('register')

            # idade mínima
            idade = hoje.year - data_nascimento.year - (
                (hoje.month, hoje.day) <
                (data_nascimento.month, data_nascimento.day)
            )

            if idade < 13:
                messages.error(
                    request,
                    'Você precisa ter pelo menos 13 anos para criar uma conta.'
                )
                return redirect('register')

        # senha
        if password != confirm_password:
            messages.error(request, 'As senhas não coincidem.')
            return redirect('register')

        # username
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Nome de usuário já existe.')
            return redirect('register')

        # nome completo
        name_parts = full_name.strip().split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''

        # 🚀 só cria a conta se passou em TODAS as validações
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        Profile.objects.create(
            user=user,
            data_nascimento=data_nascimento
        )

        messages.success(request, 'Conta criada com sucesso! Faça login.')
        return redirect('login')

        return render(request, 'mainpage/register.html')

        # valida senha
        if password != confirm_password:
            messages.error(request, 'As senhas não coincidem.')
            return redirect('register')

        # valida username
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Nome de usuário já existe.')
            return redirect('register')

        # trata nome completo
        name_parts = full_name.strip().split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''

        # 🚀 SÓ CRIA O USUÁRIO DEPOIS DE VALIDAR TUDO
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        # cria o profile
        Profile.objects.create(
            user=user,
            data_nascimento=data_nascimento
        )

        messages.success(request, 'Conta criada com sucesso! Faça login.')
        return redirect('login')

    return render(request, 'mainpage/register.html')

@login_required(login_url='login')
def menu_view(request):
    categorias = Categoria.objects.all()
    itens = Item.objects.all().order_by('-id')
    
    return render(request, 'mainpage/menu.html', {
        'categorias': categorias,
        'itens': itens,
    })

@login_required(login_url='login')
def screen_user(request):
    user = request.user

    # queryset COMPLETO (sem slice)
    itens = Item.objects.filter(usuario=user).order_by('-id')

    categorias = Categoria.objects.all()

    context = {
        'nome': user.get_full_name() or user.username,
        'email': user.email,
        'itens': itens,  # passa TODOS
        'total': itens.count(),
        'perdidos': itens.filter(status='perdido').count(),
        'encontrados': itens.filter(status='achado').count(),
        'categorias': categorias,
    }

    return render(request, 'mainpage/user.html', context)


@login_required(login_url='login')
def register_item(request):
    categorias = Categoria.objects.all()
    user = request.user

    if request.method == 'POST':
        titulo = request.POST.get('titulo')  # corrigido
        descricao = request.POST.get('descricao')
        categoria_id = request.POST.get('categoria')
        status = request.POST.get('status')
        data = request.POST.get('data')
        local = request.POST.get('local')
        imagem = request.FILES.get('imagem')

        if not titulo or len(titulo) < 3:
            messages.error(request, 'O nome do item é obrigatório e deve ter pelo menos 3 caracteres.')
            return render(request, 'mainpage/user.html', {
                'categorias': categorias,
                'itens': Item.objects.filter(usuario=user)
            })

        categoria = Categoria.objects.get(id=categoria_id) if categoria_id else None

        Item.objects.create(
            titulo=titulo,
            descricao=descricao,
            categoria=categoria,
            status=status,
            usuario=user,
            data=data,
            local=local,
            imagem=imagem
        )

        messages.success(request, 'Item cadastrado com sucesso!')
        return redirect('screen_user')

    return render(request, 'mainpage/user.html', {
        'categorias': categorias,
        'itens': Item.objects.filter(usuario=user)
    })

@login_required(login_url='login')
def edit_item(request, id):
    item = get_object_or_404(Item, id=id, usuario=request.user)
    categorias = Categoria.objects.all()

    if request.method == 'POST':
        item.titulo = request.POST.get('titulo')
        item.descricao = request.POST.get('descricao')
        item.status = request.POST.get('status')
        item.local = request.POST.get('local')
        item.data = request.POST.get('data')

        categoria_id = request.POST.get('categoria')
        item.categoria = Categoria.objects.get(id=categoria_id) if categoria_id else None

        if request.FILES.get('imagem'):
            item.imagem = request.FILES.get('imagem')

        item.save()
        messages.success(request, 'Item atualizado com sucesso!')
        return redirect('screen_user')

    return render(request, 'mainpage/item_edit.html', {
        'item': item,
        'categorias': categorias
    })

@login_required(login_url='login')
def delete_item(request, id):
    item = get_object_or_404(Item, id=id, usuario=request.user)

    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Item deletado com sucesso!')
        return redirect('screen_user')

    return render(request, 'mainpage/item_confirm_delete.html', {
        'item': item
    })

@login_required(login_url='login')
def list_item(request):
    itens = Item.objects.all()
    return render(request, 'mainpage/item_list.html', {
        'itens': itens
    })


@login_required
def upload_photo(request):
    if request.method == 'POST':
        # Garante que o perfil existe para o usuário logado
        profile, created = Profile.objects.get_or_create(user=request.user)
        
        form = ProfileupdateForm(request.POST, request.FILES, instance=profile)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Foto atualizada com sucesso!')
            print("LOG: Foto salva com sucesso no banco!")
            return redirect('screen_user')
        else:
            # Se o formulário tiver erro, ele vai aparecer no seu terminal (janela preta)
            print(f"LOG ERRO: {form.errors}")
            messages.error(request, 'Erro ao processar a imagem.')
            
    return redirect('screen_user') 

@login_required
def update_profile(request):
    if request.method == 'POST':
        user = request.user
        
        # Pega os dados do formulário HTML
        nome = request.POST.get('nome')
        # O e-mail não pegamos porque ele é readonly, então não vamos mexer nele
        telefone = request.POST.get('telefone')
        imagem = request.FILES.get('image')

        # 1. Atualiza o Nome no model User
        if nome:
            user.first_name = nome
            user.save()

        # 2. Atualiza Telefone e Imagem no model Profile
        # Nota: Certifique-se que o campo 'telefone' existe no seu model Profile
        profile = user.profile 
        if telefone:
            profile.telefone = telefone
        if imagem:
            profile.image = imagem
        profile.save()
        
        profile.cidade = request.POST.get('cidade')
        profile.estado = request.POST.get('estado')
        profile.save()

        messages.success(request, "Perfil atualizado com sucesso!")
        return redirect('screen_user') # Nome exato que está no seu urls.py

    return redirect('screen_user')

def item_detail(request, id):
    item = get_object_or_404(Item, id=id)
    return render(request, 'mainpage/item_detail.html', {
        'item': item
    })