from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views
from . views import HomePageView, SobrePageView, LocalizacaoPageView
from django.contrib.auth.views import LoginView, LogoutView

app = 'capizzas_restaurant'

urlpatterns = [
    path('', HomePageView.as_view(), name='base'),
    path('sobre/', SobrePageView.as_view(), name='sobre'),
    path('localizacao/', LocalizacaoPageView.as_view(), name='localizacao'),
    path('cardapio/', views.Cardapio, name='cardapio'),
    path('carrinho/', views.carrinho_view, name='carrinho'),
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),
    path('login_cliente/', views.login_cliente, name='login_cliente'),
    path('logout_cliente/', views.logout_cliente, name='logout_cliente'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('cadastropizza/add/', views.cadastro_pizza, name='cadastropizza'),
    path('cadastropizza/<int:id>/editar/', views.editar_pizza, name='editar_pizza'),
    path('cadastropizza/excluir/<int:pizza_id>/', views.excluir_pizza, name='excluir_pizza'),
    path('bebida/cadastrar/', views.cadastrar_bebida, name='cadastrar_bebida'),
    path('bebida/editar/<int:id>/', views.editar_bebida, name='editar_bebida'),
    path('bebida/excluir/<int:id>/', views.excluir_bebida, name='excluir_bebida'),
    path('cadastrocliente/', views.cadastro_cliente, name='cadastrocliente'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('finalizar/', views.finalizar_pedido, name='finalizar_pedido'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
