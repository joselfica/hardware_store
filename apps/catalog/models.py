"""
==============================================================================
MÓDULO DE MODELOS - CATÁLOGO DE PRODUCTOS
==============================================================================
Define las entidades relacionadas con el catálogo de componentes informáticos:
Categorías, Marcas y Productos. El diseño sigue estrictamente las tres
primeras formas normales para evitar redundancia y anomalías de actualización.

Justificación 3FN:
    - 1FN: Todos los campos son atómicos (sin listas, sin JSON embebido).
    - 2FN: Cada atributo depende de la PK completa de su tabla.
    - 3FN: Se eliminaron dependencias transitivas creando entidades
           independientes para 'Category' y 'Brand'. Así, el nombre de la
           marca no se repite en cada producto; si la marca cambia de
           nombre, solo se actualiza un registro.

Autor: [Tu Nombre Completo]
Sección: [Tu Sección]
Año: [Año actual]
==============================================================================
"""

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class Category(models.Model):
    """
    Representa una categoría del catálogo (ej: Procesadores, Tarjetas de
    Video, Memorias RAM, Almacenamiento, Fuentes de Poder).

    Se modela como entidad independiente para cumplir 3FN: el nombre de la
    categoría no se duplica en cada producto, sino que se referencia
    mediante FK.
    """

    name = models.CharField(
        _('Nombre de la categoría'),
        max_length=100,
        unique=True,
        help_text=_('Nombre único de la categoría (ej: Procesadores).'),
    )
    slug = models.SlugField(
        _('Slug'),
        max_length=120,
        unique=True,
        blank=True,
        help_text=_('Identificador URL-friendly generado automáticamente.'),
    )
    description = models.TextField(
        _('Descripción'),
        blank=True,
        help_text=_('Descripción detallada de la categoría.'),
    )
    is_active = models.BooleanField(
        _('Activa'),
        default=True,
        help_text=_('Indica si la categoría está visible en el catálogo.'),
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
        db_table = 'catalog_category'
        verbose_name = _('Categoría')
        verbose_name_plural = _('Categorías')
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """
        Sobrescribe save() para autogenerar el slug a partir del nombre
        si no fue proporcionado explícitamente.
        """
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Brand(models.Model):
    """
    Representa la marca o fabricante de un componente (ej: Intel, AMD,
    NVIDIA, Corsair, ASUS).

    Al igual que Category, se modela como entidad independiente para
    eliminar la dependencia transitiva 'producto → marca → nombre_marca'.
    """

    name = models.CharField(
        _('Nombre de la marca'),
        max_length=100,
        unique=True,
        help_text=_('Nombre único de la marca (ej: NVIDIA).'),
    )
    slug = models.SlugField(
        _('Slug'),
        max_length=120,
        unique=True,
        blank=True,
    )
    description = models.TextField(
        _('Descripción'),
        blank=True,
    )
    is_active = models.BooleanField(
        _('Activa'),
        default=True,
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
        db_table = 'catalog_brand'
        verbose_name = _('Marca')
        verbose_name_plural = _('Marcas')
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    """
    Representa un componente informático vendible en la tienda.

    Atributos clave:
        - sku: código único de inventario (Stock Keeping Unit).
        - price: precio unitario en pesos chilenos (CLP).
        - stock: unidades físicas disponibles en bodega.

    Relaciones:
        - brand (FK): marca del producto.
        - category (FK): categoría a la que pertenece.

    Notas de negocio:
        - El stock NO se descuenta al agregar al carro; solo al pasar a
          estado PAGADO (ver apps/orders/services.py).
        - El precio se congela en OrderItem al momento del checkout para
          evitar que cambios futuros afecten órdenes históricas.
    """

    sku = models.CharField(
        _('SKU'),
        max_length=50,
        unique=True,
        help_text=_('Código único de inventario (Stock Keeping Unit).'),
    )
    name = models.CharField(
        _('Nombre del producto'),
        max_length=200,
        help_text=_('Nombre comercial del componente.'),
    )
    description = models.TextField(
        _('Descripción'),
        blank=True,
        help_text=_('Especificaciones técnicas y detalles del producto.'),
    )
    brand = models.ForeignKey(
        Brand,
        on_delete=models.PROTECT,       # No se puede borrar una marca con productos
        related_name='products',
        verbose_name=_('Marca'),
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products',
        verbose_name=_('Categoría'),
    )
    price = models.PositiveIntegerField(
        _('Precio unitario (CLP)'),
        validators=[MinValueValidator(0)],
        help_text=_('Precio en pesos chilenos. No puede ser negativo.'),
    )
    stock = models.PositiveIntegerField(
        _('Stock disponible'),
        default=0,
        validators=[MinValueValidator(0)],
        help_text=_('Unidades físicas en bodega.'),
    )
    image = models.ImageField(
        _('Imagen'),
        upload_to='products/',
        blank=True,
        null=True,
        help_text=_('Imagen referencial del producto.'),
    )
    is_active = models.BooleanField(
        _('Activo'),
        default=True,
        help_text=_('Indica si el producto está disponible para la venta.'),
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
        db_table = 'catalog_product'
        verbose_name = _('Producto')
        verbose_name_plural = _('Productos')
        ordering = ['name']
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['brand', 'is_active']),
            models.Index(fields=['price']),
        ]

    def __str__(self):
        return f'{self.name} [{self.sku}]'

    @property
    def is_available(self):
        """Indica si el producto está activo y tiene stock > 0."""
        return self.is_active and self.stock > 0

    @property
    def stock_status(self):
        """
        Retorna una etiqueta legible del estado del stock.
        Útil para mostrar en el frontend.
        """
        if self.stock == 0:
            return 'Sin stock'
        elif self.stock <= 5:
            return 'Últimas unidades'
        return 'Disponible'