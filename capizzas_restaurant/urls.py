from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views
from . views import SobrePageView, LocalizacaoPageView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import views as auth_views


app = 'capizzas_restaurant'

urlpatterns = [
    path('', views.Home_View, name='home'),
    path('sobre/', SobrePageView.as_view(), name='sobre'),
    path('localizacao/', LocalizacaoPageView.as_view(), name='localizacao'),
    path('cardapio/', views.Cardapio, name='cardapio'),
    path('carrinho/', views.carrinho_view, name='carrinho'),
    path('gerenciar_promocoes/', views.gerenciar_promocoes, name='cadastropromocoes'),\
    path("promocoes/", views.promocoes_view, name="promocoes"),
    path("promocao/<slug:slug>/", views.promocao_detalhe_view, name="promocao_detalhe"),
    path('promocao/excluir/<int:id>/', views.excluir_promocao, name='excluir_promocao'),
    path('promocao/<int:promo_id>/', views.pedido_promocao, name='pedido_promocao'),
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),
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
    path('recuperar-senha/', auth_views.PasswordResetView.as_view(template_name='recuperar_senha.html'), name='password_reset'),
    path('recuperar-senha/enviado/', auth_views.PasswordResetDoneView.as_view(template_name='recuperar_senha_enviado.html'), name='password_reset_done'),
    path('resetar/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='resetar_senha.html'), name='password_reset_confirm'),
    path('resetar/sucesso/', auth_views.PasswordResetCompleteView.as_view(template_name='resetar_sucesso.html'), name='password_reset_complete'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
