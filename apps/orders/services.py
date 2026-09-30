"""
==============================================================================
SERVICIOS DE ÓRDENES - CHECKOUT Y GESTIÓN DE STOCK
==============================================================================
Este módulo contiene la lógica transaccional más crítica del sistema:

    1. checkout(user): convierte el carro activo en una Orden PENDIENTE.
    2. pay_order(order): descuenta stock y marca la orden como PAGADO.
    3. cancel_order(order): cancela la orden y repone stock si aplica.
    4. mark_as_delivered(order): marca la orden como ENTREGADO.

Todas las operaciones que afectan stock usan:
    - @transaction.atomic: garantiza atomicidad (todo o nada).
    - select_for_update(): bloqueo pesimista para evitar race conditions
      cuando dos usuarios intentan pagar el mismo producto a la vez.

IMPORTANTE: El stock NO se descuenta al agregar al carro, NI al hacer
checkout. Se descuenta ÚNICAMENTE al confirmar el pago (estado PAGADO).
Si la orden se cancela después de haber sido pagada, el stock se repone.

Autor: [Tu Nombre Completo]
Sección: [Tu Sección]
Año: [Año actual]
==============================================================================
"""

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.cart.models import Cart
from apps.catalog.models import Product
from .models import Order, OrderItem


# =============================================================================
# CHECKOUT: Carro → Orden PENDIENTE
# =============================================================================

@transaction.atomic
def checkout(user):
    """
    Convierte el carro activo del usuario en una Orden con estado PENDIENTE.

        Flujo:
        1. Obtiene el carro activo del usuario con sus ítems.
        2. Valida que el carro no esté vacío.
        3. Valida stock (sin descontar) de cada producto.
        4. Crea la Orden con total calculado.
        5. Crea los OrderItem con snapshot de nombre, SKU y precio.
        6. Elimina el carro (el historial vive en Order + OrderItem).

    Args:
        user: Usuario autenticado.

    Returns:
        Order: La orden recién creada en estado PENDIENTE.

    Raises:
        ValidationError: Si el carro está vacío o hay stock insuficiente.
    """
    # --- 1. Obtener carro activo con ítems y productos ---
    try:
        cart = Cart.objects.prefetch_related(
            'items__product'
        ).get(user=user, is_active=True)
    except Cart.DoesNotExist:
        raise ValidationError({'cart': 'No tienes un carro activo.'})

    items = list(cart.items.select_related('product').all())

    # --- 2. Validar carro no vacío ---
    if not items:
        raise ValidationError({'cart': 'Tu carro está vacío.'})

    # --- 3. Validar stock SIN descontar ---
    # Bloqueamos las filas de producto para asegurar consistencia durante
    # la validación. Esto evita que otro proceso modifique el stock
    # mientras hacemos el checkout.
    product_ids = [item.product_id for item in items]
    locked_products = {
        p.id: p for p in Product.objects.select_for_update().filter(id__in=product_ids)
    }

    errors = []
    for item in items:
        product = locked_products[item.product_id]
        if not product.is_active:
            errors.append(f'El producto "{product.name}" ya no está disponible.')
        elif item.quantity > product.stock:
            errors.append(
                f'Stock insuficiente para "{product.name}": '
                f'solicitaste {item.quantity} pero solo hay {product.stock}.'
            )

    if errors:
        raise ValidationError({'stock': errors})

    # --- 4. Crear la Orden ---
    total = sum(item.subtotal for item in items)
    order = Order.objects.create(
        user=user,
        status=Order.Status.PENDIENTE,
        total=total,
    )

    # --- 5. Crear los OrderItem con snapshot de precios ---
    order_items = [
        OrderItem(
            order=order,
            product=item.product,
            product_name=item.product.name,
            product_sku=item.product.sku,
            quantity=item.quantity,
            unit_price=item.product.price,
            subtotal=item.subtotal,
        )
        for item in items
    ]
    OrderItem.objects.bulk_create(order_items)

    # --- 6. Cerrar el carro (histórico) ---
        # --- 6. Cerrar el carro ---
    # NOTA DE DISEÑO:
    # Como Cart.user es OneToOneField (relación 1:1 con User), no podemos
    # tener dos carros por usuario (uno activo + uno cerrado). Por eso
    # ELIMINAMOS el carro tras el checkout. El historial de la compra queda
    # preservado en Order + OrderItem (con snapshot de precios, nombres y
    # cantidades).
    #
    # El próximo request a /api/cart/ creará automáticamente un carro nuevo
    # vacío gracias a get_or_create_active_cart() en apps/cart/services.py.
    cart.delete()

    return order


# =============================================================================
# PAGO: PENDIENTE → PAGADO (descuenta stock)
# =============================================================================

@transaction.atomic
def pay_order(order):
    """
    Marca la orden como PAGADA y descuenta el stock de cada producto.

    Flujo:
        1. Valida que la orden esté en estado PENDIENTE.
        2. Bloquea los productos con select_for_update().
        3. Revalida stock (pudo haber cambiado desde el checkout).
        4. Descuenta stock de cada producto.
        5. Actualiza la orden a PAGADO + paid_at.

    IMPORTANTE: Este es el ÚNICO punto donde se descuenta stock.

    Args:
        order: Instancia de Order.

    Returns:
        Order: La orden actualizada.

    Raises:
        ValidationError: Si la orden no está PENDIENTE o el stock es
            insuficiente al momento de pagar.
    """
    # --- 1. Validar estado ---
    if order.status != Order.Status.PENDIENTE:
        raise ValidationError(
            {'status': f'No se puede pagar una orden en estado {order.get_status_display()}.'}
        )

    # --- 2. Bloquear productos (evita race conditions) ---
    items = list(order.items.select_related('product').all())
    product_ids = [item.product_id for item in items]

    locked_products = {
        p.id: p
        for p in Product.objects.select_for_update().filter(id__in=product_ids)
    }

    # --- 3. Revalidar stock ---
    errors = []
    for item in items:
        product = locked_products[item.product_id]
        if not product.is_active:
            errors.append(f'El producto "{product.name}" fue desactivado.')
        elif item.quantity > product.stock:
            errors.append(
                f'Stock insuficiente para "{product.name}": '
                f'disponible {product.stock}, requerido {item.quantity}.'
            )

    if errors:
        raise ValidationError({'stock': errors})

    # --- 4. Descontar stock ---
    for item in items:
        product = locked_products[item.product_id]
        product.stock -= item.quantity
        product.save(update_fields=['stock', 'updated_at'])

    # --- 5. Actualizar orden ---
    order.status = Order.Status.PAGADO
    order.paid_at = timezone.now()
    order.save(update_fields=['status', 'paid_at', 'updated_at'])

    return order


# =============================================================================
# CANCELACIÓN: * → CANCELADO (repone stock si venía de PAGADO)
# =============================================================================

@transaction.atomic
def cancel_order(order):
    """
    Cancela la orden. Si estaba en estado PAGADO, repone el stock.

    Flujo:
        1. Valida que la orden se pueda cancelar (PENDIENTE o PAGADO).
        2. Si estaba PAGADO, repone stock con select_for_update().
        3. Actualiza la orden a CANCELADO + cancelled_at.

    Args:
        order: Instancia de Order.

    Returns:
        Order: La orden actualizada.

    Raises:
        ValidationError: Si la orden está ENTREGADO o ya CANCELADO.
    """
    # --- 1. Validar transición ---
    if order.status not in (Order.Status.PENDIENTE, Order.Status.PAGADO):
        raise ValidationError(
            {'status': f'No se puede cancelar una orden en estado {order.get_status_display()}.'}
        )

    # --- 2. Reponer stock si venía de PAGADO ---
    if order.status == Order.Status.PAGADO:
        items = list(order.items.all())
        product_ids = [item.product_id for item in items]

        locked_products = {
            p.id: p
            for p in Product.objects.select_for_update().filter(id__in=product_ids)
        }

        for item in items:
            product = locked_products[item.product_id]
            product.stock += item.quantity
            product.save(update_fields=['stock', 'updated_at'])

    # --- 3. Actualizar orden ---
    order.status = Order.Status.CANCELADO
    order.cancelled_at = timezone.now()
    order.save(update_fields=['status', 'cancelled_at', 'updated_at'])

    return order


# =============================================================================
# ENTREGA: PAGADO → ENTREGADO
# =============================================================================

@transaction.atomic
def mark_as_delivered(order):
    """
    Marca una orden PAGADA como ENTREGADO (estado final).

    Args:
        order: Instancia de Order.

    Returns:
        Order: La orden actualizada.

    Raises:
        ValidationError: Si la orden no está PAGADO.
    """
    if order.status != Order.Status.PAGADO:
        raise ValidationError(
            {'status': (
                f'Solo se pueden entregar órdenes PAGADAS. '
                f'Estado actual: {order.get_status_display()}.'
            )}
        )

    order.status = Order.Status.ENTREGADO
    order.save(update_fields=['status', 'updated_at'])
    return order


# =============================================================================
# UTILIDAD: cambiar_estado (dispatcher)
# =============================================================================

def change_order_status(order, new_status):
    """
    Despachador central de cambios de estado.

    Valida la transición y llama al servicio correspondiente.

    Args:
        order: Instancia de Order.
        new_status: Estado destino (str).

    Returns:
        Order: La orden actualizada.

    Raises:
        ValidationError: Si la transición no es válida.
    """
    if not order.can_transition_to(new_status):
        raise ValidationError(
            {'status': (
                f'Transición inválida: {order.get_status_display()} → '
                f'{dict(Order.Status.choices).get(new_status, new_status)}.'
            )}
        )

    if new_status == Order.Status.PAGADO:
        return pay_order(order)
    elif new_status == Order.Status.CANCELADO:
        return cancel_order(order)
    elif new_status == Order.Status.ENTREGADO:
        return mark_as_delivered(order)

    raise ValidationError({'status': 'Estado no reconocido.'})