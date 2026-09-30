"""
==============================================================================
ADMIN DEL CATÁLOGO
==============================================================================
Configura el panel de administración de Django para Category, Brand y
Product. Se aprovecha el admin nativo de Django como herramienta
complementaria al panel admin personalizado del frontend.

Configuraciones aplicadas:
    - list_display: columnas mostradas en el listado.
    - list_filter: filtros laterales.
    - search_fields: campos incluidos en el buscador.
    - prepopulated_fields: autogenerar slug desde el nombre.
    - list_editable: editar precio/stock directamente en el listado.
    - fieldsets: agrupar campos por secciones lógicas en el detalle.

Autor: José Fica
Sección: AP-N4-C2
Año: 2026
==============================================================================
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Brand, Category, Product


# =============================================================================
# ADMIN: CATEGORÍA
# =============================================================================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo Category.

    - list_display: nombre, slug, estado, fecha de creación.
    - list_filter: filtro por estado activo/inactivo.
    - search_fields: búsqueda por nombre y descripción.
    - prepopulated_fields: autogenera el slug desde el nombre mientras
      se escribe en el formulario de creación.
    """
    list_display = ('name', 'slug', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}


# =============================================================================
# ADMIN: MARCA
# =============================================================================

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo Brand.

    Similar a CategoryAdmin. La búsqueda solo incluye el nombre porque
    las marcas no tienen una descripción larga relevante.
    """
    list_display = ('name', 'slug', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


# =============================================================================
# ADMIN: PRODUCTO
# =============================================================================
# Configuración más avanzada: campos editables en el listado y fieldsets
# agrupados para mejor organización del detalle.
# =============================================================================

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo Product.

    Características avanzadas:
        - list_editable: permite editar precio, stock y estado directamente
          desde el listado (útil para ajustes rápidos de inventario).
        - readonly_fields: created_at y updated_at no son editables.
        - fieldsets: agrupa los campos en 4 secciones lógicas:
            * Identificación: SKU, nombre, descripción, imagen.
            * Clasificación: marca y categoría.
            * Comercial: precio, stock, estado.
            * Auditoría: timestamps (colapsado por defecto).
    """
    list_display = ('sku', 'name', 'brand', 'category', 'price', 'stock', 'is_active')
    list_filter = ('is_active', 'category', 'brand')
    search_fields = ('sku', 'name', 'description')
    list_editable = ('price', 'stock', 'is_active')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        (_('Identificación'), {
            'fields': ('sku', 'name', 'description', 'image'),
        }),
        (_('Clasificación'), {
            'fields': ('brand', 'category'),
        }),
        (_('Comercial'), {
            'fields': ('price', 'stock', 'is_active'),
        }),
        (_('Auditoría'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),  # Colapsado por defecto
        }),
    )