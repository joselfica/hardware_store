"""
==============================================================================
MÓDULO DE MODELOS - CARRO DE COMPRAS PERSISTENTE
==============================================================================
Define la estructura del carro de compras, que debe persistir en PostgreSQL
incluso después de que el usuario cierre sesión (logout) o cambie de
dispositivo.

Diseño normalizado (3FN):
    - Relación 1:1 entre User y Cart: cada usuario tiene un único carro
      activo. Se implementa con OneToOneField.
    - Relación 1:N entre Cart y CartItem: un carro contiene múltiples ítems.
    - Restricción UNIQUE compuesta (cart, product): evita duplicados del
      mismo producto en el mismo carro.

Notas de negocio:
    - El stock NO se descuenta al agregar ítems al carro.
    - El carro es histórico: al hacer checkout, se marca is_active=False y
      se crea un nuevo carro vacío para el usuario.

Autor: [Tu Nombre Completo]
Sección: [Tu Sección]
Año: [Año actual]
==============================================================================
"""

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class Cart(models.Model):
    """
    Representa el carro de compras activo de un usuario.

    Se vincula mediante OneToOneField con User para garantizar que cada
    usuario tenga exactamente un carro activo en la base de datos.
    La persistencia en PostgreSQL asegura que los ítems se conserven entre
    sesiones y dispositivos.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart',
        verbose_name=_('Usuario'),
        help_text=_('Usuario propietario del carro (relación 1:1).'),
    )
    is_active = models.BooleanField(
        _('Activo'),
        default=True,
        help_text=_(
            'Indica si el carro está abierto para agregar ítems. '
            'Al hacer checkout se marca como False y se crea uno nuevo.'
        ),
    )
    created_at = models.DateTimeField(
        _('Fecha de creación'),
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        _('Última actualización'),
        auto_now=True,
    )

    class Meta:
        db_table = 'cart_cart'
        verbose_name = _('Carro de compras')
        verbose_name_plural = _('Carros de compras')
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
        ]

    def __str__(self):
        return f'Carro de {self.user.username} ({"activo" if self.is_active else "cerrado"})'

    @property
    def total_items(self):
        """Cantidad total de unidades (suma de cantidades) en el carro."""
        return sum(item.quantity for item in self.items.all())

    @property
    def total_price(self):
        """
        Monto total del carro en CLP.
        Se calcula en tiempo de ejecución (no se almacena) para mantener 3FN
        y evitar inconsistencias si cambian los precios del catálogo.
        """
        return sum(item.subtotal for item in self.items.all())


class CartItem(models.Model):
    """
    Representa un ítem individual dentro del carro de compras.

    Restricciones:
        - UNIQUE(cart, product): evita que el mismo producto aparezca
          duplicado en el carro; si el usuario agrega de nuevo, se
          incrementa la cantidad.
    """

    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Carro'),
    )
    product = models.ForeignKey(
        'catalog.Product',
        on_delete=models.CASCADE,
        related_name='cart_items',
        verbose_name=_('Producto'),
    )
    quantity = models.PositiveIntegerField(
        _('Cantidad'),
        default=1,
        validators=[MinValueValidator(1)],
        help_text=_('Cantidad de unidades solicitadas.'),
    )
    added_at = models.DateTimeField(
        _('Fecha de agregado'),
        auto_now_add=True,
    )

    class Meta:
        db_table = 'cart_cartitem'
        verbose_name = _('Ítem del carro')
        verbose_name_plural = _('Ítems del carro')
        ordering = ['added_at']
        constraints = [
            models.UniqueConstraint(
                fields=['cart', 'product'],
                name='unique_product_per_cart',
            ),
        ]
        indexes = [
            models.Index(fields=['cart', 'product']),
        ]

    def __str__(self):
        return f'{self.quantity} x {self.product.name}'

    @property
    def subtotal(self):
        """Subtotal del ítem: precio unitario × cantidad."""
        return self.product.price * self.quantity