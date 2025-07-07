# capizzas_restaurant/apps.py

from django.apps import AppConfig

class CapizzasRestaurantConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'capizzas_restaurant'

    def ready(self):
        import capizzas_restaurant.signals  # Importa e conecta os signals
