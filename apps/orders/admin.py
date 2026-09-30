"""
==============================================================================
ADMIN DE ÓRDENES
==============================================================================
Configura el panel de administración de Django para Order y OrderItem.

Características:
    - Vista de orden con ítems embebidos (OrderItemInline).
    - Filtros por estado y fechas (created_at, paid_at).
    - Jerarquía por fecha de creación (date_hierarchy).
    - Campos readonly: order_number, timestamps, ítems.
    - Los ítems NO son editables desde el admin (preservan snapshot).

Nota: el admin nativo de Django es complementario al panel admin
personalizado del frontend. Aquí se prioriza la vista de auditoría
sobre la edición de datos históricos.

Autor: José Fica
Sección: AP-N4-C2
Año: 2026
==============================================================================
"""

from django.contrib import admin

from .models import Order, OrderItem


# =============================================================================
# INLINE: ÍTEMS DE LA ORDEN
# =============================================================================
# Muestra los OrderItem embebidos en la vista de la orden. Todos los campos
# son readonly porque representan un snapshot histórico (no deben editarse).
# can_delete=False impide eliminar ítems desde el admin: si una orden está
# mal, se cancela completa, no se edita línea por línea.
# =============================================================================

class OrderItemInline(admin.TabularInline):
    """
    Muestra los ítems de la orden embebidos en la vista de la orden.

    Configuración:
        - model: OrderItem (modelo relacionado).
        - extra: 0 (no mostrar formularios vacíos).
        - readonly_fields: todos los campos del snapshot (no editables).
        - can_delete: False (los ítems no se pueden eliminar individualmente).
    """
    model = OrderItem
    extra = 0
    readonly_fields = (
        'product', 'product_name', 'product_sku',
        'quantity', 'unit_price', 'subtotal',
    )
    can_delete = False


# =============================================================================
# ADMIN: ORDEN
# =============================================================================
# Vista principal de auditoría y gestión de órdenes.
#
# Columnas mostradas:
#     - order_number: UUID público.
#     - user: cliente que hizo la compra.
#     - status: PENDIENTE / PAGADO / ENTREGADO / CANCELADO.
#     - total: monto total en CLP.
#     - created_at: cuándo se creó la orden.
#     - paid_at: cuándo se pagó (null si no se ha pagado).
#
# Filtros:
#     - status, created_at, paid_at.
#
# Búsqueda:
#     - order_number, user__username, user__email.
#
# Date hierarchy:
#     - Navegación por año/mes/día sobre created_at.
# =============================================================================

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo Order.

    Los campos readonly garantizan que el admin no modifique datos
    críticos accidentalmente. Los cambios de estado se hacen desde el
    endpoint `PATCH /api/orders/{uuid}/status/`, no desde el admin.
    """
    list_display = ('order_number', 'user', 'status', 'total', 'created_at', 'paid_at')
    list_filter = ('status', 'created_at', 'paid_at')
    search_fields = ('order_number', 'user__username', 'user__email')
    readonly_fields = (
        'order_number', 'created_at', 'updated_at',
        'paid_at', 'cancelled_at',
    )
    inlines = [OrderItemInline]
    date_hierarchy = 'created_at'


# =============================================================================
# ADMIN: ÍTEM DE ORDEN
# =============================================================================
# Vista alternativa para inspeccionar ítems individualmente (sin navegar
# por la orden). Útil para responder consultas como: "¿qué órdenes
# incluyen el producto X?" o "¿cuántas unidades del SKU Y se han vendido?".
#
# Todos los campos son readonly: son un snapshot histórico.
# =============================================================================

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo OrderItem.

    Búsqueda por nombre de producto, SKU y número de orden. Filtro por
    estado de la orden asociada.

    Todos los campos son de solo lectura porque el OrderItem es inmutable
    (snapshot del momento de la compra).
    """
    list_display = ('id', 'order', 'product_name', 'quantity', 'unit_price', 'subtotal')
    list_filter = ('order__status',)
    search_fields = ('product_name', 'product_sku', 'order__order_number')
    readonly_fields = (
        'order', 'product', 'product_name', 'product_sku',
        'quantity', 'unit_price', 'subtotal',
    )