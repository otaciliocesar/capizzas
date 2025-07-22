from django.views.generic import TemplateView
from django.shortcuts import render, redirect, get_object_or_404
from capizzas_restaurant.models import Pizza, Compra, Bebida, CompraBebida
from django.core.serializers.json import DjangoJSONEncoder
import json
from django.contrib import messages
from .forms import PizzaForm, ClienteForm, CompraForm, BebidaForm, PromocaoForm, ProdutoDiversoForm, BordaForm
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate, login
from functools import wraps
from django.views.decorators.http import require_http_methods, require_POST
from django.db import transaction
from .models import Promocao, Cliente, ProdutoDiverso, Borda
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.shortcuts import render, redirect
from django.contrib import messages
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


@login_required(login_url='login')
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

@login_required(login_url='login')
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

@login_required(login_url='login')
def excluir_pizza(request, pizza_id):
    if not request.user.is_superuser:
        return redirect('cadastropizza')  # Protege para só admin excluir

    pizza = get_object_or_404(Pizza, id=pizza_id)
    pizza.delete()
    return redirect('cadastropizza')


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
            dados = form.cleaned_data

            # Verifica se já existe um usuário com esse email
            if User.objects.filter(username=dados['email']).exists():
                messages.error(request, "Já existe um usuário com este email.")
                return render(request, 'cadastrocliente_form.html', {'form': form})

            # Cria o usuário (login com email como username)
            user = User.objects.create_user(
                username=dados['email'],
                email=dados['email'],
                password=dados['senha'],  # campo do formulário
                first_name=dados['nome'],
                last_name=dados['sobrenome']
            )

            # Cria o cliente vinculado
            cliente = Cliente.objects.create(
                user=user,
                nome=dados['nome'],
                sobrenome=dados['sobrenome'],
                email=dados['email'],
                endereco_entrega=dados['endereco_entrega'],
                numero=dados['numero']
            )

            messages.success(request, "Cadastro realizado com sucesso. Você já pode fazer login.")
            return redirect('login')
    else:
        form = ClienteForm()

    return render(request, 'cadastrocliente_form.html', {'form': form})


def login_cliente(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        senha = request.POST.get('senha')

        user = authenticate(request, username=email, password=senha)
        if user:
            login(request, user)
            return redirect('cardapio')
        else:
            messages.error(request, "Email ou senha inválidos.")
    return render(request, 'login.html')


def logout_cliente(request):
    request.session.flush()  # Remove todas as variáveis de sessão
    return redirect('base')  # Ou para onde quiser redirecionar após o logout




import json
from decimal import Decimal

@login_required(login_url='login')
def carrinho_view(request):
    cliente = request.user.cliente
    pizzas = Pizza.objects.all()
    bebidas = Bebida.objects.all()
    carrinho_session = request.session.get("carrinho", [])

    if request.method == 'POST':
        # Recebe o JSON do campo oculto
        pedido_json = request.POST.get('pedido_final')
        if not pedido_json:
            # Trate o erro ou redirecione
            return redirect('carrinho')

        pedido_itens = json.loads(pedido_json)

        # Para simplificar, crie uma compra para cada pizza (ou adapte conforme seu modelo)
        for item in pedido_itens:
            if item['tipo'] == 'pizza':
                pizza1 = Pizza.objects.get(id=item['pizza1']['id'])
                pizza2 = None
                if item.get('pizza2'):
                    pizza2 = Pizza.objects.get(id=item['pizza2']['id'])

                preco_pizza1 = pizza1.preco
                preco_pizza2 = pizza2.preco if pizza2 else Decimal('0.00')
                preco_base = max(preco_pizza1, preco_pizza2)

                borda_info = item.get('borda')
                preco_borda = Decimal(borda_info['preco']) if borda_info else Decimal('0.00')

                compra = Compra(
                    cliente=cliente,
                    pizza_1=pizza1,
                    pizza_2=pizza2,
                    preco_final=preco_base + preco_borda,
                    borda=borda_info  # salva dict com sabores e preco
                )
                compra.save()

            elif item['tipo'] == 'bebida':
                # Similarmente, salvar bebidas se você tiver o model para isso
                pass

        # Limpa carrinho da sessão após salvar
        request.session["carrinho"] = []

        return redirect('pagina_de_sucesso')

    else:
        form = CompraForm()
    
    bordas = Borda.objects.all()

    return render(request, 'carrinho.html', {
    'form': form,
    'pizzas': list(pizzas.values('id', 'nome', 'preco')),
    'bebidas': list(bebidas.values('id', 'nome', 'preco')),
    'bordas': list(bordas.values('id', 'nome', 'preco')),
    'carrinho': carrinho_session,
})




@login_required(login_url='login')
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

            promocao_slug = request.POST.get("promocao_slug")
            if promocao_slug:
                request.session["promocao_slug"] = promocao_slug
            else:
                request.session.pop("promocao_slug", None)

            cliente = request.user.cliente
            total = 0
            for item in carrinho:
                if item["tipo"] == "pizza":
                    total += float(item.get("total", 0))
                elif item["tipo"] == "bebida":
                    preco = item.get("bebida", {}).get("preco", 0)
                    quantidade = item.get("quantidade", 1)
                    total += float(preco) * int(quantidade)

            itens_html = ""
            for item in carrinho:                
                if item['tipo'] == 'pizza':
                    sabores = item.get('sabores', [])
                    nomes_sabores = ' + '.join(sabor['nome'] for sabor in sabores)
                    borda = item.get('borda', {})
                    borda_nome = borda['sabores'][0] if borda.get('temBorda') and borda.get('sabores') else 'Sem borda'
                    itens_html += (
                        f"<li>🍕 {nomes_sabores} + Borda: {borda_nome} — <strong>R$ {item['total']}</strong></li>"
                    )
                elif item['tipo'] == 'bebida':
                    bebida = item.get('bebida', {})
                    nome_bebida = bebida.get('nome', 'Bebida')
                    quantidade = item.get('quantidade', 1)
                    preco = bebida.get('preco', 0)
                    total_bebida = float(preco) * int(quantidade)
                    itens_html += (
                        f"<li>🥤 {nome_bebida} x {quantidade} — <strong>R$ {total_bebida:.2f}</strong></li>"
                    )

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





@login_required(login_url='login')
@require_POST
def finalizar_pedido(request):
    cliente = request.user.cliente
    carrinho_str = request.POST.get('pedido_final', '[]')

    try:
        carrinho = json.loads(carrinho_str)
    except json.JSONDecodeError:
        messages.error(request, "Erro no formato do pedido. Tente novamente.")
        return redirect('checkout')

    try:
        with transaction.atomic():
            compras_bebidas = []  # lista para agrupar bebidas por compra

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
                    # Salva borda como JSON se existir
                    if item.get('borda'):
                        compra.borda = item['borda']
                        compra.save()

                elif item['tipo'] == 'bebida':
                    # Para bebidas, vamos criar uma compra "sem pizza"
                    bebida_id = item['bebida']['id']
                    quantidade = item['quantidade']
                    preco_final = float(item['total'])

                    compra = Compra.objects.create(
                        cliente=cliente,
                        pizza_1=None,
                        pizza_2=None,
                        preco_final=preco_final,
                        quantidade=quantidade
                    )
                    CompraBebida.objects.create(
                        compra=compra,
                        bebida_id=bebida_id,
                        quantidade=quantidade
                    )

        messages.success(request, "Pedido finalizado com sucesso! Confirmação enviada por e-mail.")
        request.session.pop('promocao_slug', None)
        return redirect('cardapio')

    except Exception as e:
        messages.error(request, f"Erro ao finalizar pedido: {e}")
        return redirect('checkout')

    

@login_required(login_url='login')
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

@login_required(login_url='login')
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

@login_required(login_url='login')
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

@login_required(login_url='login')
def clientes_pedidos(request):
    cliente = Cliente.objects.get(user=request.user)
    pedidos = Compra.objects.filter(cliente=cliente).order_by('-timestamp').prefetch_related('bebidas', 'comprabebida_set')

    return render(request, 'clientespedidos.html', {'pedidos': pedidos})



@login_required(login_url='login')
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

@login_required(login_url='login')
def excluir_bebida(request, id):
    if not request.user.is_superuser:
        return redirect('base')
    bebida = get_object_or_404(Bebida, id=id)
    bebida.delete()
    return redirect('cadastrobebidas')

@login_required(login_url='login')
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

@login_required(login_url='login')
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

@login_required(login_url='login')
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


def cadastro_borda(request):
    bordas = Borda.objects.all()
    sucesso = False

    if request.method == 'POST':
        form = BordaForm(request.POST)
        if form.is_valid():
            form.save()
            sucesso = True
            return redirect('cadastro_borda')  # Redireciona para limpar o form
    else:
        form = BordaForm()

    return render(request, 'cadastroborda_form.html', {
        'form': form,
        'bordas': bordas,
        'sucesso': sucesso
    })