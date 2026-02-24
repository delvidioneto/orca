from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.db import transaction

User = get_user_model()


def has_superuser():
    """Verifica se existe pelo menos um superusuário no sistema"""
    return User.objects.filter(is_superuser=True).exists()


def home_redirect(request):
    """
    View de redirecionamento inicial.
    Verifica se existe superusuário e redireciona adequadamente.
    """
    # Se não existe superusuário, redireciona para setup
    if not has_superuser():
        return redirect('accounts:setup')
    
    # Se o usuário está autenticado, redireciona para dashboard
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    
    # Caso contrário, redireciona para login
    return redirect('accounts:login')


@require_http_methods(["GET", "POST"])
def setup_superuser(request):
    """
    View para cadastro do primeiro superusuário.
    Só permite acesso se não houver nenhum superusuário cadastrado.
    """
    # Se já existe um superusuário, redireciona para login
    if has_superuser():
        return redirect('accounts:login')
    
    # Se o usuário já está autenticado, redireciona para dashboard
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')
        
        # Validações
        errors = []
        
        if not username:
            errors.append('O nome de usuário é obrigatório.')
        elif len(username) < 3:
            errors.append('O nome de usuário deve ter pelo menos 3 caracteres.')
        elif User.objects.filter(username=username).exists():
            errors.append('Este nome de usuário já está em uso.')
        
        if not email:
            errors.append('O e-mail é obrigatório.')
        elif '@' not in email:
            errors.append('Por favor, insira um e-mail válido.')
        
        if not password:
            errors.append('A senha é obrigatória.')
        elif len(password) < 8:
            errors.append('A senha deve ter pelo menos 8 caracteres.')
        
        if password != password_confirm:
            errors.append('As senhas não coincidem.')
        
        if errors:
            return render(request, 'accounts/setup_superuser.html', {
                'errors': errors,
                'username': username,
                'email': email,
            })
        
        # Cria o superusuário
        try:
            with transaction.atomic():
                user = User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password
                )
                messages.success(request, f'Superusuário "{username}" criado com sucesso! Faça login para continuar.')
                return redirect('accounts:login')
        except Exception as e:
            return render(request, 'accounts/setup_superuser.html', {
                'errors': [f'Erro ao criar superusuário: {str(e)}'],
                'username': username,
                'email': email,
            })
    
    return render(request, 'accounts/setup_superuser.html')
