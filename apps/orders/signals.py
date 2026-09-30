"""
==============================================================================
SEÑALES DE ÓRDENES
==============================================================================
Define las señales que reaccionan a eventos del ciclo de vida de las
órdenes. Se usan principalmente para auditoría: registrar cuándo se crea
una orden y cuándo cambia de estado.

Señales implementadas:
    1. log_order_status_change (pre_save):
       Detecta y registra cambios de estado comparando el estado anterior
       (desde la BD) con el nuevo (en memoria).

    2. log_order_created (post_save):
       Registra en el log la creación de una nueva orden.

Consideraciones técnicas:
    - Se usa `logging` para no acoplar la lógica de notificación a la
      lógica de negocio. En el futuro, aquí se podrían enviar emails o
      notificaciones push cuando una orden cambia de estado.
    - pre_save se ejecuta ANTES de guardar: permite comparar el estado
      anterior (BD) con el nuevo (instancia).
    - post_save se ejecuta DESPUÉS de guardar: la orden ya está en BD.

Autor: José Fica
Sección: AP-N4-C2
Año: 2026
==============================================================================
"""

import logging

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Order

logger = logging.getLogger(__name__)


# =============================================================================
# SEÑAL 1: LOG DE CAMBIO DE ESTADO
# =============================================================================
# pre_save se ejecuta ANTES de que la orden se guarde en la BD. Esto permite
# comparar el estado ANTERIOR (cargado desde la BD) con el NUEVO y detectar
# si hubo un cambio.
#
# Importante:
#     - Se usa `_state.adding` para detectar si es una creación (no hay
#       estado anterior que comparar).
#     - Se usa try/except por si la orden aún no existe en la BD.
#     - Se usa `.only('status')` para traer solo el campo necesario y
#       reducir el payload de la query.
# =============================================================================

@receiver(pre_save, sender=Order)
def log_order_status_change(sender, instance, **kwargs):
    """
    Detecta y registra cambios de estado en una orden.

    Se ejecuta ANTES de guardar la orden, comparando el estado anterior
    (desde la BD) con el nuevo (instancia en memoria). Si difieren, loggea
    el cambio.

    Args:
        sender: Modelo que dispara la señal (Order).
        instance: Instancia de la orden a guardar.
        **kwargs: Argumentos adicionales.
    """
    # Si es una creación, no hay estado anterior que comparar
    if instance._state.adding:
        return

    # Intentar cargar el estado anterior desde la BD
    try:
        old_order = Order.objects.only('status').get(pk=instance.pk)
    except Order.DoesNotExist:
        return

    # Comparar y loggear si cambió
    if old_order.status != instance.status:
        logger.info(
            f'[SIGNAL-ORDER] Cambio de estado en orden '
            f'{instance.order_number}: {old_order.status} → {instance.status}'
        )


# =============================================================================
# SEÑAL 2: LOG DE CREACIÓN DE ORDEN
# =============================================================================
# post_save se ejecuta DESPUÉS de guardar la orden. Se usa `created=True`
# para registrar solo cuando la orden se crea por primera vez (no en cada
# actualización de estado).
# =============================================================================

@receiver(post_save, sender=Order)
def log_order_created(sender, instance, created, **kwargs):
    """
    Registra en el log la creación de una nueva orden.

    Args:
        sender: Modelo que dispara la señal (Order).
        instance: Instancia de la orden.
        created (bool): True si es un INSERT, False si es un UPDATE.
        **kwargs: Argumentos adicionales.
    """
    if created:
        logger.info(
            f'[SIGNAL-ORDER] Nueva orden creada: {instance.order_number} | '
            f'Usuario: {instance.user.username} | '
            f'Total: ${instance.total} | '
            f'Estado inicial: {instance.status}'
        )