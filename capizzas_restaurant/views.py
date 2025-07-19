from django.views.generic import TemplateView
from django.shortcuts import render, redirect, get_object_or_404
from capizzas_restaurant.models import Pizza, Compra, Bebida, CompraBebida
from django.core.serializers.json import DjangoJSONEncoder
import json
from django.contrib import messages
from decimal import Decimal
from .forms import PizzaForm, ClienteForm, CompraForm, BebidaForm, PromocaoForm, ProdutoDiversoForm
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate, login
from functools import wraps
from django.views.decorators.http import require_http_methods, require_POST
from django.template.loader import render_to_string
from django.db import transaction
from .models import Promocao, Cliente, ProdutoDiverso
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.shortcuts import render, redirect
from django.contrib import messages
from utils.email import enviar_email
from django.urls import reverse

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

def login_cliente_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f'/login/?next={request.path}')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


@login_cliente_required
def cadastro_pizza(request):
    if not request.user.is_superuser:
        return redirect('base')

    pizza_id = request.GET.get('editar_pizza')
    pizza_instance = get_object_or_404(Pizza, id=pizza_id) if pizza_id else None

    if request.method == 'POST':
        form = PizzaForm(request.POST, request.FILES, instance=pizza_instance)
        if form.is_valid():
            form.save()
            return redirect('cadastropizza')
    else:
        form = PizzaForm(instance=pizza_instance)

    pizzas = Pizza.objects.all().order_by('nome')
    return render(request, 'cadastropizza_form.html', {
        'form': form,
        'pizzas': pizzas,
        'pizza_editando': pizza_instance
    })


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




@login_cliente_required
def carrinho_view(request):
    cliente = request.user.cliente
    pizzas = Pizza.objects.all()
    bebidas = Bebida.objects.all()
    carrinho = request.session.get("carrinho", [])

    if request.method == 'POST':
        form = CompraForm(request.POST)
        if form.is_valid():
            compra = form.save(commit=False)
            compra.cliente = cliente

            # Lógica de preço com base na pizza_1 e pizza_2
            preco1 = compra.pizza_1.preco
            preco2 = compra.pizza_2.preco if compra.pizza_2 else 0
            compra.preco_final = max(preco1, preco2)

            compra.save()

            # Limpa o carrinho da sessão após salvar
            request.session["carrinho"] = []

            return redirect('pagina_de_sucesso')
    else:
        form = CompraForm()

    return render(request, 'carrinho.html', {
        'form': form,
        'pizzas': pizzas,
        'bebidas': bebidas,
        'carrinho': carrinho,
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
            request.session["carrinho"] = carrinho  # Salva o carrinho na sessão

            # Opcional: salvar slug da promoção na sessão, se enviado no POST
            promocao_slug = request.POST.get("promocao_slug")
            if promocao_slug:
                request.session["promocao_slug"] = promocao_slug
            else:
                request.session.pop("promocao_slug", None)

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
            return redirect("checkout")  # Ou outra página após confirmação

        except json.JSONDecodeError:
            messages.error(request, "Erro ao processar o carrinho.")
            return redirect("carrinho")

    # GET
    carrinho = request.session.get("carrinho", [])
    promocao_slug = request.session.get("promocao_slug")

    # Definir URL de voltar sempre
    if promocao_slug:
        voltar_url = reverse('pedido_promocao', args=[promocao_slug])
    else:
        voltar_url = reverse('carrinho')

    promocao = None
    if promocao_slug:
        try:
            promocao = Promocao.objects.get(slug=promocao_slug)
        except Promocao.DoesNotExist:
            promocao = None

    return render(request, "checkout.html", {
        "carrinho": carrinho,
        "promocao": promocao,
        "voltar_url": voltar_url,
    })




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
        request.session.pop('promocao_slug', None)
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
    carrinho = request.session.get("carrinho", [])  # <-- incluir para consistência

    request.session['promocao_slug'] = promocao.slug
    return render(request, 'pedido_promocao.html', {
        'promocao': promocao,
        'pizzas': pizzas,
        'bebidas': bebidas,
        'carrinho': carrinho,
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

@login_cliente_required
def clientes_pedidos(request):
    cliente = Cliente.objects.get(user=request.user)
    pedidos = Compra.objects.filter(cliente=cliente).order_by('-timestamp').prefetch_related('bebidas', 'comprabebida_set')

    return render(request, 'clientespedidos.html', {'pedidos': pedidos})



@login_cliente_required
def cadastro_bebidas(request):
    if not request.user.is_superuser:
        return redirect('base')

    bebida_instance = None

    if request.method == 'POST':
        bebida_id = request.POST.get('bebida_id')
        if bebida_id:
            bebida_instance = get_object_or_404(Bebida, id=bebida_id)
        form = BebidaForm(request.POST, request.FILES, instance=bebida_instance)
        if form.is_valid():
            form.save()
            return redirect('cadastrobebidas')
    else:
        bebida_id = request.GET.get('editar_bebida')
        if bebida_id:
            bebida_instance = get_object_or_404(Bebida, id=bebida_id)
        form = BebidaForm(instance=bebida_instance)

    bebidas = Bebida.objects.all().order_by('nome')
    return render(request, 'cadastrobebidas_form.html', {
        'bebida_form': form,
        'bebidas': bebidas,
        'bebida_editando': bebida_instance
    })

@login_cliente_required
def excluir_bebida(request, id):
    if not request.user.is_superuser:
        return redirect('base')
    bebida = get_object_or_404(Bebida, id=id)
    bebida.delete()
    return redirect('cadastrobebidas')

@login_cliente_required
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

@login_cliente_required
def cadastro_produtos_diversos(request):
    produto_editando = None
    error = None

    if 'editar_produto' in request.GET:
        produto_editando = get_object_or_404(ProdutoDiverso, id=request.GET.get('editar_produto'))

    if request.method == 'POST':
        if produto_editando:
            form = ProdutoDiversoForm(request.POST, request.FILES, instance=produto_editando)
        else:
            form = ProdutoDiversoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('cadastrodiversos')  # nome da url
        else:
            error = "Erro ao salvar o produto. Verifique os dados."
    else:
        form = ProdutoDiversoForm(instance=produto_editando)

    produtos = ProdutoDiverso.objects.all()

    return render(request, 'cadastrodiversos_form.html', {
        'form': form,
        'produtos': produtos,
        'produto_editando': produto_editando,
        'error': error
    })

def excluir_diverso(request, produto_id):
    produto = get_object_or_404(ProdutoDiverso, id=produto_id)
    produto.delete()
    return redirect('cadastrodiversos')

@login_cliente_required
def editar_perfil(request):
    cliente = get_object_or_404(Cliente, user=request.user)
    sucesso = False

    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            sucesso = True
    else:
        form = ClienteForm(instance=cliente)

    return render(request, 'editar_perfil.html', {
        'form': form,
        'sucesso': sucesso
    })