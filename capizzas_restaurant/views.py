from django.views.generic import TemplateView
from django.shortcuts import render, redirect
from capizzas_restaurant.models import Pizza
from django.shortcuts import render
from django.core.serializers.json import DjangoJSONEncoder
import json
from decimal import Decimal
from .forms import PizzaForm

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

def CadastroPizza(request):
    if request.method == 'POST':
        form = PizzaForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = PizzaForm()
    return render(request, 'cadastropizza_form.html', {'form': form}) 


        
def pedidopizza(request):
    pizzas = Pizza.objects.all().values('nome', 'ingredientes', 'preco')
    pizzas_json = json.dumps(list(pizzas), cls=DjangoJSONEncoder)
    return render(request, 'pedidopizza.html', {'pizzas_json': pizzas_json})


def Carrinho(request):
    return render(request, 'carrinho.html')

def NovoPedido(request):
    pizzas = Pizza.objects.all()
    return render(request, 'carrinho_novo.html', {'pizzas': pizzas})

def HomeData(request):
    pizzas = Pizza.objects.all().values('nome', 'ingredientes', 'preco')
    context = {
        'pizzas_json': json.dumps(list(pizzas), cls=DjangoJSONEncoder)
    }
    return render(request, 'home.html', context)


