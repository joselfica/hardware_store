"""
==============================================================================
VISTAS DEL CARRO DE COMPRAS
==============================================================================
Implementa los endpoints REST del carro. Todas las vistas requieren
autenticación JWT y operan exclusivamente sobre el carro del usuario
autenticado (nunca sobre el carro de otro usuario).

Arquitectura:
    - Las vistas son delgadas (thin controllers): solo validan entrada,
      delegan a los servicios y formatean la salida.
    - La lógica de negocio vive en `apps/cart/services.py`.
    - Los serializers se encargan de la validación y serialización.

Endpoints:
    - GET    /api/cart/                  → Ver mi carro activo.
    - POST   /api/cart/items/            → Agregar producto.
    - PATCH  /api/cart/items/{id}/       → Modificar cantidad.
    - DELETE /api/cart/items/{id}/       → Eliminar ítem.
    - DELETE /api/cart/clear/            → Vaciar carro.
    - GET    /api/cart/summary/          → Resumen rápido (para el badge).

Reglas de negocio aplicadas:
    1. El carro persiste en PostgreSQL vinculado al usuario (1:1).
    2. NUNCA se descuenta stock en estas operaciones. El stock se descuenta
       exclusivamente al confirmar el pago (ver apps/orders/services.py).
    3. Solo el dueño del carro puede verlo y modificarlo.
    4. Los duplicados se manejan con la restricción UNIQUE(cart, product):
       si el producto ya está en el carro, se suma la cantidad.

Autor: José Fica
Sección: AP-N4-C2
Año: 2026
==============================================================================
"""

from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    AddToCartSerializer,
    CartSerializer,
    UpdateCartItemSerializer,
)
from .services import (
    add_product_to_cart,
    clear_cart,
    get_or_create_active_cart,
    remove_item,
    update_item_quantity,
)


# =============================================================================
# ENDPOINT: GET /api/cart/
# =============================================================================
# Retorna el carro activo del usuario autenticado con todos sus ítems y
# totales calculados. Si el usuario no tiene carro (porque es nuevo o porque
# acaba de hacer checkout y se eliminó el anterior), se crea uno vacío
# automáticamente.
# =============================================================================

@extend_schema(
    tags=['Carro de Compras'],
    summary='Ver mi carro activo',
    description=(
        'Retorna el carro activo del usuario autenticado con todos sus '
        'ítems y totales. Si el usuario no tiene carro, se crea uno vacío.'
    ),
    responses={200: CartSerializer},
)
class CartView(APIView):
    """
    Endpoint principal del carro.

    Método: GET /api/cart/
    Permisos: IsAuthenticated (cualquier usuario logueado).
    Respuesta: objeto Cart con ítems anidados y totales.

    Lógica:
        1. Se obtiene o crea el carro activo del usuario con
           `get_or_create_active_cart()`.
        2. Se serializa con CartSerializer (incluye ítems anidados y totales).
        3. Se retorna la respuesta 200 con el JSON del carro.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Maneja el GET del carro activo.

        Args:
            request: Objeto Request de DRF con el usuario autenticado.

        Returns:
            Response: JSON con el carro y sus ítems.
        """
        # --- 1. Obtener o crear el carro activo ---
        # Este servicio garantiza que el usuario siempre tenga un carro,
        # incluso si es su primer acceso tras registrarse.
        cart = get_or_create_active_cart(request.user)

        # --- 2. Serializar el carro ---
        # El CartSerializer incluye los ítems anidados (con subtotales) y
        # los totales calculados (total_items, total_price).
        serializer = CartSerializer(cart, context={'request': request})

        # --- 3. Retornar la respuesta ---
        return Response(serializer.data)


# =============================================================================
# ENDPOINT: POST /api/cart/items/
# =============================================================================
# Agrega un producto al carro del usuario autenticado.
#
# Regla clave: si el producto ya está en el carro, se SUMA la cantidad en
# lugar de crear una fila duplicada. Esto es posible gracias a la restricción
# UNIQUE(cart, product) en el modelo CartItem.
#
# Validaciones:
#     - El producto debe existir y estar activo.
#     - El producto debe tener stock > 0.
#     - La cantidad TOTAL (existente + nueva) no puede superar el stock.
#
# IMPORTANTE: No se descuenta stock aquí. Solo se valida.
# =============================================================================

@extend_schema(
    tags=['Carro de Compras'],
    summary='Agregar producto al carro',
    description=(
        'Agrega un producto al carro activo. Si el producto ya está, '
        'se suma la cantidad. NO descuenta stock (eso ocurre al pagar).'
    ),
    request=AddToCartSerializer,
    responses={
        201: OpenApiResponse(description='Producto agregado al carro.'),
        400: OpenApiResponse(description='Stock insuficiente o producto inválido.'),
    },
)
class AddToCartView(APIView):
    """
    Endpoint para agregar productos al carro.

    Método: POST /api/cart/items/
    Permisos: IsAuthenticated.
    Body: {product_id: int, quantity: int (default 1)}.

    Respuesta:
        201 Created si se creó un nuevo CartItem.
        200 OK si se actualizó uno existente (sumando cantidad).
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Maneja el POST para agregar un producto al carro.

        Flujo:
            1. Se valida el input con AddToCartSerializer (verifica que el
               producto exista y esté activo).
            2. Se delega a `add_product_to_cart()` que aplica las reglas
               de negocio (validación de stock, suma de duplicados).
            3. Se retorna el carro completo actualizado + el ID del ítem.

        Args:
            request: Objeto Request con {product_id, quantity}.

        Returns:
            Response: 201 si se creó, 200 si se actualizó, 400 si hay error.
        """
        # --- 1. Validar entrada ---
        # AddToCartSerializer valida que product_id exista y esté activo,
        # y que quantity sea un entero >= 1. Además, guarda la instancia
        # del producto en `context['product']` para reutilizarla.
        serializer = AddToCartSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        product = serializer.context['product']
        quantity = serializer.validated_data['quantity']

        # --- 2. Delegar a la lógica de negocio ---
        # add_product_to_cart() valida stock, suma cantidades si el producto
        # ya está, y devuelve (cart, item, created).
        cart, item, created = add_product_to_cart(request.user, product, quantity)

        # --- 3. Retornar respuesta diferenciada ---
        # 201 si se creó un nuevo ítem, 200 si se actualizó uno existente.
        return Response(
            {
                'message': (
                    f'Producto agregado al carro.' if created
                    else f'Cantidad actualizada en el carro.'
                ),
                'item_id': item.id,
                'cart': CartSerializer(cart).data,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


# =============================================================================
# ENDPOINT: PATCH /api/cart/items/{id}/
# =============================================================================
# Modifica la cantidad de un ítem existente en el carro.
#
# Validaciones:
#     - El ítem debe pertenecer al carro activo del usuario.
#     - La nueva cantidad debe ser >= 1.
#     - La nueva cantidad no puede superar el stock disponible del producto.
#
# IMPORTANTE: No se descuenta stock aquí. Solo se valida.
# =============================================================================

@extend_schema(
    tags=['Carro de Compras'],
    summary='Modificar cantidad de un ítem',
    request=UpdateCartItemSerializer,
    responses={
        200: OpenApiResponse(description='Cantidad actualizada.'),
        400: OpenApiResponse(description='Stock insuficiente.'),
        404: OpenApiResponse(description='Ítem no encontrado.'),
    },
)
class UpdateCartItemView(APIView):
    """
    Endpoint para modificar la cantidad de un ítem.

    Método: PATCH /api/cart/items/{item_id}/
    Permisos: IsAuthenticated.
    Body: {quantity: int}.

    Nota: Se usa PATCH (no PUT) porque solo modificamos un campo
    (quantity). El resto del CartItem (product, cart) es inmutable.
    """

    permission_classes = [IsAuthenticated]

    def patch(self, request, item_id):
        """
        Maneja el PATCH para modificar la cantidad de un ítem.

        Args:
            request: Objeto Request con {quantity}.
            item_id: ID del CartItem a modificar.

        Returns:
            Response: JSON con el mensaje y el carro actualizado.
        """
        # --- 1. Validar entrada ---
        serializer = UpdateCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # --- 2. Delegar a la lógica de negocio ---
        # update_item_quantity() valida que el ítem pertenezca al usuario,
        # que la cantidad sea válida, y que no supere el stock del producto.
        item = update_item_quantity(
            request.user,
            item_id,
            serializer.validated_data['quantity'],
        )

        # --- 3. Retornar el carro actualizado ---
        cart = get_or_create_active_cart(request.user)
        return Response({
            'message': 'Cantidad actualizada.',
            'cart': CartSerializer(cart).data,
        })


# =============================================================================
# ENDPOINT: DELETE /api/cart/items/{id}/
# =============================================================================
# Elimina un ítem del carro activo del usuario.
#
# El método `remove_item()` filtra por `cart__user=user`, por lo que un
# usuario NO puede eliminar ítems de otro carro aunque conozca el ID.
#
# NO afecta el stock (nunca se descontó, así que no hay nada que reponer).
# =============================================================================

@extend_schema(
    tags=['Carro de Compras'],
    summary='Eliminar un ítem del carro',
    responses={
        204: OpenApiResponse(description='Ítem eliminado.'),
        404: OpenApiResponse(description='Ítem no encontrado.'),
    },
)
class RemoveCartItemView(APIView):
    """
    Endpoint para eliminar un ítem del carro.

    Método: DELETE /api/cart/items/{item_id}/
    Permisos: IsAuthenticated.

    Respuesta:
        204 No Content si se eliminó.
        404 Not Found si el ítem no existe o no pertenece al usuario.
    """

    permission_classes = [IsAuthenticated]

    def delete(self, request, item_id):
        """
        Maneja el DELETE de un ítem.

        Args:
            request: Objeto Request.
            item_id: ID del CartItem a eliminar.

        Returns:
            Response: 204 No Content o 404 Not Found.
        """
        # --- 1. Intentar eliminar el ítem ---
        # remove_item() filtra por `cart__user=user`, así que un usuario
        # malicioso no puede eliminar ítems ajenos con un ID adivinado.
        deleted = remove_item(request.user, item_id)

        # --- 2. Retornar según el resultado ---
        if not deleted:
            return Response(
                {'detail': 'Ítem no encontrado en tu carro.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


# =============================================================================
# ENDPOINT: DELETE /api/cart/clear/
# =============================================================================
# Vacía completamente el carro activo del usuario.
#
# Es más eficiente que eliminar los ítems uno por uno. Se usa cuando el
# usuario quiere "empezar de cero" antes de hacer checkout.
# =============================================================================

@extend_schema(
    tags=['Carro de Compras'],
    summary='Vaciar el carro',
    responses={204: OpenApiResponse(description='Carro vaciado.')},
)
class ClearCartView(APIView):
    """
    Endpoint para vaciar el carro activo.

    Método: DELETE /api/cart/clear/
    Permisos: IsAuthenticated.

    Elimina TODOS los ítems del carro en una sola operación. Es más
    eficiente que hacer N requests DELETE /items/{id}/.
    """

    permission_classes = [IsAuthenticated]

    def delete(self, request):
        """
        Maneja el DELETE del carro completo.

        Args:
            request: Objeto Request.

        Returns:
            Response: 204 No Content siempre (aunque ya estuviera vacío).
        """
        # --- 1. Vaciar el carro ---
        # clear_cart() obtiene el carro activo y elimina todos sus ítems
        # en una sola query. Devuelve la cantidad eliminada.
        clear_cart(request.user)

        # --- 2. Retornar respuesta exitosa ---
        return Response(
            {'message': 'Carro vaciado exitosamente.'},
            status=status.HTTP_204_NO_CONTENT,
        )


# =============================================================================
# ENDPOINT: GET /api/cart/summary/
# =============================================================================
# Retorna SOLO los totales del carro (cantidad de ítems y monto).
#
# Es útil para el frontend porque permite actualizar el badge del carrito
# en el navbar sin traer todo el objeto Cart (que puede ser pesado si tiene
# muchos ítems).
#
# Se llama en cada carga de página para mantener el badge sincronizado.
# =============================================================================

@extend_schema(
    tags=['Carro de Compras'],
    summary='Resumen del carro',
    description='Retorna solo los totales del carro (cantidad y monto).',
    responses={200: {'type': 'object', 'properties': {
        'total_items': {'type': 'integer'},
        'total_price': {'type': 'number'},
        'items_count': {'type': 'integer'},
    }}},
)
class CartSummaryView(APIView):
    """
    Endpoint para obtener un resumen ligero del carro.

    Método: GET /api/cart/summary/
    Permisos: IsAuthenticated.

    Retorna:
        - total_items: suma de cantidades (ej: 3 productos de 2 unidades = 6).
        - total_price: monto total en CLP.
        - items_count: número de filas en el carro (ítems distintos).
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Maneja el GET del resumen.

        Args:
            request: Objeto Request.

        Returns:
            Response: JSON con {total_items, total_price, items_count}.
        """
        # --- 1. Obtener el carro activo ---
        cart = get_or_create_active_cart(request.user)

        # --- 2. Retornar solo los totales ---
        # No serializamos el carro completo, solo los agregados. Esto
        # reduce el payload drásticamente en carros con muchos ítems.
        return Response({
            'total_items': cart.total_items,
            'total_price': cart.total_price,
            'items_count': cart.items.count(),
        })