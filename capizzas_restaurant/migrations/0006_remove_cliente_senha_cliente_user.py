# Generated by Django 5.2.4 on 2025-07-10 21:34

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "capizzas_restaurant",
            "0005_remove_pedido_cliente_compra_delete_itempedido_and_more",
        ),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name="cliente",
            name="senha",
        ),
        migrations.AddField(
            model_name="cliente",
            name="user",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
