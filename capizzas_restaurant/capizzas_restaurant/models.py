from django.db import models

class Pizza(models.Model):
    nome = models.CharField(max_length=100)
    ingredientes = models.TextField()
    preco = models.DecimalField(max_digits=6, decimal_places=2)
    imagem = models.ImageField(upload_to='pizzas/', null=True, blank=True)

    def __str__(self):
        return self.nome

class Compra(models.Model):
    nome = models.ForeignKey(Pizza, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nome} vendido em {self.timestamp.strftime('%d/%m/%Y %H:%M')}"