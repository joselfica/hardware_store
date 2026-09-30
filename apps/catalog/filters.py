"""
==============================================================================
FILTROS DEL CATÁLOGO (django-filter)
==============================================================================
Define los FilterSets para Category, Brand y Product.

Un FilterSet se aplica automáticamente cuando DRF procesa un request
con parámetros de query. Cada filtro se declara explícitamente para
documentar su comportamiento y permitir validaciones.

Uso:
    from django_filters.rest_framework import DjangoFilterBackend
    class ProductViewSet(viewsets.ModelViewSet):
        filter_backends = [DjangoFilterBackend]
        filterset_class = ProductFilter

Autor: [Tu Nombre Completo]
Sección: [Tu Sección]
Año: [Año actual]
==============================================================================
"""

import django_filters
from django.db.models import Q

from .models import Brand, Category, Product


# =============================================================================
# FILTRO DE CATEGORÍA
# =============================================================================

class CategoryFilter(django_filters.FilterSet):
    """
    Filtros para /api/categories/.

    Parámetros:
        - is_active (bool): filtrar por estado activo/inactivo.
        - search (str): búsqueda en nombre y descripción (a través de SearchFilter).
        - ordering (str): ordenamiento (a través de OrderingFilter).
    """

    name_contains = django_filters.CharFilter(
        field_name='name',
        lookup_expr='icontains',
        label='Nombre contiene',
    )
    created_after = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='gte',
        label='Creadas después de',
    )
    created_before = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='lte',
        label='Creadas antes de',
    )

    class Meta:
        model = Category
        fields = ['is_active']


# =============================================================================
# FILTRO DE MARCA
# =============================================================================

class BrandFilter(django_filters.FilterSet):
    """Filtros para /api/brands/. Estructura idéntica a CategoryFilter."""

    name_contains = django_filters.CharFilter(
        field_name='name',
        lookup_expr='icontains',
        label='Nombre contiene',
    )
    created_after = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='gte',
    )
    created_before = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='lte',
    )

    class Meta:
        model = Brand
        fields = ['is_active']


# =============================================================================
# FILTRO DE PRODUCTO (el más importante)
# =============================================================================

class ProductFilter(django_filters.FilterSet):
    """
    Filtros avanzados para /api/products/.

    Parámetros:
        - category (int): ID de categoría.
        - category_slug (str): slug de categoría (URL-friendly).
        - brand (int): ID de marca.
        - brand_slug (str): slug de marca.
        - price_min (decimal): precio mínimo (>=).
        - price_max (decimal): precio máximo (<=).
        - stock_min (int): stock mínimo (>=).
        - in_stock (bool): solo productos con stock > 0.
        - is_active (bool): solo productos activos.
        - search (str): búsqueda en nombre/SKU/descripción/marca/categoría.
        - ordering (str): ordenamiento por price, name, created_at, stock.
    """

    # --- Filtros por categoría ---
    category = django_filters.NumberFilter(
        field_name='category__id',
        label='ID de categoría',
    )
    category_slug = django_filters.CharFilter(
        field_name='category__slug',
        lookup_expr='iexact',
        label='Slug de categoría',
    )
    category_name = django_filters.CharFilter(
        field_name='category__name',
        lookup_expr='icontains',
        label='Nombre de categoría contiene',
    )

    # --- Filtros por marca ---
    brand = django_filters.NumberFilter(
        field_name='brand__id',
        label='ID de marca',
    )
    brand_slug = django_filters.CharFilter(
        field_name='brand__slug',
        lookup_expr='iexact',
        label='Slug de marca',
    )
    brand_name = django_filters.CharFilter(
        field_name='brand__name',
        lookup_expr='icontains',
        label='Nombre de marca contiene',
    )

    # --- Filtros por rango de precio ---
    price_min = django_filters.NumberFilter(
        field_name='price',
        lookup_expr='gte',
        label='Precio mínimo',
    )
    price_max = django_filters.NumberFilter(
        field_name='price',
        lookup_expr='lte',
        label='Precio máximo',
    )

    # --- Filtros por stock ---
    stock_min = django_filters.NumberFilter(
        field_name='stock',
        lookup_expr='gte',
        label='Stock mínimo',
    )
    stock_max = django_filters.NumberFilter(
        field_name='stock',
        lookup_expr='lte',
        label='Stock máximo',
    )
    in_stock = django_filters.BooleanFilter(
        method='filter_in_stock',
        label='Solo con stock disponible',
    )

    # --- Filtros por fecha ---
    created_after = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='gte',
        label='Creados después de',
    )
    created_before = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='lte',
        label='Creados antes de',
    )

    # --- Filtro compuesto de búsqueda ---
    search = django_filters.CharFilter(
        method='filter_search',
        label='Búsqueda general',
    )

    class Meta:
        model = Product
        fields = ['is_active']

    def filter_in_stock(self, queryset, name, value):
        """Filtra productos con stock > 0 si value=True."""
        if value:
            return queryset.filter(stock__gt=0)
        return queryset

    def filter_search(self, queryset, name, value):
        """
        Búsqueda compuesta en múltiples campos: nombre, SKU, descripción,
        nombre de marca y nombre de categoría.
        """
        return queryset.filter(
            Q(name__icontains=value)
            | Q(sku__icontains=value)
            | Q(description__icontains=value)
            | Q(brand__name__icontains=value)
            | Q(category__name__icontains=value)
        )