"""
==============================================================================
SERIALIZERS DE ÓRDENES
==============================================================================
Define los serializers para exponer órdenes y sus ítems, y para recibir
el cambio de estado desde la API.

Serializers:
    - OrderItemSerializer: lectura del detalle de la orden.
    - OrderSerializer: lectura completa de la orden.
    - OrderListSerializer: versión ligera para listados.
    - ChangeStatusSerializer: entrada para cambiar estado.
    - CheckoutResponseSerializer: respuesta del checkout.

Autor: [Tu Nombre Completo]
Sección: [Tu Sección]
Año: [Año actual]
==============================================================================
"""

from rest_framework import serializers

from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer de LECTURA de un ítem de orden (snapshot histórico)."""

    class Meta:
        model = OrderItem
        fields = (
            'id', 'product', 'product_name', 'product_sku',
            'quantity', 'unit_price', 'subtotal',
        )
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer COMPLETO de una orden (con ítems anidados y totales).
    """

    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    total_items = serializers.IntegerField(read_only=True)

    class Meta:
        model = Order
        fields = (
            'id', 'order_number', 'username', 'status', 'status_display',
            'items', 'total_items', 'total',
            'created_at', 'updated_at', 'paid_at', 'cancelled_at',
        )
        read_only_fields = fields


class OrderListSerializer(serializers.ModelSerializer):
    """Serializer LIGERO para listados (sin ítems)."""

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    total_items = serializers.IntegerField(read_only=True)

    class Meta:
        model = Order
        fields = (
            'id', 'order_number', 'status', 'status_display',
            'total_items', 'total', 'created_at',
        )
        read_only_fields = fields


class ChangeStatusSerializer(serializers.Serializer):
    """
    Serializer de ENTRADA para cambiar el estado de una orden.

    Solo acepta valores válidos del enum Order.Status.
    """

    status = serializers.ChoiceField(
        choices=Order.Status.choices,
        required=True,
        help_text='Nuevo estado de la orden.',
    )


class CheckoutResponseSerializer(serializers.Serializer):
    """Serializer de RESPUESTA del endpoint de checkout."""

    message = serializers.CharField()
    order = OrderSerializer()