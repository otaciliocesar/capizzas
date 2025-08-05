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
        fields = [
            'nome', 'sobrenome', 'email', 'telefone', 'endereco_entrega', 'numero',
            'complemento', 'bairro', 'cidade', 'estado', 'cep', 'senha'
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'sobrenome': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(XX) 9XXXX-XXXX'}),
            'endereco_entrega': forms.TextInput(attrs={'class': 'form-control'}),
            'numero': forms.TextInput(attrs={'class': 'form-control'}),
            'complemento': forms.TextInput(attrs={'class': 'form-control'}),
            'bairro': forms.TextInput(attrs={'class': 'form-control'}),
            'cidade': forms.TextInput(attrs={'class': 'form-control'}),
            'estado': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 2}),
            'cep': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'XXXXX-XXX'}),
        }

    def clean_cep(self):
        cep = self.cleaned_data.get("cep")
        if cep and not re.match(r'^\d{5}-\d{3}$', cep):
            raise forms.ValidationError("CEP inválido. Use o formato XXXXX-XXX.")
        return cep

    def clean_telefone(self):
        telefone = self.cleaned_data.get("telefone")
        if telefone and not re.match(r'^\(\d{2}\)\s?\d{4,5}-\d{4}$', telefone):
            raise forms.ValidationError("Telefone inválido. Use o formato (XX) 9XXXX-XXXX.")
        return telefone

class CompraForm(forms.ModelForm):
    class Meta:
        model = Compra
        fields = '__all__'
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