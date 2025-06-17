from django.views.generic import TemplateView
from django.shortcuts import render
from capizzas_restaurant.models import Pizza
from django.shortcuts import render
from django.core.serializers.json import DjangoJSONEncoder
import json
from decimal import Decimal

class HomePageView(TemplateView):    
    template_name = 'home.html'    
    context_object_name = 'home'

class SobrePageView(TemplateView):
    template_name = 'sobre.html'
    context_object_name = 'sobre'

class LocalizacaoPageView(TemplateView):
    template_name = 'localizacao.html'
    context_object_name = 'localizacao'


def Cardapio(request):
    pizzas = Pizza.objects.all()
    return render(request, 'cardapio.html', {'pizzas': pizzas})


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


