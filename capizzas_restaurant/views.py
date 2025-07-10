from django.views.generic import TemplateView
from django.shortcuts import render, redirect
from capizzas_restaurant.models import Pizza, Cliente, Compra
from django.shortcuts import render, get_object_or_404
from django.core.serializers.json import DjangoJSONEncoder
import json
from django.contrib import messages
from decimal import Decimal
from .forms import PizzaForm, ClienteForm, CompraForm
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate, login
from functools import wraps

class HomePageView(TemplateView):    
    template_name = 'base.html'    
    context_object_name = 'base'

class SobrePageView(TemplateView):
    template_name = 'sobre.html'
    context_object_name = 'sobre'

class LocalizacaoPageView(TemplateView):
    template_name = 'localizacao.html'
    context_object_name = 'localizacao'

class LoginPageView(TemplateView):
    template_name = 'login.html'
    context_object_name = 'login'


def Cardapio(request):
    pizzas = Pizza.objects.all()
    return render(request, 'cardapio.html', {'pizzas': pizzas})

def cadastro_pizza(request):
    if not request.user.is_superuser:
        return redirect('base')  # ou uma mensagem de erro

    if request.method == 'POST':
        form = PizzaForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('cadastropizza')
    else:
        form = PizzaForm()

    pizzas = Pizza.objects.all().order_by('nome')
    return render(request, 'cadastropizza_form.html', {'form': form, 'pizzas': pizzas})


def editar_pizza(request, id):
    pizza = get_object_or_404(Pizza, id=id)
    if request.method == 'POST':
        form = PizzaForm(request.POST, request.FILES, instance=pizza)
        if form.is_valid():
            form.save()
            return redirect('cadastropizza')
    else:
        form = PizzaForm(instance=pizza)
    pizzas = Pizza.objects.all()
    return render(request, 'cadastropizza_form.html', {'form': form, 'pizzas': pizzas})

def excluir_pizza(request, pizza_id):
    if not request.user.is_superuser:
        return redirect('cadastropizza')  # Protege para só admin excluir

    pizza = get_object_or_404(Pizza, id=pizza_id)
    pizza.delete()
    return redirect('cadastropizza')


        
def pedidopizza(request):
    pizzas = Pizza.objects.all().values('nome', 'ingredientes', 'preco')
    pizzas_json = json.dumps(list(pizzas), cls=DjangoJSONEncoder)
    return render(request, 'pedidopizza.html', {'pizzas_json': pizzas_json})

def HomeData(request):
    pizzas = Pizza.objects.all().values('nome', 'ingredientes', 'preco')
    context = {
        'pizzas_json': json.dumps(list(pizzas), cls=DjangoJSONEncoder)
    }
    return render(request, 'home.html', context)


def cadastro_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save(commit=False)
            cliente.senha = make_password(form.cleaned_data['senha'])  # <- Aqui criptografa a senha
            cliente.save()
            return redirect('login_cliente')  # redireciona para login após cadastro
    else:
        form = ClienteForm()
    
    return render(request, 'cadastrocliente_form.html', {'form': form})

def login_cliente(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        senha = request.POST.get('senha')

        user = authenticate(request, username=email, password=senha)
        if user is not None:
            login(request, user)
            return redirect('cardapio')  # Ou para onde você quiser
        else:
            messages.error(request, 'Email ou senha incorretos.')

    return render(request, 'login_cliente.html')

def logout_cliente(request):
    request.session.flush()  # Remove todas as variáveis de sessão
    return redirect('base')  # Ou para onde quiser redirecionar após o logout


def login_cliente_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f'/login_cliente/?next={request.path}')
        # Aqui você pode adicionar lógica para verificar se é cliente mesmo
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@login_cliente_required
def carrinho_view(request):
    cliente = request.user.cliente  # Assumindo que o cliente está logado
    pizzas = Pizza.objects.all()

    if request.method == 'POST':
        form = CompraForm(request.POST)
        if form.is_valid():
            compra = form.save(commit=False)
            compra.cliente = cliente
            preco1 = compra.pizza_1.preco
            preco2 = compra.pizza_2.preco if compra.pizza_2 else 0
            compra.preco_final = max(preco1, preco2)
            compra.save()
            return redirect('pagina_de_sucesso')
    else:
        form = CompraForm()

    return render(request, 'carrinho.html', {'form': form, 'pizzas': pizzas})