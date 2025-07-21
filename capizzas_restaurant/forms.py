import re
from django import forms  
from django.contrib.auth.models import User  
from .models import Pizza, Cliente, Compra, Bebida, Promocao, ProdutoDiverso, Borda
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

class PizzaForm(forms.ModelForm):
    class Meta:
        model = Pizza
        fields = '__all__'


class ClienteForm(forms.ModelForm):
    senha = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Senha"
    )

    class Meta:
        model = Cliente
        fields = ['nome', 'sobrenome', 'email', 'endereco_entrega', 'numero', 'senha']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'sobrenome': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'endereco_entrega': forms.TextInput(attrs={'class': 'form-control'}),
            'numero': forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'id_numero',
            'placeholder': '(XX) 9XXXX-XXXX'
        }),
    }

    def clean_senha(self):
        senha = self.cleaned_data.get('senha')
        if not senha:
            raise forms.ValidationError("Este campo é obrigatório.")
        if len(senha) < 8:
            raise forms.ValidationError("A senha deve ter no mínimo 8 caracteres.")
        if not re.search(r'[A-Z]', senha):
            raise forms.ValidationError("A senha deve conter pelo menos uma letra maiúscula.")
        if not re.search(r'[a-z]', senha):
            raise forms.ValidationError("A senha deve conter pelo menos uma letra minúscula.")
        if not re.search(r'\d', senha):
            raise forms.ValidationError("A senha deve conter pelo menos um número.")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', senha):
            raise forms.ValidationError("A senha deve conter pelo menos um caractere especial.")
        return senha

    def clean_email(self):
        email = self.cleaned_data.get('email')

        if not email:
            raise forms.ValidationError("Este campo é obrigatório.")

        try:
            validate_email(email)
        except ValidationError:
            raise forms.ValidationError("E-mail inválido.")

        if User.objects.filter(username=email).exists():
            raise forms.ValidationError("Este e-mail já está em uso.")

        return email

    def clean_numero(self):
        numero = self.cleaned_data.get('numero')

        if not numero:
            raise forms.ValidationError("Este campo é obrigatório.")

    # Aceita formatos como: (11) 91234-5678 ou (11) 1234-5678
        pattern = r'^\(\d{2}\)\s?\d{4,5}-\d{4}$'

        if not re.match(pattern, numero):
                raise forms.ValidationError("Número inválido. Use o formato (XX) 9XXXX-XXXX ou (XX) XXXX-XXXX.")

        return numero

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



class BordaForm(forms.ModelForm):
    class Meta:
        model = Borda
        fields = ['nome', 'preco']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome da borda'}),
            'preco': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Preço (ex: 5.00)'}),
        }