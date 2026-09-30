"""
==============================================================================
MÓDULO DE MODELOS - ÓRDENES Y TRANSACCIONES
==============================================================================
Define las entidades que representan el ciclo de vida de una compra:
Order (cabecera histórica) y OrderItem (detalle con precios congelados).

Diseño normalizado (3FN):
    - Order almacena la cabecera de la transacción (usuario, estado, total).
    - OrderItem almacena el detalle (producto, cantidad, precio histórico).
    - El precio se congela en OrderItem para evitar dependencias con el
      catálogo actual: si el precio del producto cambia, la orden histórica
      no se ve afectada.

Máquina de estados de la Orden (CHOICES):
    PENDIENTE → PAGADO → ENTREGADO
        ↓
    CANCELADO

Reglas de negocio críticas:
    1. El stock se descuenta ÚNICAMENTE al pasar a estado PAGADO.
    2. Si el stock es insuficiente al pagar, la transacción se rechaza.
    3. Si la orden pasa a CANCELADO, el stock descontado se repone.

Autor: [Tu Nombre Completo]
Sección: [Tu Sección]
Año: [Año actual]
==============================================================================
"""

import uuid

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class Order(models.Model):
    """
    Representa una orden de compra generada a partir del checkout de un carro.

    Cada orden es un registro histórico e inmutable en cuanto a sus ítems:
    el detalle (OrderItem) conserva los precios del momento de la compra.
    """

    # ------------------------------------------------------------------
    # CHOICES: Máquina de estados de la orden.
    # Se define como TextChoices para agrupar las constantes del dominio
    # y permitir consultas legibles (Order.Status.PAGADO).
    # ------------------------------------------------------------------
    class Status(models.TextChoices):
        """
        Estados posibles de una orden a lo largo de su ciclo de vida.

        Flujo normal:
            PENDIENTE → PAGADO → ENTREGADO

        Flujo alternativo:
            PENDIENTE → CANCELADO
            PAGADO    → CANCELADO (repone stock)
        """
        PENDIENTE = 'PENDIENTE', _('Pendiente de pago')
        PAGADO = 'PAGADO', _('Pagado')
        ENTREGADO = 'ENTREGADO', _('Entregado')
        CANCELADO = 'CANCELADO', _('Cancelado')

    # ------------------------------------------------------------------
    # ATRIBUTO: order_number
    # Identificador público único de la orden (UUID4) para exponer en la API
    # sin revelar la PK interna. Evita enumeración de órdenes.
    # ------------------------------------------------------------------
    order_number = models.UUIDField(
        _('Número de orden'),
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text=_('Identificador público único de la orden (UUID4).'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,       # No se puede borrar usuario con órdenes
        related_name='orders',
        verbose_name=_('Usuario'),
    )

    status = models.CharField(
        _('Estado'),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDIENTE,
        db_index=True,
        help_text=_('Estado actual de la orden en su ciclo de vida.'),
    )

    total = models.DecimalField(
        _('Total (CLP)'),
        max_digits=14,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text=_('Monto total de la orden al momento del checkout.'),
    )

    # ------------------------------------------------------------------
    # Timestamps del ciclo de vida
    # ------------------------------------------------------------------
    created_at = models.DateTimeField(
        _('Fecha de creación'),
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        _('Última actualización'),
        auto_now=True,
    )
    paid_at = models.DateTimeField(
        _('Fecha de pago'),
        null=True,
        blank=True,
        help_text=_('Se completa al pasar a estado PAGADO.'),
    )
    cancelled_at = models.DateTimeField(
        _('Fecha de cancelación'),
        null=True,
        blank=True,
        help_text=_('Se completa al pasar a estado CANCELADO.'),
    )

    class Meta:
        db_table = 'orders_order'
        verbose_name = _('Orden')
        verbose_name_plural = _('Órdenes')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['order_number']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f'Orden {self.order_number} - {self.get_status_display()}'

    @property
    def total_items(self):
        """Cantidad total de unidades en la orden."""
        return sum(item.quantity for item in self.items.all())

    def can_transition_to(self, new_status):
        """
        Valida si la orden puede transicionar al nuevo estado.

        Reglas:
            - PENDIENTE → PAGADO o CANCELADO
            - PAGADO → ENTREGADO o CANCELADO
            - ENTREGADO → (estado final)
            - CANCELADO → (estado final)

        Args:
            new_status (str): Estado destino.

        Returns:
            bool: True si la transición es válida.
        """
        valid_transitions = {
            self.Status.PENDIENTE: {self.Status.PAGADO, self.Status.CANCELADO},
            self.Status.PAGADO: {self.Status.ENTREGADO, self.Status.CANCELADO},
            self.Status.ENTREGADO: set(),
            self.Status.CANCELADO: set(),
        }
        return new_status in valid_transitions.get(self.status, set())


class OrderItem(models.Model):
    """
    Representa una línea de detalle de una orden.

    IMPORTANTE: 'unit_price' es un snapshot histórico del precio del
    producto al momento del checkout. Esto garantiza que cambios futuros
    en el catálogo no alteren órdenes ya generadas (cumple 3FN al no
    depender del precio actual del producto).
    """

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Orden'),
    )
    product = models.ForeignKey(
        'catalog.Product',
        on_delete=models.PROTECT,       # Preserva histórico aunque se borre el producto
        related_name='order_items',
        verbose_name=_('Producto'),
    )
    product_name = models.CharField(
        _('Nombre del producto (snapshot)'),
        max_length=200,
        help_text=_('Nombre del producto al momento de la compra.'),
    )
    product_sku = models.CharField(
        _('SKU (snapshot)'),
        max_length=50,
        help_text=_('SKU del producto al momento de la compra.'),
    )
    quantity = models.PositiveIntegerField(
        _('Cantidad'),
        validators=[MinValueValidator(1)],
    )
    unit_price = models.DecimalField(
        _('Precio unitario (snapshot)'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text=_('Precio del producto congelado al momento del checkout.'),
    )
    subtotal = models.DecimalField(
        _('Subtotal'),
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text=_('unit_price × quantity (almacenado para consultas rápidas).'),
    )

    class Meta:
        db_table = 'orders_orderitem'
        verbose_name = _('Ítem de orden')
        verbose_name_plural = _('Ítems de orden')
        ordering = ['id']

    def __str__(self):
        return f'{self.quantity} x {self.product_name}'

    def save(self, *args, **kwargs):
        """
        Calcula automáticamente el subtotal antes de guardar.
        """
        self.subtotal = self.unit_price * self.quantity
        super().save(*args, **kwargs)