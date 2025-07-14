from django import forms  
from django.contrib.auth.models import User  
from .models import Pizza, Cliente, Compra, Bebida, Promocao

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

    def save(self, commit=True):
        cliente = super().save(commit=False)
        senha = self.cleaned_data['senha']
        email = self.cleaned_data['email']
        nome = self.cleaned_data['nome']
        sobrenome = self.cleaned_data['sobrenome']

        user = User.objects.create_user(
            username=email,
            email=email,
            password=senha,
            first_name=nome,
            last_name=sobrenome
        )

        cliente.user = user

        if commit:
            cliente.save()
        return cliente

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