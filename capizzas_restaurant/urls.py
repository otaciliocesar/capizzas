from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views
from . views import HomePageView, SobrePageView, LocalizacaoPageView

app = 'capizzas_restaurant'

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('sobre/', SobrePageView.as_view(), name='sobre'),
    path('localizacao/', LocalizacaoPageView.as_view(), name='localizacao'),
    path('cardapio/', views.Cardapio, name='cardapio'),
    path('carrinho/', views.Carrinho, name='carrinho'),
   # path('comprapizza/add/', views.CompraPizza, name='comprapizza'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
