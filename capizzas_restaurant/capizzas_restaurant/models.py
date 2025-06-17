from django.db import models

class Pizza(models.Model):
    nome = models.CharField(max_length=100)
    ingredientes = models.TextField()
    preco = models.DecimalField(max_digits=6, decimal_places=2)
    imagem = models.ImageField(upload_to='pizzas/', null=True, blank=True)

    def __str__(self):
        return self.nome
