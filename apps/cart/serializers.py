"""
==============================================================================
SERIALIZERS DEL CARRO DE COMPRAS
==============================================================================
Define los serializers para exponer el carro y sus ítems a través de la API,
y para validar la entrada de las operaciones de escritura.

Serializers:
    - CartItemSerializer: lectura enriquecida de un ítem (incluye datos
      del producto anidado y subtotal calculado).
    - CartSerializer: lectura completa del carro con ítems y totales.
    - AddToCartSerializer: entrada para POST /api/cart/items/.
    - UpdateCartItemSerializer: entrada para PATCH /api/cart/items/{id}/.

Notas:
    - Los serializers de lectura (CartItem, Cart) son de solo lectura: la
      modificación se hace exclusivamente mediante los servicios.
    - Los serializers de entrada (AddToCart, UpdateCartItem) usan
      serializers.Serializer en lugar de ModelSerializer porque no
      representan directamente un modelo (agregar al carro puede sumar
      cantidad en lugar de crear una fila nueva).

Autor: José Fica
Sección: AP-N4-C2
Año: 2026
==============================================================================
"""

from rest_framework import serializers

from apps.catalog.models import Product
from .models import Cart, CartItem


# =============================================================================
# SERIALIZER: ÍTEM DEL CARRITO (LECTURA)
# =============================================================================
# Expone un CartItem con datos enriquecidos del producto anidado
# (nombre, SKU, precio, stock, imagen) y el subtotal calculado.
#
# Es de SOLO LECTURA porque la modificación se realiza mediante los
# servicios (add_product_to_cart, update_item_quantity, remove_item).
# =============================================================================

class CartItemSerializer(serializers.ModelSerializer):
    """
    Serializer de lectura de un ítem del carro.

    Campos anidados (read-only) del producto:
        - product_id, product_name, product_sku
        - product_price, product_stock, product_image

    Campos calculados:
        - subtotal: precio × cantidad.

    Uso típico:
        Forma parte de CartSerializer (anidado en `items`).
    """

    # --- Datos enriquecidos del producto ---
    product_id = serializers.IntegerField(source='product.id', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    product_price = serializers.IntegerField(source='product.price', read_only=True)
    product_stock = serializers.IntegerField(source='product.stock', read_only=True)
    product_image = serializers.ImageField(source='product.image', read_only=True)

    # --- Campos calculados ---
    # El subtotal es una property del modelo (product.price * quantity).
    subtotal = serializers.IntegerField(read_only=True)

    class Meta:
        model = CartItem
        fields = (
            'id', 'product_id', 'product_name', 'product_sku',
            'product_price', 'product_stock', 'product_image',
            'quantity', 'subtotal', 'added_at',
        )


# =============================================================================
# SERIALIZER: CARRITO (LECTURA)
# =============================================================================
# Expone un Cart completo con sus ítems anidados y los totales calculados.
# Se usa en las respuestas de GET /api/cart/ y POST /api/cart/items/.
# =============================================================================

class CartSerializer(serializers.ModelSerializer):
    """
    Serializer de lectura del carro completo.

    Campos:
        - id, username, is_active.
        - items: lista de CartItemSerializer (anidado).
        - total_items: suma de cantidades.
        - total_price: monto total en CLP.
        - created_at, updated_at.

    Los totales son properties del modelo, por eso no se almacenan en la BD
    (mantiene 3FN y evita inconsistencias si cambian los precios).
    """

    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    total_price = serializers.IntegerField(read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Cart
        fields = (
            'id', 'username', 'is_active',
            'items', 'total_items', 'total_price',
            'created_at', 'updated_at',
        )


# =============================================================================
# SERIALIZER: AGREGAR AL CARRITO (ENTRADA)
# =============================================================================
# Valida la entrada de POST /api/cart/items/.
#
# Se usa serializers.Serializer (no ModelSerializer) porque no representa
# un modelo directamente: puede crear un CartItem O sumar cantidad a uno
# existente (lógica en add_product_to_cart).
# =============================================================================

class AddToCartSerializer(serializers.Serializer):
    """
    Serializer de entrada para agregar un producto al carro.

    Campos:
        - product_id: ID del producto (obligatorio).
        - quantity: cantidad (opcional, default=1, mínimo 1).

    Validación:
        - product_id debe corresponder a un producto activo existente.
        - Se guarda la instancia del producto en `self.context['product']`
          para que la vista la reutilice sin hacer una segunda query.
    """

    product_id = serializers.IntegerField(
        required=True,
        help_text='ID del producto a agregar.',
    )
    quantity = serializers.IntegerField(
        required=False,
        default=1,
        min_value=1,
        help_text='Cantidad a agregar (mínimo 1).',
    )

    def validate_product_id(self, value):
        """
        Verifica que el producto exista y esté activo.

        Args:
            value: ID del producto recibido en el payload.

        Returns:
            int: El mismo ID si es válido.

        Raises:
            ValidationError: Si el producto no existe o está inactivo.
        """
        try:
            product = Product.objects.get(pk=value, is_active=True)
        except Product.DoesNotExist:
            raise serializers.ValidationError(
                'El producto no existe o no está disponible.'
            )
        # Guardar la instancia para reutilizarla en la vista
        self.context['product'] = product
        return value


# =============================================================================
# SERIALIZER: ACTUALIZAR CANTIDAD (ENTRADA)
# =============================================================================
# Valida la entrada de PATCH /api/cart/items/{id}/.
#
# Solo acepta `quantity` (mínimo 1). No se puede modificar el producto
# asociado a un ítem: si quieres otro producto, eliminas este ítem y
# agregas el nuevo.
# =============================================================================

class UpdateCartItemSerializer(serializers.Serializer):
    """
    Serializer de entrada para modificar la cantidad de un ítem.

    Campos:
        - quantity: nueva cantidad (obligatorio, mínimo 1).

    La validación de stock se hace en el servicio `update_item_quantity()`
    porque necesita consultar el producto asociado al ítem.
    """

    quantity = serializers.IntegerField(
        required=True,
        min_value=1,
        help_text='Nueva cantidad (mínimo 1).',
    )