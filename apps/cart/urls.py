"""
==============================================================================
URLS DEL CARRO DE COMPRAS
==============================================================================
Define las rutas del carro. Todas requieren autenticación JWT
(IsAuthenticated) y operan exclusivamente sobre el carro del usuario
autenticado.

Estructura:
    ┌──────────────────────────────────────────────────────────────────┐
    │ GET     /api/cart/                     → Ver mi carro activo     │
    │ GET     /api/cart/summary/             → Totales (para el badge) │
    │ DELETE  /api/cart/clear/               → Vaciar el carro         │
    │ POST    /api/cart/items/               → Agregar producto        │
    │ PATCH   /api/cart/items/{id}/          → Modificar cantidad      │
    │ DELETE  /api/cart/items/{id}/delete/   → Eliminar ítem           │
    └──────────────────────────────────────────────────────────────────┘

Nota de diseño:
    Se usa APIView en lugar de ViewSet porque cada endpoint tiene un
    comportamiento muy específico y no sigue el patrón CRUD estándar.
    Por ejemplo, "agregar al carro" no es un "create" típico porque
    puede sumar cantidad si el producto ya existe.

Autor: José Fica
Sección: AP-N4-C2
Año: 2026
==============================================================================
"""

from django.urls import path

from .views import (
    AddToCartView,
    CartSummaryView,
    CartView,
    ClearCartView,
    RemoveCartItemView,
    UpdateCartItemView,
)

app_name = 'cart'

urlpatterns = [
    # =========================================================================
    # OPERACIONES SOBRE EL CARRO
    # =========================================================================
    # - GET    → ver el carro activo con sus ítems.
    # - GET    → resumen ligero (totales) para el badge del navbar.
    # - DELETE → vaciar todo el carro en una sola operación.
    # =========================================================================
    path('cart/', CartView.as_view(), name='cart-detail'),
    path('cart/summary/', CartSummaryView.as_view(), name='cart-summary'),
    path('cart/clear/', ClearCartView.as_view(), name='cart-clear'),

    # =========================================================================
    # OPERACIONES SOBRE LOS ÍTEMS
    # =========================================================================
    # - POST   → agregar un producto (o sumar cantidad si ya existe).
    # - PATCH  → modificar la cantidad de un ítem existente.
    # - DELETE → eliminar un ítem.
    #
    # Nota: El DELETE usa una ruta separada con sufijo `/delete/` porque
    # DRF no permite dos métodos distintos (PATCH y DELETE) sobre la misma
    # ruta cuando se usan APIView individuales. Con un ViewSet se podría,
    # pero aquí priorizamos la claridad de cada endpoint.
    # =========================================================================
    path('cart/items/', AddToCartView.as_view(), name='cart-add-item'),
    path('cart/items/<int:item_id>/', UpdateCartItemView.as_view(), name='cart-update-item'),
    path('cart/items/<int:item_id>/delete/', RemoveCartItemView.as_view(), name='cart-remove-item'),
]