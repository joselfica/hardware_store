"""
==============================================================================
URLS DE ÓRDENES
==============================================================================
Define las rutas del ciclo de vida de las órdenes.

Estructura:
    ┌──────────────────────────────────────────────────────────────────────┐
    │ POST   /api/orders/checkout/               → Carro → Orden PENDIENTE │
    │ GET    /api/orders/my-orders/              → Mis órdenes (cliente)   │
    │ GET    /api/orders/                        → Todas (solo admin)      │
    │ GET    /api/orders/{order_number}/         → Detalle (UUID público)  │
    │ PATCH  /api/orders/{order_number}/status/  → Cambiar estado          │
    └──────────────────────────────────────────────────────────────────────┘

Nota de diseño:
    Se usa `order_number` (UUID) en las rutas en lugar de la PK entera.
    Esto evita que un atacante enumere órdenes ajenas probando IDs
    secuenciales (/api/orders/1/, /api/orders/2/, ...).

Autor: José Fica
Sección: AP-N4-C2
Año: 2026
==============================================================================
"""

from django.urls import path

from .views import (
    AllOrdersView,
    ChangeOrderStatusView,
    CheckoutView,
    MyOrdersView,
    OrderDetailView,
)

app_name = 'orders'

urlpatterns = [
    # =========================================================================
    # CHECKOUT
    # =========================================================================
    # POST /api/orders/checkout/
    # Convierte el carro activo del usuario en una orden PENDIENTE.
    # NO descuenta stock. Elimina el carro tras la operación.
    # =========================================================================
    path('orders/checkout/', CheckoutView.as_view(), name='checkout'),

    # =========================================================================
    # LISTADOS
    # =========================================================================
    # - /my-orders/  → solo las órdenes del usuario autenticado.
    # - /            → todas las órdenes (solo admin).
    # =========================================================================
    path('orders/my-orders/', MyOrdersView.as_view(), name='my-orders'),
    path('orders/', AllOrdersView.as_view(), name='all-orders'),

    # =========================================================================
    # DETALLE Y CAMBIO DE ESTADO
    # =========================================================================
    # Se usa <uuid:order_number> en lugar de <int:pk> para evitar
    # enumeración de órdenes por parte de atacantes.
    # =========================================================================
    path(
        'orders/<uuid:order_number>/',
        OrderDetailView.as_view(),
        name='order-detail',
    ),
    path(
        'orders/<uuid:order_number>/status/',
        ChangeOrderStatusView.as_view(),
        name='order-status',
    ),
]