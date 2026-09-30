"""
==============================================================================
URLS DEL CATÁLOGO
==============================================================================
Define las rutas del catálogo de productos usando DefaultRouter de DRF.
El router genera automáticamente las rutas REST estándar para cada ViewSet,
más las acciones personalizadas (@action).

Estructura generada:
    ┌─────────────────────────────────────────────────────────────────┐
    │ CATEGORÍAS                                                       │
    │ GET     /api/categories/              → listar                   │
    │ POST    /api/categories/              → crear (admin)            │
    │ GET     /api/categories/{id}/         → detalle                  │
    │ PUT     /api/categories/{id}/         → actualizar (admin)       │
    │ PATCH   /api/categories/{id}/         → actualizar parcial       │
    │ DELETE  /api/categories/{id}/         → eliminar (admin)         │
    ├─────────────────────────────────────────────────────────────────┤
    │ MARCAS                                                           │
    │ (misma estructura que categorías)                                │
    ├─────────────────────────────────────────────────────────────────┤
    │ PRODUCTOS                                                        │
    │ (misma estructura que categorías)                                │
    │ GET     /api/products/{id}/stock/     → acción personalizada     │
    └─────────────────────────────────────────────────────────────────┘

Ventajas del DefaultRouter:
    - Genera las rutas automáticamente (menos código).
    - Incluye la API raíz navegable (/api/) con enlaces a los endpoints.
    - Soporta el sufijo de formato (?format=json o ?format=api).

Autor: José Fica
Sección: AP-N4-C2
Año: 2026
==============================================================================
"""

from rest_framework.routers import DefaultRouter

from .views import BrandViewSet, CategoryViewSet, ProductViewSet

app_name = 'catalog'

# =============================================================================
# ROUTER
# =============================================================================
# Registramos cada ViewSet con una URL base. DRF genera automáticamente
# las rutas para las acciones estándar (list, create, retrieve, update,
# partial_update, destroy) + cualquier @action personalizada.
# =============================================================================

router = DefaultRouter()

# Categorías: /api/categories/ y /api/categories/{id}/
router.register(r'categories', CategoryViewSet, basename='category')

# Marcas: /api/brands/ y /api/brands/{id}/
router.register(r'brands', BrandViewSet, basename='brand')

# Productos: /api/products/ y /api/products/{id}/
# Incluye acción personalizada: /api/products/{id}/stock/
router.register(r'products', ProductViewSet, basename='product')

urlpatterns = router.urls