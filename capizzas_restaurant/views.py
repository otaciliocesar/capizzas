from django.views.generic import TemplateView
from django.shortcuts import render, redirect, get_object_or_404
from capizzas_restaurant.models import Pizza, Compra, Bebida, CompraBebida, Promocao, ProdutoDiverso, Cliente, Borda, CompraItemPizza
from django.http import HttpResponse, HttpResponseBadRequest
from django.core.serializers.json import DjangoJSONEncoder
import json
from django.contrib import messages
from .forms import PizzaForm, ClienteForm, CompraForm, BebidaForm, PromocaoForm, ProdutoDiversoForm, BordaForm
from django.contrib.auth import authenticate, login
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
from django.conf import settings
from decimal import Decimal
import requests
from xml.etree import ElementTree as ET
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt









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






@login_required(login_url='login')
def carrinho_view(request):
    cliente = request.user.cliente
    pizzas = Pizza.objects.all()
    bebidas = Bebida.objects.all()
    carrinho_session = request.session.get("carrinho", [])

    if request.method == 'POST':
        pedido_json = request.POST.get('pedido_final')
        if not pedido_json:
            return redirect('carrinho')

        pedido_itens = json.loads(pedido_json)
        total = Decimal('0.00')

        compra = Compra.objects.create(
            cliente=cliente,
            preco_final=Decimal('0.00'),
        )

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
                preco_total = preco_base + preco_borda

                CompraItemPizza.objects.create(
                    compra=compra,
                    pizza_1=pizza1,
                    pizza_2=pizza2,
                    borda=borda_info,
                    preco=preco_total,
                    quantidade=1
                )

                total += preco_total

            elif item['tipo'] == 'bebida':
                bebida_data = item.get('bebida')
                if bebida_data:
                    bebida = Bebida.objects.get(id=bebida_data['id'])
                    quantidade = int(item.get('quantidade', 1))
                    
                    # Cria registro CompraBebida com quantidade
                    CompraBebida.objects.create(
                        compra=compra,
                        bebida=bebida,
                        quantidade=quantidade
                    )
                    
                    total += bebida.preco * quantidade

        compra.preco_final = total
        compra.save()

        # Limpa o carrinho da sessão após salvar
        request.session["carrinho"] = []

        return redirect('pagina_de_sucesso')

    else:
        form = CompraForm()

    bordas = Borda.objects.all()

    return render(request, 'carrinho.html', {
        'form': form,
        'pizzas': pizzas,
        'bebidas': bebidas,
        'bordas': list(bordas.values('id', 'nome', 'preco')),
        'carrinho': carrinho_session,
    })


@login_required(login_url='login')
@require_http_methods(["GET", "POST"])
def checkout_view(request):
    if request.method == "POST":
        if "pedido_final" in request.POST and not request.POST.get("finalizar_pedido"):
            try:
                carrinho = json.loads(request.POST.get("pedido_final"))
                request.session["carrinho"] = carrinho

                promocao_slug = request.POST.get("promocao_slug")
                if promocao_slug:
                    request.session["promocao_slug"] = promocao_slug
                else:
                    request.session.pop("promocao_slug", None)

                return redirect("checkout")
            except json.JSONDecodeError:
                messages.error(request, "Erro ao processar o carrinho.")
                return redirect("carrinho")

        elif "finalizar_pedido" in request.POST:
            carrinho = request.session.get("carrinho")
            promocao_slug = request.session.get("promocao_slug")

            if not carrinho:
                messages.error(request, "Carrinho vazio ou inválido.")
                return redirect("carrinho")

            cliente = request.user.cliente
            total = Decimal('0.00')
            itens_html = ""

            compra = Compra.objects.create(cliente=cliente, preco_final=Decimal('0.00'))

            for item in carrinho:
                if item['tipo'] == 'pizza':
                    pizza1 = Pizza.objects.get(id=item['pizza1']['id'])
                    pizza2 = Pizza.objects.get(id=item['pizza2']['id']) if item.get('pizza2') else None
                    preco_base = max(pizza1.preco, pizza2.preco if pizza2 else Decimal('0.00'))

                    borda_info = item.get('borda')
                    preco_borda = Decimal(borda_info['preco']) if borda_info else Decimal('0.00')
                    preco_total = preco_base + preco_borda

                    CompraItemPizza.objects.create(
                        compra=compra,
                        pizza_1=pizza1,
                        pizza_2=pizza2,
                        borda=borda_info,
                        preco=preco_total,
                        quantidade=1
                    )

                    total += preco_total
                    nomes = [pizza1.nome]
                    if pizza2:
                        nomes.append(pizza2.nome)
                    nome_pizza = " + ".join(nomes)
                    if borda_info and borda_info.get("nome", "").lower() != "sem borda":
                        nome_pizza += f" ({borda_info['nome']})"
                    itens_html += f"<li>🍕 {nome_pizza} — <strong>R$ {preco_total:.2f}</strong></li>"

                elif item['tipo'] == 'bebida':
                    bebida_data = item.get('bebida')
                    if bebida_data:
                        bebida = Bebida.objects.get(id=bebida_data['id'])
                        quantidade = int(item.get('quantidade', 1))
                        CompraBebida.objects.create(compra=compra, bebida=bebida, quantidade=quantidade)
                        subtotal = bebida.preco * quantidade
                        total += subtotal
                        itens_html += f"<li>🥤 {bebida.nome} x {quantidade} — <strong>R$ {subtotal:.2f}</strong></li>"

            compra.preco_final = total
            compra.save()

            request.session["carrinho"] = []
            request.session.pop("promocao_slug", None)

            # Envio de e-mails
            html_email = f"""
                <h2>🍕 Confirmação de Pedido - Capizzas</h2>
                <p>Olá {cliente.nome},</p>
                <p>Recebemos seu pedido com sucesso! Aqui está o resumo:</p>
                <ul>{itens_html}</ul>
                <p><strong>Total do pedido:</strong> R$ {total:.2f}</p>
                <p>🛵 Em breve estaremos chegando com sua pizza quente e saborosa!</p>
                <hr>
                <p>👤 Nome: {cliente.nome} {cliente.sobrenome}</p>
                <p>📱 Número de contato: {cliente.numero}</p>
                <p>📍 Endereço de entrega: {cliente.endereco_entrega}</p>
                <p>📧 E-mail: {cliente.email}</p>
            """

            for destinatario in [request.user.email, settings.EMAIL_HOST_USER]:
                email = EmailMultiAlternatives(
                    subject="🍕 Capizzas - Confirmação do Pedido",
                    body=strip_tags(html_email),
                    from_email=settings.EMAIL_HOST_USER,
                    to=[destinatario],
                )
                email.attach_alternative(html_email, "text/html")
                email.send()

            # PagBank Checkout - sandbox
            headers = {
                "Authorization": f"Bearer {settings.PAGBANK_TOKEN}",
                "Content-Type": "application/json",
            }

            data = {
                "reference_id": f"compra-{compra.pk}",
                "redirect_url": request.build_absolute_uri(reverse("meus_pedidos")),
                "items": [
                    {
                        "name": "Pedido Capizzas",
                        "quantity": 1,
                        "unit_amount": int(compra.preco_final * 100)
                    }
                ],
                "customer": {
                    "name": f"{cliente.nome} {cliente.sobrenome}",
                    "email": cliente.email,
                    "tax_id": "11111111111",  # CPF fictício válido para sandbox
                    "phones": [
                        {
                            "country": "55",
                            "area": "11",
                            "number": "999999999",
                            "type": "MOBILE"
                        }
                    ]
                },
                "shipping": {
                    "address": {
                        "street": "Rua de Teste",
                        "number": "123",
                        "complement": "Apto 45",
                        "locality": "Bairro",
                        "city": "São Paulo",
                        "region_code": "SP",
                        "country": "BRA",
                        "postal_code": "01234567"
                    }
                }
            }

            try:
                response = requests.post(
                    "https://ws.sandbox.pagbank.com.br/v2/checkout",
                    json=data,
                    headers=headers,
                    timeout=10
                )
                if response.status_code == 201:
                    resp_json = response.json()
                    for link in resp_json.get("links", []):
                        if link.get("rel") == "PAY":
                            return redirect(link["href"])
                    messages.error(request, "Link de pagamento não encontrado.")
                else:
                    messages.error(request, f"Erro PagBank: {response.status_code} - {response.text}")
            except requests.RequestException as e:
                messages.error(request, f"Erro ao conectar com PagBank: {e}")

            return redirect("carrinho")

    # GET
    carrinho = request.session.get("carrinho", [])
    promocao_slug = request.session.get("promocao_slug")
    voltar_url = reverse('pedido_promocao', args=[promocao_slug]) if promocao_slug else reverse('carrinho')

    promocao = None
    if promocao_slug:
        try:
            promocao = Promocao.objects.get(slug=promocao_slug)
        except Promocao.DoesNotExist:
            pass

    return render(request, "checkout.html", {
        "carrinho": carrinho,
        "promocao": promocao,
        "voltar_url": voltar_url,
    })
   

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
    cliente = get_object_or_404(Cliente, user=request.user)
    pedidos = Compra.objects.filter(cliente=cliente).order_by('-timestamp')
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


import json


@login_required
@require_POST
def pagamento_pagbank(request):
    try:
        compra = Compra.objects.filter(cliente__user=request.user).order_by('-timestamp').first()
        if not compra:
            return JsonResponse({"error": "Compra não encontrada"}, status=404)

        # Payload conforme exigência do PagBank
        data = {
            "email": settings.PAGBANK_EMAIL,
            "token": settings.PAGBANK_TOKEN,
            "currency": "BRL",
            "reference": f"compra-{compra.pk}",
            "redirectURL": request.build_absolute_uri("/obrigado/"),
            "notificationURL": request.build_absolute_uri("/pagbank/notification/"),
            "itemId1": "001",
            "itemDescription1": "Pedido de Pizzas e Bebidas",
            "itemAmount1": f"{compra.preco_final:.2f}",  # Ex: "10.00"
            "itemQuantity1": "1"
        }

        # Sem headers → requests vai aplicar o correto para form-urlencoded
        response = requests.post(
            "https://ws.sandbox.pagbank.com.br/v2/checkout",
            data=data
        )

        if response.status_code == 200:
            root = ET.fromstring(response.text)
            code_elem = root.find("code")
            if code_elem is None or not code_elem.text:
                return JsonResponse({"error": "Código de pagamento não encontrado no XML"}, status=500)

            code = code_elem.text
            compra.codigo_pagamento = code
            compra.status_pagamento = "Aguardando"
            compra.save()

            return JsonResponse({
                "pagamento_url": f"https://sandbox.pagseguro.uol.com.br/v2/checkout/payment.html?code={code}"
            })

        return JsonResponse({
            "error": f"Erro ao criar pagamento: {response.status_code}",
            "resposta": response.text
        }, status=500)

    except Exception as e:
        return JsonResponse({"error": f"Erro inesperado: {str(e)}"}, status=500)



@csrf_exempt
@require_POST
def pagbank_notification(request):
    notification_code = request.POST.get("notificationCode")
    if not notification_code:
        return JsonResponse({"error": "notificationCode ausente"}, status=400)

    url = f"https://ws.sandbox.pagbank.com.br/v2/notifications/{notification_code}"
    params = {
        "email": settings.PAGBANK_EMAIL,
        "token": settings.PAGBANK_TOKEN,
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        return JsonResponse({"error": "Erro ao consultar notificação"}, status=400)

    try:
        root = ET.fromstring(response.text)
        status_elem = root.find("status")
        reference_elem = root.find("reference")

        if status_elem is None or status_elem.text is None:
            return JsonResponse({"error": "Status ausente na notificação"}, status=400)
        if reference_elem is None or reference_elem.text is None:
            return JsonResponse({"error": "Reference ausente na notificação"}, status=400)

        status = status_elem.text
        reference = reference_elem.text

        compra_id = int(reference.replace("compra-", ""))
        compra = Compra.objects.get(id=compra_id)

        status_map = {
            "1": "Aguardando",
            "2": "Em análise",
            "3": "Pago",
            "7": "Cancelado"
        }

        compra.status_pagamento = status_map.get(status, "Outro")
        compra.save()
    except Exception as e:
        return JsonResponse({"error": f"Erro ao processar notificação: {str(e)}"}, status=500)

    return JsonResponse({"success": True})