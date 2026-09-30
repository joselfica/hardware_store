"""
==============================================================================
ADMIN DEL CARRO DE COMPRAS
==============================================================================
Configura el panel de administración de Django para inspeccionar los
carros activos y sus ítems. Es útil para depuración y soporte técnico:
permite ver qué productos tiene cada usuario en su carro sin consultar
la base de datos manualmente.

Modelos registrados:
    - Cart: cabecera del carro (usuario, estado, totales).
    - CartItem: ítems individuales del carro (producto, cantidad).

Optimizaciones:
    - CartItemInline permite ver y editar los ítems embebidos en la
      vista del carro (una sola página en lugar de navegar a otra).
    - list_display muestra solo las columnas relevantes para no saturar.

Autor: José Fica
Sección: AP-N4-C2
Año: 2026
==============================================================================
"""

from django.contrib import admin

from .models import Cart, CartItem


# =============================================================================
# INLINE: ÍTEMS DEL CARRO
# =============================================================================
# TabularInline muestra los ítems como una tabla embebida en la vista del
# carro. `extra = 0` evita que Django muestre filas vacías para agregar
# ítems manualmente (los ítems se crean desde la API, no desde el admin).
# =============================================================================

class CartItemInline(admin.TabularInline):
    """
    Muestra los ítems del carro embebidos en la vista del carro.

    Configuración:
        model: Modelo relacionado (CartItem).
        extra: Filas vacías adicionales (0 = no mostrar formularios vacíos).
        readonly_fields: Campos que no se pueden editar desde el admin.
    """
    model = CartItem
    extra = 0
    readonly_fields = ('added_at',)


# =============================================================================
# ADMIN: CARRITO
# =============================================================================
# Vista principal para inspeccionar carros. Muestra el usuario dueño, su
# estado (activo/cerrado), los totales calculados y la fecha de última
# modificación. Incluye los ítems embebidos.
# =============================================================================

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo Cart.

    Columnas mostradas:
        - id: PK del carro.
        - user: usuario dueño del carro.
        - is_active: si el carro está activo o cerrado.
        - total_items: cantidad total de unidades (property).
        - total_price: monto total en CLP (property).
        - updated_at: última modificación del carro.

    Filtros:
        - is_active: filtrar por carros activos/cerrados.

    Búsqueda:
        - user__username: buscar por nombre de usuario.
        - user__email: buscar por email.
    """
    list_display = ('id', 'user', 'is_active', 'total_items', 'total_price', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('user__username', 'user__email')
    inlines = [CartItemInline]
    readonly_fields = ('created_at', 'updated_at')


# =============================================================================
# ADMIN: ÍTEM DEL CARRITO
# =============================================================================
# Vista alternativa para inspeccionar ítems de forma individual (sin
# navegar por el carro). Útil para responder preguntas como "¿qué usuarios
# tienen el producto X en su carro?".
# =============================================================================

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo CartItem.

    Columnas mostradas:
        - id, cart, product, quantity, subtotal (property), added_at.

    Filtros:
        - added_at: filtrar por fecha de agregado.

    Búsqueda:
        - product__name: buscar por nombre del producto.
        - product__sku: buscar por SKU.
        - cart__user__username: buscar por usuario dueño del carro.
    """
    list_display = ('id', 'cart', 'product', 'quantity', 'subtotal', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('product__name', 'product__sku', 'cart__user__username')
    readonly_fields = ('added_at',)