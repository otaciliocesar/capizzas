from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class Cliente(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    nome = models.CharField(max_length=100)
    sobrenome = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    endereco_entrega = models.CharField(max_length=200)
    numero = models.CharField(max_length=11)

    def __str__(self):
        return f"{self.nome} {self.sobrenome}"


class Pizza(models.Model):
    nome = models.CharField(max_length=100)
    ingredientes = models.TextField()
    preco = models.DecimalField(max_digits=6, decimal_places=2)
    imagem = models.ImageField(upload_to='pizzas/', null=True, blank=True)

    def __str__(self):
        return self.nome
    
class Bebida(models.Model):
    nome = models.CharField(max_length=100)
    preco = models.DecimalField(max_digits=6, decimal_places=2)
    imagem = models.ImageField(upload_to='bebidas/', null=True, blank=True)

    def __str__(self):
        return self.nome  

class Compra(models.Model):
    cliente = models.ForeignKey('Cliente', on_delete=models.CASCADE)
    pizza_1 = models.ForeignKey('Pizza', related_name='pizza_sabor1', on_delete=models.CASCADE)
    pizza_2 = models.ForeignKey('Pizza', related_name='pizza_sabor2', on_delete=models.CASCADE, null=True, blank=True)
    preco_final = models.DecimalField(max_digits=6, decimal_places=2)
    quantidade = models.PositiveIntegerField(default=1)
    bebidas = models.ManyToManyField('Bebida', through='CompraBebida', blank=True)
    updated = models.DateTimeField(auto_now=True)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Pedido de {self.cliente.nome} - {self.quantidade}x {self.pizza_1} {'+ ' + self.pizza_2.nome if self.pizza_2 else ''}"


class CompraBebida(models.Model):
    compra = models.ForeignKey(Compra, on_delete=models.CASCADE)
    bebida = models.ForeignKey(Bebida, on_delete=models.CASCADE)
    quantidade = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantidade}x {self.bebida.nome} (Pedido #{self.compra.id})"