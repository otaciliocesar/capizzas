from django.views.generic import TemplateView
from django.shortcuts import render

class HomePageView(TemplateView):    
    template_name = 'home.html'    
    context_object_name = 'home'



def sobre(request):
    return render(request, 'sobre.html')

def localizacao(request):
    return render(request, 'localizacao.html')

def cardapio(request):
    pizzas = [
        {"nome": "Calabresa", "ingredientes": "Molho, mussarela, calabresa e cebola", "preco": "39,90", "imagem": "img/calabresa.jpg"},
        {"nome": "Frango com Catupiry", "ingredientes": "Molho, frango desfiado e catupiry", "preco": "44,90", "imagem": "img/frangocatupiry.jpg"},
        {"nome": "Portuguesa", "ingredientes": "Molho, presunto, ovo, cebola e pimentão", "preco": "42,90", "imagem": "img/portuguesa.jpg"},
        {"nome": "Marguerita", "ingredientes": "Molho, tomate, manjericão e mussarela", "preco": "38,90", "imagem": "img/marguerita.jpg"},
        {"nome": "Quatro Queijos", "ingredientes": "Mussarela, gorgonzola, provolone e parmesão", "preco": "45,90", "imagem": "img/4queijos.jpg"},
        {"nome": "Pepperoni", "ingredientes": "Molho, mussarela e pepperoni", "preco": "46,90", "imagem": "img/pepperoni.jpg"},
        {"nome": "Vegetariana", "ingredientes": "Molho, berinjela, abobrinha e pimentão", "preco": "40,90", "imagem": "img/vegetariana.jpg"},
        {"nome": "Doce de Banana", "ingredientes": "Banana, açúcar e canela", "preco": "36,90", "imagem": "img/banana.avif"},
        {"nome": "Chocolate com Morango", "ingredientes": "Chocolate ao leite e morangos frescos", "preco": "49,90", "imagem": "img/chocolate.jpg"},
    ]
    return render(request, 'cardapio.html', {'pizzas': pizzas})
