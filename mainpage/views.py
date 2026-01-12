from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required

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

def register_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password != confirm_password:
            messages.error(request, 'As senhas não coincidem.')
            return redirect('register')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Nome de usuário já existe.')
            return redirect('register')
        
        user = User.objects.create_user(username=username, email=email, password=password)
        messages.success(request, 'Conta criada com sucesso! Faça login.')

        return redirect('login')
    return render(request, 'mainpage/register.html')

@login_required(login_url='login')
def menu_view(request):
    return render(request, 'mainpage/menu.html')

@login_required(login_url='login')
def tela_usuario(request):
    user = request.user

    context = {
        'nome': user.get_full_name() or user.username,
        'email': user.email,
        'data_cadastro': user.date_joined,
    }

    return render(request, 'mainpage/tela_usuario.html', context)

@login_required(login_url='login')
def cadastrar_item(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        descricao = request.POST.get('descricao')

        if not nome:
            messages.error(request, 'O nome do item é obrigatório.')
            return redirect('cadastrar_item')

        # Aqui depois você pode salvar no banco (model)
        messages.success(request, 'Item cadastrado com sucesso!')

        return redirect('menu')

    return render(request, 'mainpage/cadastrar_item.html')