from django import forms  
from django.contrib.auth.models import User  
from .models import Pizza, Cliente, Compra, Bebida, Promocao, ProdutoDiverso

class PizzaForm(forms.ModelForm):
    class Meta:
        model = Pizza
        fields = '__all__'


class ClienteForm(forms.ModelForm):
    senha = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Cliente
        fields = ['nome', 'sobrenome', 'email', 'endereco_entrega', 'numero', 'senha']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'sobrenome': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'endereco_entrega': forms.TextInput(attrs={'class': 'form-control'}),
            'numero': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_email(self):
        email = self.cleaned_data['email']
        from django.contrib.auth.models import User
        if User.objects.filter(username=email).exists():
            raise forms.ValidationError("Este e-mail já está em uso.")
        return email

class CompraForm(forms.ModelForm):
    class Meta:
        model = Compra
        fields = ['pizza_1', 'pizza_2', 'quantidade']
        widgets = {
            'pizza_1': forms.Select(attrs={'class': 'form-control'}),
            'pizza_2': forms.Select(attrs={'class': 'form-control'}),
            'quantidade': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }        

class BebidaForm(forms.ModelForm):
    class Meta:
        model = Bebida
        fields = '__all__'


class PromocaoForm(forms.ModelForm):
    class Meta:
        model = Promocao
        fields = ['titulo', 'descricao', 'preco', 'imagem', 'pizzas', 'bebidas', 'ativa']
        widgets = {
            'pizzas': forms.CheckboxSelectMultiple,
            'bebidas': forms.CheckboxSelectMultiple,
            'preco': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class ProdutoDiversoForm(forms.ModelForm):
    class Meta:
        model = ProdutoDiverso
        fields = ['nome', 'preco', 'imagem']