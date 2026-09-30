"""
==============================================================================
ADMIN DE USUARIOS
==============================================================================
Configura el panel de administración de Django para el modelo User
personalizado. Extiende UserAdmin nativo para agregar los campos
personalizados (role, rut, phone) tanto en la vista de detalle como
en el formulario de creación.

Características:
    - list_display: username, email, nombre completo, rol, estado, fecha.
    - list_filter: filtros por rol, estado y flags de permisos.
    - search_fields: búsqueda por username, email, RUT y nombre.
    - fieldsets: agrupa los campos personalizados en sección "Información adicional".

Autor: José Fica
Sección: AP-N4-C2
Año: 2026
==============================================================================
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


# =============================================================================
# ADMIN: USUARIO
# =============================================================================
# Extiende UserAdmin de Django para agregar los campos personalizados del
# modelo User (role, rut, phone). Se usa `fieldsets` y `add_fieldsets` para
# agrupar los campos tanto en la vista de detalle como en la creación.
# =============================================================================

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Personalización del admin para el modelo User personalizado.

    Columnas mostradas:
        - username, email, full_name (property), role, is_active, date_joined.

    Filtros laterales:
        - role: CLIENTE vs ADMIN.
        - is_active, is_staff, is_superuser.

    Búsqueda:
        - username, email, rut, first_name, last_name.

    Fieldsets extendidos:
        - Se agregan role, rut y phone a los fieldsets por defecto de
          UserAdmin, en una sección "Información adicional".
    """

    list_display = ('username', 'email', 'full_name', 'role', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'rut', 'first_name', 'last_name')
    ordering = ('-date_joined',)

    # --- Extender fieldsets con los campos personalizados ---
    fieldsets = BaseUserAdmin.fieldsets + (
        (_('Información adicional'), {
            'fields': ('role', 'rut', 'phone'),
        }),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (_('Información adicional'), {
            'fields': ('role', 'rut', 'phone'),
        }),
    )