"""
==============================================================================
CONFIGURACIÓN DE LA APP CATALOG
==============================================================================
Define la configuración de la aplicación 'catalog' (catálogo de productos).

Contiene:
    - Categorías (Category).
    - Marcas (Brand).
    - Productos (Product).
    - Vistas web del frontend (web_views.py).
    - Comando de gestión `seed_data` para poblar la BD.

Nota: si en el futuro se implementan señales para el catálogo (por ejemplo,
invalidar caché cuando se crea un producto), se importarían en el método
`ready()` de esta clase.

Autor: José Fica
Sección: AP-N4-C2
Año: 2026
==============================================================================
"""

from django.apps import AppConfig


class CatalogConfig(AppConfig):
    """
    Configuración de la app Catalog.

    Atributos:
        default_auto_field: Tipo de PK por defecto (BigAutoField).
        name: Ruta completa del módulo (apps.catalog).
        verbose_name: Nombre legible para el panel admin.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.catalog'
    verbose_name = 'Catálogo de Productos'

    # ------------------------------------------------------------------------
    # MÉTODO ready()
    # ------------------------------------------------------------------------
    # Se ejecuta cuando Django termina de cargar la app. Aquí se importarían
    # las señales si las tuvieras. Ejemplo:
    #
    #     def ready(self):
    #         import apps.catalog.signals  # noqa
    #
    # Como actualmente no hay señales en esta app, el método queda comentado.
    # ------------------------------------------------------------------------