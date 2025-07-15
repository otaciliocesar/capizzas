from django.views.generic import TemplateView
from django.shortcuts import render, redirect, get_object_or_404
from capizzas_restaurant.models import Pizza, Compra, Bebida, CompraBebida
from django.core.serializers.json import DjangoJSONEncoder
import json
from django.contrib import messages
from decimal import Decimal
from .forms import PizzaForm, ClienteForm, CompraForm, BebidaForm, PromocaoForm
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate, login
from functools import wraps
from django.views.decorators.http import require_http_methods, require_POST
from django.template.loader import render_to_string
from django.db import transaction
from .models import Promocao
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.shortcuts import render, redirect
from django.contrib import messages
from utils.email import enviar_email
  

class SobrePageView(TemplateView):
    template_name = 'sobre.html'
    context_object_name = 'sobre'

class LocalizacaoPageView(TemplateView):
    template_name = 'localizacao.html'
    context_object_name = 'localizacao'

class LoginPageView(TemplateView):
    template_name = 'login.html'
    context_object_name = 'login'

def Home_View(request):
    promocoes = Promocao.objects.filter(ativa=True)
    return render(request, 'home.html', {'promocoes': promocoes})

def Cardapio(request):
    pizzas = Pizza.objects.all()
    return render(request, 'cardapio.html', {'pizzas': pizzas})


def cadastro_pizza(request):
    if not request.user.is_superuser:
        return redirect('base')  # ou uma mensagem de erro

    # Form pizza
    if request.method == 'POST' and 'nome' in request.POST and 'ingredientes' in request.POST:
        form = PizzaForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('cadastropizza')
    else:
        form = PizzaForm()

    # Form bebida (não submete aqui)
    bebida_form = BebidaForm()

    pizzas = Pizza.objects.all().order_by('nome')
    bebidas = Bebida.objects.all().order_by('nome')

    context = {
        'form': form,
        'bebida_form': bebida_form,
        'pizzas': pizzas,
        'bebidas': bebidas,
    }
    return render(request, 'cadastropizza_form.html', context)


def cadastrar_bebida(request):
    if not request.user.is_superuser:
        return redirect('base')

    if request.method == 'POST':
        form = BebidaForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('cadastropizza')
    return redirect('cadastropizza')


def editar_bebida(request, id):
    if not request.user.is_superuser:
        return redirect('base')

    bebida = get_object_or_404(Bebida, id=id)
    if request.method == 'POST':
        form = BebidaForm(request.POST, request.FILES, instance=bebida)
        if form.is_valid():
            form.save()
            return redirect('cadastropizza')
    else:
        form = BebidaForm(instance=bebida)
    return render(request, 'editar_bebida.html', {'form': form})


def excluir_bebida(request, id):
    if not request.user.is_superuser:
        return redirect('base')

    bebida = get_object_or_404(Bebida, id=id)
    bebida.delete()
    return redirect('cadastropizza')


def editar_pizza(request, id):
    if not request.user.is_superuser:
        return redirect('base')

    pizza = get_object_or_404(Pizza, id=id)
    if request.method == 'POST':
        form = PizzaForm(request.POST, request.FILES, instance=pizza)
        if form.is_valid():
            form.save()
            return redirect('cadastropizza')
    else:
        form = PizzaForm(instance=pizza)
    pizzas = Pizza.objects.all()
    bebidas = Bebida.objects.all()
    return render(request, 'cadastropizza_form.html', {'form': form, 'pizzas': pizzas, 'bebidas': bebidas})


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
            return redirect('login')  # redireciona para login após cadastro
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

    return render(request, 'login.html')


def logout_cliente(request):
    request.session.flush()  # Remove todas as variáveis de sessão
    return redirect('base')  # Ou para onde quiser redirecionar após o logout


def login_cliente_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f'/login/?next={request.path}')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


@login_cliente_required
def carrinho_view(request):
    cliente = request.user.cliente  # Assumindo que o cliente está logado
    pizzas = Pizza.objects.all()
    bebidas = Bebida.objects.all()  # <-- Adicionado

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

    return render(request, 'carrinho.html', {
        'form': form,
        'pizzas': pizzas,
        'bebidas': bebidas  # <-- Adicionado no contexto
    })


@login_cliente_required
@require_http_methods(["GET", "POST"])
def checkout_view(request):
    if request.method == 'POST':
        carrinho_json = request.POST.get("pedido_final")
        if not carrinho_json:
            messages.error(request, "Carrinho vazio ou inválido.")
            return redirect("carrinho")

        try:
            carrinho = json.loads(carrinho_json)
            request.session["carrinho"] = carrinho  # Salva na sessão

            cliente = request.user.cliente
            total = sum(float(item["total"]) for item in carrinho)

            # Montar HTML simples do email:
            itens_html = "".join([
                f"<li>🍕 {item['pizza1']['nome']}" +
                (f" + {item['pizza2']['nome']}" if item.get('pizza2') else "") +
                f" — <strong>R$ {item['total']}</strong></li>"
                if item['tipo'] == 'pizza' else
                f"<li>🥤 {item['bebida']['nome']} x {item['quantidade']} — <strong>R$ {item['total']}</strong></li>"
                for item in carrinho
            ])

            html_email = f"""
                <h2>🍕 Confirmação de Pedido - Capizzas</h2>
                <p>Olá {cliente.nome},</p>
                <p>Recebemos seu pedido com sucesso! Aqui está o resumo:</p>
                <ul>{itens_html}</ul>
                <p><strong>Total do pedido:</strong> R$ {total:.2f}</p>
                <p>🛵 Em breve estaremos chegando com sua pizza quente e saborosa!</p>
                <hr>
                <p>📍 Endereço de entrega: {cliente.endereco_entrega}, Nº {cliente.numero}</p>
                <p>📧 E-mail: {cliente.email}</p>
            """

            assunto = "🍕 Capizzas - Confirmação do Pedido"
            destinatario = request.user.email
            texto = f"Olá {cliente.nome}, recebemos seu pedido! Total: R$ {total:.2f}"


            messages.success(request, "Pedido confirmado! Confirmação enviada por e-mail.")
            return redirect("checkout")  # Ou para outra página após confirmação

        except json.JSONDecodeError:
            messages.error(request, "Erro ao processar o carrinho.")
            return redirect("carrinho")

    carrinho = request.session.get("carrinho", [])
    return render(request, "checkout.html", {"carrinho": carrinho})





@login_cliente_required
@require_POST
def finalizar_pedido(request):
    print("📬 View finalizar_pedido foi chamada")

    cliente = request.user.cliente
    carrinho_str = request.POST.get('pedido_final', '[]')

    try:
        carrinho = json.loads(carrinho_str)
    except json.JSONDecodeError as e:
        print(f"❌ Erro de JSON: {e}")
        messages.error(request, "Erro no formato do pedido. Tente novamente.")
        return redirect('checkout')

    try:
        with transaction.atomic():
            for item in carrinho:
                if item['tipo'] == 'pizza':
                    pizza1_id = item['pizza1']['id']
                    pizza2_id = item['pizza2']['id'] if item.get('pizza2') else None
                    preco_final = float(item['total'])

                    compra = Compra.objects.create(
                        cliente=cliente,
                        pizza_1_id=pizza1_id,
                        pizza_2_id=pizza2_id,
                        preco_final=preco_final,
                        quantidade=1
                    )

                elif item['tipo'] == 'bebida':
                    bebida_id = item['bebida']['id']
                    quantidade = item['quantidade']

                    compra = Compra.objects.create(
                        cliente=cliente,
                        pizza_1=Pizza.objects.first(),  # Dummy temporário
                        preco_final=float(item['total']),
                        quantidade=1
                    )
                    CompraBebida.objects.create(
                        compra=compra,
                        bebida_id=bebida_id,
                        quantidade=quantidade
                    )

        # Enviar e-mail
        from utils.email import enviar_email

        itens_html = "".join([
            f"<li>🍕 {item['pizza1']['nome']}" +
            (f" + {item['pizza2']['nome']}" if item.get('pizza2') else "") +
            f" — <strong>R$ {item['total']}</strong></li>"
            if item['tipo'] == 'pizza' else
            f"<li>🥤 {item['bebida']['nome']} x {item['quantidade']} — <strong>R$ {item['total']}</strong></li>"
            for item in carrinho
        ])
        total = sum(float(item["total"]) for item in carrinho)

        html_email = f"""
            <h2>🍕 Confirmação de Pedido - Capizzas</h2>
            <p>Olá {cliente.nome},</p>
            <p>Recebemos seu pedido com sucesso! Aqui está o resumo:</p>
            <ul>{itens_html}</ul>
            <p><strong>Total do pedido:</strong> R$ {total:.2f}</p>
            <p>🛵 Em breve estaremos chegando com sua pizza quente e saborosa!</p>
            <hr>
            <p>📍 Endereço de entrega: {cliente.endereco_entrega}, Nº {cliente.numero}</p>
            <p>📧 E-mail: {cliente.email}</p>
        """
        assunto = "🍕 Capizzas - Confirmação do Pedido"
        texto = f"Olá {cliente.nome}, recebemos seu pedido! Total: R$ {total:.2f}"
        destinatario = cliente.email

        enviar_email(destinatario, assunto, texto, html_email)
        enviar_email("contato@capizzas.com", "[Cópia Interna] " + assunto, texto, html_email)

        messages.success(request, "Pedido finalizado com sucesso! Confirmação enviada por e-mail.")
        return redirect('cardapio')

    except Exception as e:
        print(f"❌ Erro ao finalizar pedido: {e}")
        messages.error(request, "Erro ao finalizar pedido.")
        return redirect('checkout')

    

@login_cliente_required
def gerenciar_promocoes(request):
    if not request.user.is_superuser:
        return redirect('base')

    if request.method == 'POST':
        form = PromocaoForm(request.POST, request.FILES)
        if form.is_valid():
            promocao = form.save(commit=False)
            promocao.save()
            form.save_m2m()  # Agora funciona corretamente!
            return redirect('cadastropromocoes')
    else:
        form = PromocaoForm()

    promocoes = Promocao.objects.filter(ativa=True)  # Exibe apenas promoções ativas
    return render(request, 'cadastropromocoes_form.html', {
        'form': form,
        'promocoes': promocoes
    })

@login_cliente_required
def pedido_promocao(request, slug):
    promocao = get_object_or_404(Promocao, slug=slug, ativa=True)
    bebidas = Bebida.objects.all()
    pizzas = promocao.pizzas.all()

    return render(request, 'pedido_promocao.html', {
        'promocao': promocao,
        'pizzas': pizzas,
        'bebidas': bebidas,
    })

@login_cliente_required
@require_POST
def excluir_promocao(request, id):
    if not request.user.is_superuser:
        return redirect('base')

    promocao = get_object_or_404(Promocao, id=id)
    promocao.delete()
    messages.success(request, "Promoção excluída com sucesso.")
    return redirect('cadastropromocoes')

def promocoes_view(request):
    promocoes = Promocao.objects.all()
    return render(request, "promocoes.html", {"promocoes": promocoes})

def promocao_detalhe_view(request, slug):
    promocao = get_object_or_404(Promocao, slug=slug, ativa=True)
    return render(request, "pedido_promocao.html", {"promocao": promocao})
