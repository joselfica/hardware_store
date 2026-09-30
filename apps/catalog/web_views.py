"""
==============================================================================
VISTAS WEB (FRONTEND HTML)
==============================================================================
Vistas Django que renderizan los templates HTML del frontend. No contienen
lógica de negocio: solo retornan el template correspondiente y los datos
del alumno (nombre, sección, año) para el footer.

El frontend consume la API REST mediante JavaScript (fetch + JWT).

Autor: [Tu Nombre Completo]
Sección: [Tu Sección]
Año: [Año actual]
==============================================================================
"""

from django.shortcuts import render
from django.views.generic import TemplateView


# --- Datos del alumno para el footer (REQUISITO DE LA EVALUACIÓN) ---
STUDENT_INFO = {
    'student_name': 'José Fica',
    'student_section': 'AP-N4-C2',
    'student_year': '2026',
}


class BaseContextMixin:
    """Mixin que inyecta los datos del alumno en el contexto de cada vista."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(STUDENT_INFO)
        return context


# =============================================================================
# VISTAS PÚBLICAS
# =============================================================================

class HomeView(BaseContextMixin, TemplateView):
    """Página principal: catálogo de productos con filtros."""
    template_name = 'catalog/product_list.html'


class ProductDetailView(BaseContextMixin, TemplateView):
    """Detalle de un producto: /producto/<id>/"""
    template_name = 'catalog/product_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product_id'] = self.kwargs['pk']
        return context


class LoginPageView(BaseContextMixin, TemplateView):
    """Página de login."""
    template_name = 'auth/login.html'


class RegisterPageView(BaseContextMixin, TemplateView):
    """Página de registro."""
    template_name = 'auth/register.html'


# =============================================================================
# VISTAS PROTEGIDAS (el template valida el token vía JS)
# =============================================================================

class CartPageView(BaseContextMixin, TemplateView):
    """Página del carro de compras."""
    template_name = 'cart/cart_detail.html'


class OrderHistoryPageView(BaseContextMixin, TemplateView):
    """Historial de órdenes del cliente."""
    template_name = 'orders/order_history.html'


class CheckoutPageView(BaseContextMixin, TemplateView):
    """Página de checkout."""
    template_name = 'orders/checkout.html'



# =============================================================================
# VISTAS DEL PANEL DE ADMINISTRACIÓN
# =============================================================================
# Estas vistas renderizan los templates del panel admin. La verificación
# real del rol ocurre en el frontend (admin_guard.js) mediante el claim
# 'role' del JWT. Si un cliente intenta acceder, es redirigido al inicio.
#
# Aunque el frontend oculta el enlace, la seguridad REAL está en el backend:
# los endpoints de escritura exigen IsAdminRole.
# =============================================================================

class AdminDashboardView(BaseContextMixin, TemplateView):
    """Panel principal del admin con estadísticas rápidas."""
    template_name = 'admin_panel/dashboard.html'


class CategoriesManageView(BaseContextMixin, TemplateView):
    """CRUD de categorías."""
    template_name = 'admin_panel/categories_manage.html'


class BrandsManageView(BaseContextMixin, TemplateView):
    """CRUD de marcas."""
    template_name = 'admin_panel/brands_manage.html'


class ProductsManageView(BaseContextMixin, TemplateView):
    """CRUD de productos."""
    template_name = 'admin_panel/products_manage.html'


class OrdersManageView(BaseContextMixin, TemplateView):
    """Gestión de órdenes (cambio de estados)."""
    template_name = 'admin_panel/orders_manage.html'

class UsersManageView(BaseContextMixin, TemplateView):
    """Gestión de usuarios (solo Admin)."""
    template_name = 'admin_panel/users_manage.html'