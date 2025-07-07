

import os
from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import Pizza

@receiver(post_delete, sender=Pizza)
def deletar_imagem_pizza(sender, instance, **kwargs):
    """Remove a imagem da pizza do disco quando o objeto é deletado."""
    if instance.imagem and os.path.isfile(instance.imagem.path):
        os.remove(instance.imagem.path)
