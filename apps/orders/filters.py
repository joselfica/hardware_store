"""
==============================================================================
FILTROS DE ÓRDENES
==============================================================================
Filtros para el listado de órdenes (solo admin).

Parámetros:
    - status: estado de la orden (PENDIENTE, PAGADO, ENTREGADO, CANCELADO).
    - user: ID del usuario.
    - created_after / created_before: rango de fechas.
    - paid_after / paid_before: rango de fechas de pago.
    - total_min / total_max: rango de monto.
    - search: búsqueda en order_number o username.

Autor: [Tu Nombre Completo]
Sección: [Tu Sección]
Año: [Año actual]
==============================================================================
"""

import django_filters
from django.db.models import Q

from .models import Order


class OrderFilter(django_filters.FilterSet):
    """Filtros avanzados para el listado de órdenes."""

    user = django_filters.NumberFilter(field_name='user__id')
    username = django_filters.CharFilter(
        field_name='user__username',
        lookup_expr='icontains',
    )
    created_after = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    paid_after = django_filters.DateFilter(field_name='paid_at', lookup_expr='gte')
    paid_before = django_filters.DateFilter(field_name='paid_at', lookup_expr='lte')
    total_min = django_filters.NumberFilter(field_name='total', lookup_expr='gte')
    total_max = django_filters.NumberFilter(field_name='total', lookup_expr='lte')
    search = django_filters.CharFilter(method='filter_search')

    class Meta:
        model = Order
        fields = ['status']

    def filter_search(self, queryset, name, value):
        """Busca por order_number o username."""
        return queryset.filter(
            Q(order_number__icontains=value)
            | Q(user__username__icontains=value)
            | Q(user__email__icontains=value)
        )