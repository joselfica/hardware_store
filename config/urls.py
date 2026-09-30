"""
==============================================================================
URLs RAÍZ DEL PROYECTO
==============================================================================
Aquí se centralizan las rutas principales:
    - /admin/         → Panel de administración Django
    - /api/           → API REST (dividida por apps)
    - /api/docs/      → Documentación Swagger
    - /api/schema/    → Esquema OpenAPI en YAML
    - /               → Frontend HTML
    - /admin-panel/   → Panel de administración personalizado (frontend)
==============================================================================
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# --- Documentación OpenAPI (drf-spectacular) ---
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

# --- Vistas del frontend (apps.catalog.web_views) ---
from apps.catalog.web_views import (
    # Páginas públicas
    HomeView,
    ProductDetailView,
    LoginPageView,
    RegisterPageView,
    CartPageView,
    OrderHistoryPageView,
    CheckoutPageView,
    # Páginas del panel admin
    AdminDashboardView,
    CategoriesManageView,
    BrandsManageView,
    ProductsManageView,
    OrdersManageView,
    UsersManageView,
)


urlpatterns = [
    # ========================================================================
    # ADMIN DE DJANGO
    # ========================================================================
    path('admin/', admin.site.urls),

    # ========================================================================
    # API REST (por app)
    # ========================================================================
    path('api/', include('apps.users.urls')),
    path('api/', include('apps.catalog.urls')),
    path('api/', include('apps.cart.urls')),
    path('api/', include('apps.orders.urls')),

    # ========================================================================
    # DOCUMENTACIÓN API (Swagger / OpenAPI)
    # ========================================================================
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # ========================================================================
    # FRONTEND HTML - PÁGINAS PÚBLICAS
    # ========================================================================
    path('', HomeView.as_view(), name='home'),
    path('producto/<int:pk>/', ProductDetailView.as_view(), name='product-detail-page'),
    path('login/', LoginPageView.as_view(), name='login-page'),
    path('registro/', RegisterPageView.as_view(), name='register-page'),

    # ========================================================================
    # FRONTEND HTML - PÁGINAS DEL CLIENTE
    # ========================================================================
    path('carro/', CartPageView.as_view(), name='cart-page'),
    path('mis-ordenes/', OrderHistoryPageView.as_view(), name='order-history-page'),
    path('checkout/', CheckoutPageView.as_view(), name='checkout-page'),

    # ========================================================================
    # FRONTEND HTML - PANEL DE ADMINISTRACIÓN
    # ========================================================================
    path('admin-panel/', AdminDashboardView.as_view(), name='admin-dashboard'),
    path('admin-panel/categorias/', CategoriesManageView.as_view(), name='admin-categories'),
    path('admin-panel/marcas/', BrandsManageView.as_view(), name='admin-brands'),
    path('admin-panel/productos/', ProductsManageView.as_view(), name='admin-products'),
    path('admin-panel/ordenes/', OrdersManageView.as_view(), name='admin-orders'),
    path('admin-panel/usuarios/', UsersManageView.as_view(), name='admin-users'),
]


# ============================================================================
# SERVIR ARCHIVOS MEDIA Y STATIC EN DESARROLLO
# ============================================================================
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)