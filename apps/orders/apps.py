"""
==============================================================================
CONFIGURACIÓN DE LA APP ORDERS
==============================================================================
Define la configuración de la aplicación 'orders' (órdenes y transacciones).

Señales conectadas (en el método ready()):
    - log_order_status_change: registra cambios de estado de órdenes.
    - log_order_created: registra la creación de nuevas órdenes.

Autor: José Fica
Sección: AP-N4-C2
Año: 2026
==============================================================================
"""

from django.apps import AppConfig


class OrdersConfig(AppConfig):
    """
    Configuración de la app Orders.

    Atributos:
        default_auto_field: Tipo de PK por defecto (BigAutoField).
        name: Ruta completa del módulo (apps.orders).
        verbose_name: Nombre legible para el panel admin.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.orders'
    verbose_name = 'Órdenes y Transacciones'

    def ready(self):
        """
        Se ejecuta cuando Django termina de cargar la app.

        Importa las señales para que se registren con Django. El import
        debe estar DENTRO del método para evitar problemas de carga
        temprana (los modelos aún no están listos al importar apps.py).
        """
        import apps.orders.signals  # noqa: F401