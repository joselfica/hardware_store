"""
==============================================================================
PERMISOS PERSONALIZADOS DRF (RBAC)
==============================================================================
Define clases de permiso que implementan control de acceso basado en roles.

Estas clases se aplican a nivel de vista (ViewSet o APIView) mediante el
atributo 'permission_classes'. DRF las evalúa en cada request antes de
ejecutar el handler correspondiente.

Roles del sistema:
    - CLIENTE: lectura pública + gestión de su propio carro y órdenes.
    - ADMIN:   gestión total del catálogo e inventario + cambio de estados.

Buenas prácticas aplicadas:
    - Se hereda de BasePermission y se sobrescriben has_permission y/o
      has_object_permission según corresponda.
    - Los mensajes de error son descriptivos y en español.

Autor: [Tu Nombre Completo]
Sección: [Tu Sección]
Año: [Año actual]
==============================================================================
"""

from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdminRole(BasePermission):
    """
    Permite el acceso únicamente a usuarios con rol ADMIN.

    Uso típico: gestión de productos, categorías, marcas y cambio de
    estados de órdenes.
    """

    message = 'Se requiere rol de Administrador de TI para esta operación.'

    def has_permission(self, request, view):
        """Verifica que el usuario esté autenticado y sea ADMIN."""
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'role', None) == 'ADMIN'
        )


class IsClientRole(BasePermission):
    """
    Permite el acceso únicamente a usuarios con rol CLIENTE.

    Uso típico: endpoints de carro y checkout (aunque los admins también
    podrían comprar, la separación de roles es más clara así).
    """

    message = 'Se requiere rol de Cliente para esta operación.'

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'role', None) == 'CLIENTE'
        )


class IsOwnerOrAdmin(BasePermission):
    """
    Permite acceso al propietario del recurso o a un administrador.

    Uso típico: ver/editar el carro o las órdenes propias. Un admin puede
    consultar cualquier carro/orden, pero un cliente solo los suyos.
    """

    message = 'No tienes permiso para acceder a este recurso.'

    def has_object_permission(self, request, view, obj):
        # Los administradores siempre pueden acceder
        if request.user.is_authenticated and getattr(request.user, 'role', None) == 'ADMIN':
            return True
        # Los clientes solo acceden a sus propios recursos
        return obj.user == request.user


class IsAdminOrReadOnly(BasePermission):
    """
    Permite lectura (GET/HEAD/OPTIONS) a cualquiera y escritura solo a ADMIN.

    Uso típico: catálogo de productos y categorías. El público puede ver
    los productos, pero solo un admin puede crearlos/actualizarlos/borrarlos.
    """

    message = 'Solo un Administrador puede modificar el catálogo.'

    def has_permission(self, request, view):
        # Lectura pública
        if request.method in SAFE_METHODS:
            return True
        # Escritura solo para admins autenticados
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'role', None) == 'ADMIN'
        )


class IsAuthenticatedAndActive(BasePermission):
    """
    Permite acceso solo a usuarios autenticados y activos.

    Se diferencia de IsAuthenticated en que valida explícitamente el
    campo is_active (por si se ha desactivado la cuenta sin logout).
    """

    message = 'Tu cuenta está inactiva o no autenticada.'

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_active
        )