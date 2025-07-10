from django.db import models

class Cliente(models.Model):
    nome = models.CharField(max_length=100)
    sobrenome = models.CharField(max_length=100)
    senha = models.CharField(max_length=128)
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

class Pedido(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True)
    data_pedido = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='Pendente')  # Ex: Pendente, Pago, Entregue, Cancelado

    def __str__(self):
        return f"Pedido {self.id} - {self.cliente or 'Cliente não informado'} - {self.status}"

    def get_total(self):
        total = sum(item.get_subtotal() for item in self.itens.all())
        return total

class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, related_name='itens', on_delete=models.CASCADE)
    pizza = models.ForeignKey(Pizza, on_delete=models.CASCADE)
    quantidade = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantidade}x {self.pizza.nome}"

    def get_subtotal(self):
        return self.quantidade * self.pizza.preco
