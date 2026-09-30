"""
==============================================================================
CONFIGURACIÓN DE LA APP USERS
==============================================================================
Define la configuración de la aplicación 'users' (gestión de usuarios y
autenticación JWT).

Señales conectadas (en el método ready()):
    - create_cart_for_new_user: crea un carro vacío al registrar un usuario.
    - log_new_user: registra en el log la creación de usuarios nuevos.

Autor: José Fica
Sección: AP-N4-C2
Año: 2026
==============================================================================
"""

from django.apps import AppConfig


class UsersConfig(AppConfig):
    """
    Configuración de la app Users.

    Atributos:
        default_auto_field: Tipo de PK por defecto (BigAutoField).
        name: Ruta completa del módulo (apps.users).
        verbose_name: Nombre legible para el panel admin.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'
    verbose_name = 'Gestión de Usuarios'

    def ready(self):
        """
        Se ejecuta cuando Django termina de cargar la app.

        Importa las señales para que se registren con Django. El import
        debe estar DENTRO del método para evitar problemas de carga
        temprana (los modelos aún no están listos al importar apps.py).

        El comentario `# noqa: F401` le dice a los linters que ignore el
        warning de "import no usado", porque el import tiene un efecto
        secundario (registrar la señal).
        """
        import apps.users.signals  # noqa: F401