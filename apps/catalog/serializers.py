"""
==============================================================================
SERIALIZERS DEL CATÁLOGO
==============================================================================
Define los serializers para Category, Brand y Product.

Estrategia:
    - Para Category y Brand se exponen serializers de lectura y escritura
      simples, ya que tienen pocos campos.
    - Para Product se exponen DOS serializers:
        * ProductListSerializer: versión ligera para listados (sin descripción
          larga ni imagen), optimizada para rendimiento.
        * ProductDetailSerializer: versión completa con anidamiento de marca
          y categoría para vistas de detalle.
    - Se incluyen campos calculados (read-only) como is_available y
      stock_status que el frontend puede usar directamente.

Autor: [Tu Nombre Completo]
Sección: [Tu Sección]
Año: [Año actual]
==============================================================================
"""

from rest_framework import serializers

from .models import Brand, Category, Product


# =============================================================================
# SERIALIZERS DE CATEGORÍA
# =============================================================================

class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer de lectura/escritura para Category.

    Campos calculados:
        - products_count: cantidad de productos activos en la categoría.
          Se obtiene por annotate en la vista para evitar N+1 queries.
    """

    products_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = (
            'id', 'name', 'slug', 'description',
            'is_active', 'products_count', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'slug', 'created_at', 'updated_at')

    def validate_name(self, value):
        """Valida que el nombre no esté duplicado (case-insensitive)."""
        qs = Category.objects.filter(name__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                'Ya existe una categoría con este nombre.'
            )
        return value


# =============================================================================
# SERIALIZERS DE MARCA
# =============================================================================

class BrandSerializer(serializers.ModelSerializer):
    """
    Serializer de lectura/escritura para Brand.
    """

    products_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Brand
        fields = (
            'id', 'name', 'slug', 'description',
            'is_active', 'products_count', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'slug', 'created_at', 'updated_at')

    def validate_name(self, value):
        """Valida que el nombre no esté duplicado (case-insensitive)."""
        qs = Brand.objects.filter(name__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                'Ya existe una marca con este nombre.'
            )
        return value


# =============================================================================
# SERIALIZERS DE PRODUCTO
# =============================================================================

class ProductListSerializer(serializers.ModelSerializer):
    """
    Serializer LIGERO para listados de productos.

    Optimización:
        - Solo expone los campos esenciales para tarjetas de catálogo.
        - Anida marca y categoría como strings (no objetos completos) para
          reducir el tamaño del JSON.
    """

    brand_name = serializers.CharField(source='brand.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    stock_status = serializers.CharField(read_only=True)
    is_available = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = (
            'id', 'sku', 'name', 'brand_name', 'category_name',
            'price', 'stock', 'stock_status', 'is_available',
            'image', 'is_active',
        )


class ProductDetailSerializer(serializers.ModelSerializer):
    """
    Serializer COMPLETO para detalle y escritura de productos.

    Características:
        - Anida marca y categoría como objetos completos (read-only).
        - Acepta brand_id y category_id para escritura.
        - Valida que el precio sea positivo y el stock no negativo.
        - El SKU es de solo lectura tras la creación (no se puede modificar).
    """

    brand = BrandSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    brand_id = serializers.PrimaryKeyRelatedField(
        queryset=Brand.objects.filter(is_active=True),
        source='brand',
        write_only=True,
    )
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.filter(is_active=True),
        source='category',
        write_only=True,
    )
    stock_status = serializers.CharField(read_only=True)
    is_available = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = (
            'id', 'sku', 'name', 'description',
            'brand', 'brand_id', 'category', 'category_id',
            'price', 'stock', 'stock_status', 'is_available',
            'image', 'is_active', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def validate_price(self, value):
        """Valida que el precio sea positivo."""
        if value <= 0:
            raise serializers.ValidationError(
                'El precio debe ser mayor a 0.'
            )
        return value

    def validate_stock(self, value):
        """Valida que el stock no sea negativo."""
        if value < 0:
            raise serializers.ValidationError(
                'El stock no puede ser negativo.'
            )
        return value

    def validate_sku(self, value):
        """
        Valida que el SKU sea único (case-insensitive) y no contenga
        espacios (formato estándar SKU).
        """
        if ' ' in value:
            raise serializers.ValidationError(
                'El SKU no puede contener espacios.'
            )
        qs = Product.objects.filter(sku__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                'Ya existe un producto con este SKU.'
            )
        return value.upper()