"""
==============================================================================
SERVICIOS DEL CARRO DE COMPRAS
==============================================================================
Centraliza la lógica de negocio relacionada con el carro, separándola de
las vistas y serializers. Esto facilita:
    - Testeo unitario.
    - Reutilización desde distintos puntos (API, admin, tareas).
    - Mantenimiento del principio de responsabilidad única (SRP).

Operaciones:
    - get_or_create_active_cart(user)
    - add_product_to_cart(user, product, quantity)
    - update_item_quantity(user, item_id, quantity)
    - remove_item(user, item_id)
    - clear_cart(user)

IMPORTANTE: Ninguna de estas operaciones descuenta stock. El descuento
ocurre exclusivamente al confirmar el pago (ver apps/orders/services.py).

Autor: José Fica
Sección: AP-N4-C2
Año: 2026
==============================================================================
"""

from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.catalog.models import Product
from .models import Cart, CartItem


# =============================================================================
# SERVICIO: OBTENER O CREAR CARRITO ACTIVO
# =============================================================================
# Garantiza que el usuario SIEMPRE tenga un carro activo. Se llama en cada
# operación del carro. Si el usuario no tiene carro (porque es nuevo o
# porque acaba de hacer checkout), se crea uno vacío automáticamente.
# =============================================================================

def get_or_create_active_cart(user):
    """
    Obtiene el carro activo del usuario o lo crea si no existe.

    Nota de implementación:
        Como Cart.user es OneToOneField, cada usuario puede tener como
        máximo UN carro. Si el usuario tuvo un carro antes que fue eliminado
        por un checkout, esta función crea uno nuevo vacío. Si ya existe un
        carro activo, lo devuelve.

        NOTA: Se usa `get` + `except` en lugar de `get_or_create` porque
        `get_or_create(user=user)` fallaría si existiera un carro inactivo
        (porque la restricción OneToOne sobre user ya está ocupada).

    Args:
        user: Instancia de User autenticado.

    Returns:
        Cart: Carro activo del usuario.
    """
    try:
        cart = Cart.objects.get(user=user, is_active=True)
    except Cart.DoesNotExist:
        cart = Cart.objects.create(user=user, is_active=True)
    return cart


# =============================================================================
# VALIDACIÓN DE STOCK (PRIVADA)
# =============================================================================
# Función interna que valida si hay stock suficiente para la cantidad
# solicitada. NO descuenta stock. Se llama desde add_product_to_cart y
# update_item_quantity.
# =============================================================================

def _validate_stock_availability(product, requested_quantity):
    """
    Valida que el producto esté disponible y que la cantidad solicitada
    no supere el stock. NO descuenta stock.

    Args:
        product: Instancia de Product.
        requested_quantity: Cantidad a validar (int).

    Raises:
        ValidationError: Si el producto está inactivo, sin stock, o la
            cantidad solicitada excede el stock disponible.
    """
    if not product.is_active:
        raise ValidationError(
            {'product': f'El producto "{product.name}" no está disponible.'}
        )
    if product.stock <= 0:
        raise ValidationError(
            {'product': f'El producto "{product.name}" no tiene stock disponible.'}
        )
    if requested_quantity > product.stock:
        raise ValidationError(
            {'quantity': (
                f'Solo hay {product.stock} unidades disponibles de '
                f'"{product.name}".'
            )}
        )


# =============================================================================
# SERVICIO: AGREGAR PRODUCTO AL CARRITO
# =============================================================================
# Regla clave: si el producto ya está en el carro, se SUMA la cantidad en
# lugar de crear una fila duplicada. Esto es posible gracias a la
# restricción UNIQUE(cart, product) en el modelo CartItem.
# =============================================================================

@transaction.atomic
def add_product_to_cart(user, product, quantity=1):
    """
    Agrega un producto al carro del usuario.

    Reglas:
        - Si el producto ya está en el carro, se SUMA la cantidad.
        - Se valida stock antes de agregar (sin descontar).
        - Operación atómica: si algo falla, no se modifica el carro.

    Args:
        user: Usuario autenticado.
        product: Instancia de Product a agregar.
        quantity: Cantidad a agregar (por defecto 1).

    Returns:
        tuple: (cart, cart_item, created)
            - cart: instancia del carro.
            - cart_item: instancia del CartItem.
            - created: True si se creó, False si se actualizó.
    """
    cart = get_or_create_active_cart(user)

    # --- 1. Verificar si el producto ya está en el carro ---
    existing_item = CartItem.objects.filter(cart=cart, product=product).first()
    new_quantity = quantity + (existing_item.quantity if existing_item else 0)

    # --- 2. Validar stock para la cantidad TOTAL ---
    _validate_stock_availability(product, new_quantity)

    # --- 3. Actualizar o crear el ítem ---
    if existing_item:
        existing_item.quantity = new_quantity
        existing_item.save(update_fields=['quantity'])
        return cart, existing_item, False
    else:
        item = CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=quantity,
        )
        return cart, item, True


# =============================================================================
# SERVICIO: ACTUALIZAR CANTIDAD DE UN ÍTEM
# =============================================================================
# Solo se valida stock al AUMENTAR la cantidad. Reducirla siempre debe ser
# posible, incluso si el stock bajó por debajo de lo que hay en el carro:
# el usuario necesita poder ajustar su carro a la nueva realidad del stock.
# =============================================================================

@transaction.atomic
def update_item_quantity(user, item_id, quantity):
    """
    Actualiza la cantidad de un ítem existente en el carro del usuario.

    Regla de negocio:
        Solo se valida stock al AUMENTAR la cantidad. Reducirla siempre
        debe ser posible (por ejemplo, si el stock bajó a 0 mientras el
        usuario tenía 5 unidades en su carro, debe poder bajarlas a 1 o
        eliminarlas). El checkout revalida todo antes de generar la orden.

    Args:
        user: Usuario autenticado.
        item_id: ID del CartItem a modificar.
        quantity: Nueva cantidad (>= 1).

    Returns:
        CartItem: Ítem actualizado.

    Raises:
        ValidationError: Si el ítem no pertenece al usuario o la nueva
            cantidad excede el stock disponible (al aumentar).
    """
    # --- 1. Obtener el ítem verificando propiedad ---
    try:
        item = CartItem.objects.select_related('product', 'cart').get(
            id=item_id,
            cart__user=user,
            cart__is_active=True,
        )
    except CartItem.DoesNotExist:
        raise ValidationError({'item': 'Ítem no encontrado en tu carro.'})

    # --- 2. Validar stock SOLO al aumentar ---
    if quantity > item.quantity:
        _validate_stock_availability(item.product, quantity)

    # --- 3. Guardar ---
    item.quantity = quantity
    item.save(update_fields=['quantity'])
    return item


# =============================================================================
# SERVICIO: ELIMINAR UN ÍTEM
# =============================================================================
# Filtra por `cart__user=user` para que un usuario no pueda eliminar
# ítems de otro carro aunque conozca el ID.
# =============================================================================

@transaction.atomic
def remove_item(user, item_id):
    """
    Elimina un ítem del carro del usuario.

    Args:
        user: Usuario autenticado.
        item_id: ID del CartItem a eliminar.

    Returns:
        bool: True si se eliminó, False si no existía o no pertenecía.
    """
    deleted, _ = CartItem.objects.filter(
        id=item_id,
        cart__user=user,
        cart__is_active=True,
    ).delete()
    return deleted > 0


# =============================================================================
# SERVICIO: VACIAR EL CARRITO
# =============================================================================
# Elimina TODOS los ítems del carro en una sola query. Más eficiente que
# eliminar ítem por ítem desde el frontend.
# =============================================================================

@transaction.atomic
def clear_cart(user):
    """
    Elimina todos los ítems del carro activo del usuario.

    Args:
        user: Usuario autenticado.

    Returns:
        int: Cantidad de ítems eliminados.
    """
    cart = get_or_create_active_cart(user)
    deleted, _ = cart.items.all().delete()
    return deleted