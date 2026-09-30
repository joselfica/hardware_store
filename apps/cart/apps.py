"""
==============================================================================
CONFIGURACIÓN DE LA APP CART
==============================================================================
Define la configuración de la aplicación 'cart' (carro de compras).
Incluye metadata como el nombre completo y el verbose_name que Django
usa en el panel de administración.

Nota: si en el futuro se implementan señales (signals) para el carro,
este es el lugar donde se importarían en el método `ready()`.

Autor: José Fica
Sección: AP-N4-C2
Año: 2026
==============================================================================
"""

from django.apps import AppConfig


class CartConfig(AppConfig):
    """
    Configuración de la app Cart.

    Atributos:
        default_auto_field: Tipo de PK por defecto (BigAutoField).
        name: Ruta completa del módulo (apps.cart).
        verbose_name: Nombre legible para el panel admin.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.cart'
    verbose_name = 'Carro de Compras'

    # ------------------------------------------------------------------------
    # MÉTODO ready()
    # ------------------------------------------------------------------------
    # Se ejecuta cuando Django termina de cargar la app. Aquí se importarían
    # las señales si las tuvieras. Ejemplo:
    #
    #     def ready(self):
    #         import apps.cart.signals  # noqa
    #
    # Como actualmente no hay señales en esta app, el método queda comentado.
    # ------------------------------------------------------------------------