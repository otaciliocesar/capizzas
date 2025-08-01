from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.db.models import JSONField

class Cliente(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    nome = models.CharField(max_length=100)
    sobrenome = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    endereco_entrega = models.CharField(max_length=200)
    numero = models.CharField(max_length=15)

    def __str__(self):
        return f"{self.nome} {self.sobrenome}"


class Pizza(models.Model):
    nome = models.CharField(max_length=100)
    ingredientes = models.TextField()
    preco = models.DecimalField(max_digits=6, decimal_places=2)
    imagem = models.ImageField(upload_to='pizzas/', null=True, blank=True)

    def __str__(self):
        return self.nome
    
class Borda(models.Model):
    nome = models.CharField(max_length=50)
    preco = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f"{self.nome} - R${self.preco}"


class Bebida(models.Model):
    nome = models.CharField(max_length=100)
    preco = models.DecimalField(max_digits=6, decimal_places=2)
    imagem = models.ImageField(upload_to='bebidas/', null=True, blank=True)

    def __str__(self):
        return self.nome  

class Compra(models.Model):
    cliente = models.ForeignKey('Cliente', on_delete=models.CASCADE)
    preco_final = models.DecimalField(max_digits=6, decimal_places=2)
    bebidas = models.ManyToManyField('Bebida', through='CompraBebida', blank=True)
    updated = models.DateTimeField(auto_now=True)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Compra #{self.pk} - Cliente: {self.cliente.nome}"


class CompraBebida(models.Model):
    compra = models.ForeignKey(Compra, on_delete=models.CASCADE)
    bebida = models.ForeignKey(Bebida, on_delete=models.CASCADE)
    quantidade = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantidade}x {self.bebida.nome} (Pedido #{self.compra.pk})"
    
    
class Promocao(models.Model):
    titulo = models.CharField(max_length=100)
    descricao = models.TextField()
    preco = models.DecimalField(max_digits=6, decimal_places=2)
    imagem = models.ImageField(upload_to='promocoes/', blank=True, null=True)
    pizzas = models.ManyToManyField(Pizza, related_name='promocoes')
    bebidas = models.ManyToManyField(Bebida, blank=True, related_name='promocoes')
    ativa = models.BooleanField(default=True)
    slug = models.SlugField(unique=True, blank=True)  # ← AQUI

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.titulo)
            slug = base_slug
            counter = 1
            while Promocao.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


class ProdutoDiverso(models.Model):
    nome = models.CharField(max_length=100)
    preco = models.DecimalField(max_digits=6, decimal_places=2)
    imagem = models.ImageField(upload_to='diversos/', null=True, blank=True)

    def __str__(self):
        return self.nome


class CompraItemPizza(models.Model):
    compra = models.ForeignKey('Compra', on_delete=models.CASCADE, related_name='itens_pizza')
    pizza_1 = models.ForeignKey('Pizza', related_name='item_pizza_sabor1', on_delete=models.CASCADE)
    pizza_2 = models.ForeignKey('Pizza', related_name='item_pizza_sabor2', on_delete=models.CASCADE, null=True, blank=True)
    borda = JSONField(null=True, blank=True)
    preco = models.DecimalField(max_digits=6, decimal_places=2)
    quantidade = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantidade}x {self.pizza_1} {'+ ' + self.pizza_2.nome if self.pizza_2 else ''}"
