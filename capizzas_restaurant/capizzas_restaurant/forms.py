from django import forms    
from .models import Pizza, Compra

class PizzaForm(forms.ModelForm):
    class Meta:
        model = Pizza
        fields = '__all__'


class CompraForm(forms.ModelForm):
    class Meta:
        model = Compra
        fields = '__all__'