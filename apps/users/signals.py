"""
==============================================================================
SEÑALES DE USUARIOS
==============================================================================
Define las señales (signals) que reaccionan a eventos del ciclo de vida de
los usuarios. Las señales permiten desacoplar la lógica de reacción del
flujo principal: el registro de un usuario no necesita saber que se le debe
crear un carro; una señal lo hace automáticamente.

Señales implementadas:
    1. create_cart_for_new_user (post_save):
       Crea un carro vacío cuando se registra un usuario nuevo.
       Mejora la UX porque el frontend puede agregar productos sin que
       el backend tenga que crear el carro en el primer request.

    2. log_new_user (post_save):
       Registra en el log la creación de un usuario nuevo.
       Útil para auditoría y monitoreo.

Consideraciones técnicas:
    - Se usa `logging` en lugar de `print` para respetar la configuración
      de logs de Django (niveles, handlers, formatters).
    - Los imports locales (dentro de las funciones) evitan circular imports:
      `users` no debe importar `cart` al cargar, sino solo cuando se
      dispara la señal.
    - Se usa `created=True` para filtrar y ejecutar solo en creación,
      no en cada actualización del usuario.

Autor: José Fica
Sección: AP-N4-C2
Año: 2026
==============================================================================
"""

import logging

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


# =============================================================================
# SEÑAL 1: CREAR CARRO VACÍO AL REGISTRAR UN USUARIO
# =============================================================================
# Cuando se crea un usuario (created=True), se crea automáticamente su
# carro vacío. Esto mejora la UX porque el usuario puede agregar productos
# inmediatamente sin que el backend tenga que crear el carro en el primer
# request a /api/cart/.
#
# Importante:
#     - Se filtra por created=True para evitar crear carros en cada
#       actualización del usuario (cambio de email, last_login, etc.).
#     - Import local de Cart para evitar circular imports: `users` no
#       debe depender de `cart` en tiempo de carga del módulo.
#     - Se usa get_or_create por idempotencia: si por algún motivo la
#       señal se dispara dos veces, no crea duplicados.
# =============================================================================

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_cart_for_new_user(sender, instance, created, **kwargs):
    """
    Crea un carro vacío automáticamente cuando se registra un usuario nuevo.

    Args:
        sender: Modelo que dispara la señal (User).
        instance: Instancia del usuario creado o actualizado.
        created (bool): True si es un INSERT, False si es un UPDATE.
        **kwargs: Argumentos adicionales de la señal.
    """
    # Solo actuar en creación, no en cada save
    if not created:
        return

    # Import local para evitar circular imports
    from apps.cart.models import Cart

    # get_or_create para idempotencia (evita duplicados si la señal se
    # dispara dos veces por algún motivo)
    cart, cart_created = Cart.objects.get_or_create(
        user=instance,
        defaults={'is_active': True},
    )

    if cart_created:
        logger.info(
            f'[SIGNAL-USER] Carro creado automáticamente para '
            f'"{instance.username}" (cart_id={cart.id})'
        )


# =============================================================================
# SEÑAL 2: LOG DE AUDITORÍA AL CREAR UN USUARIO
# =============================================================================
# Registra en el log la creación de cada usuario nuevo. Útil para:
#     - Auditoría: ¿quién se registró y cuándo?
#     - Detección de registros masivos (spam, bots).
#     - Debugging en producción cuando no hay acceso directo a la BD.
# =============================================================================

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def log_new_user(sender, instance, created, **kwargs):
    """
    Registra en el log la creación de un usuario nuevo.

    Args:
        sender: Modelo que dispara la señal (User).
        instance: Instancia del usuario.
        created (bool): True si es un INSERT, False si es un UPDATE.
        **kwargs: Argumentos adicionales.
    """
    if created:
        logger.info(
            f'[SIGNAL-USER] Nuevo usuario registrado: "{instance.username}" | '
            f'Rol: {instance.role} | Email: {instance.email or "(sin email)"}'
        )