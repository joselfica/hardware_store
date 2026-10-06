"""
==============================================================================
VISTAS WEB (FRONTEND HTML)
==============================================================================
Vistas Django que renderizan los templates HTML del frontend. No contienen
lógica de negocio: solo retornan el template correspondiente y los datos
del alumno (nombre, sección, año) para el footer.

El frontend consume la API REST mediante JavaScript (fetch + JWT).

Vistas implementadas:
    - Públicas: Home, ProductDetail, Login, Register.
    - Cliente: Cart, OrderHistory, Checkout, Profile.
    - Admin: Dashboard, Categories, Brands, Products, Orders, Users.
    - Errores: custom_404, custom_500.

Todas heredan de BaseContextMixin, que inyecta los datos del alumno en el
contexto para que el footer los renderice dinámicamente.

Autor: José Fica
Sección: AP-N4-C2
Año: 2026
==============================================================================
"""

from django.shortcuts import render
from django.views.generic import TemplateView


# =============================================================================
# DATOS DEL ALUMNO (REQUISITO DE LA EVALUACIÓN)
# =============================================================================
# Estos datos se inyectan en el contexto de TODAS las vistas y se renderizan
# en el footer base (templates/partials/footer.html).
# =============================================================================

STUDENT_INFO = {
    'student_name': 'José Fica',
    'student_section': 'AP-N4-C2',
    'student_year': '2026',
}


class BaseContextMixin:
    """
    Mixin que inyecta los datos del alumno en el contexto de cada vista.

    Todas las vistas del frontend heredan de este mixin, así el footer
    siempre tiene acceso a student_name, student_section y student_year.
    """

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
# VISTAS DEL CLIENTE (el template valida el token vía JS)
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


class ProfilePageView(BaseContextMixin, TemplateView):
    """
    Página de perfil del usuario autenticado.

    Permite al usuario:
        - Ver y editar sus datos personales.
        - Cambiar su contraseña.

    La verificación de autenticación ocurre en el frontend (profile.js).
    """
    template_name = 'auth/profile.html'


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


# =============================================================================
# HANDLERS DE ERROR PERSONALIZADOS
# =============================================================================
# IMPORTANTE: Solo se activan cuando DEBUG=False.
# Con DEBUG=True, Django muestra sus propias páginas de error de desarrollo.
#
# Se registran en config/urls.py:
#     handler404 = 'apps.catalog.web_views.custom_404'
#     handler500 = 'apps.catalog.web_views.custom_500'
# =============================================================================

def custom_404(request, exception):
    """
    Vista personalizada para error 404.

    Se activa automáticamente cuando DEBUG=False y el usuario accede a una
    URL que no existe.

    Args:
        request: Objeto Request de Django.
        exception: Excepción Http404 que disparó el error.

    Returns:
        HttpResponse: Render del template 404.html con status 404.
    """
    return render(request, '404.html', status=404)


def custom_500(request):
    """
    Vista personalizada para error 500.

    Se activa cuando hay una excepción no capturada en el servidor.
    Con DEBUG=True, Django muestra el traceback en lugar de esta página.

    Args:
        request: Objeto Request de Django.

    Returns:
        HttpResponse: Render del template 500.html con status 500.
    """
    return render(request, '500.html', status=500)