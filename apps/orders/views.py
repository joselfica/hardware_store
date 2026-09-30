"""
==============================================================================
VISTAS DE ÓRDENES
==============================================================================
Implementa los endpoints REST del ciclo de vida de las órdenes. Cada vista
es delgada (thin controller): valida permisos, delega la lógica de negocio
a `apps/orders/services.py` y formatea la respuesta.

Endpoints:
    - POST   /api/orders/checkout/                    → Carro → Orden PENDIENTE.
    - GET    /api/orders/my-orders/                   → Mis órdenes (cliente).
    - GET    /api/orders/                             → Todas las órdenes (admin).
    - GET    /api/orders/{order_number}/              → Detalle.
    - PATCH  /api/orders/{order_number}/status/       → Cambiar estado.

Reglas de permisos (RBAC):
    - Cliente:
        • Puede ver SUS propias órdenes (MyOrdersView).
        • Puede ver el detalle de SUS órdenes.
        • Puede pagar SUS órdenes (PENDIENTE → PAGADO).
        • NO puede cancelar ni entregar órdenes.
    - Admin:
        • Puede ver TODAS las órdenes.
        • Puede cambiar CUALQUIER orden a cualquier estado válido.
        • Puede cancelar órdenes pagadas (repone stock).

Transiciones de estado permitidas (validadas en `services.py`):
    PENDIENTE → PAGADO       (descuenta stock)
    PENDIENTE → CANCELADO    (no repone, nunca se descontó)
    PAGADO    → ENTREGADO    (estado final)
    PAGADO    → CANCELADO    (repone stock)
    ENTREGADO → (nada)       (estado final)
    CANCELADO → (nada)       (estado final)

Autor: José Fica
Sección: AP-N4-C2
Año: 2026
==============================================================================
"""

from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.permissions import IsAdminRole, IsOwnerOrAdmin
from .filters import OrderFilter
from .models import Order
from .serializers import (
    ChangeStatusSerializer,
    CheckoutResponseSerializer,
    OrderListSerializer,
    OrderSerializer,
)
from .services import change_order_status, checkout


# =============================================================================
# ENDPOINT: POST /api/orders/checkout/
# =============================================================================
# Convierte el carro activo del usuario en una Orden con estado PENDIENTE.
#
# Reglas de negocio aplicadas (ver `apps/orders/services.py::checkout`):
#     1. El carro NO puede estar vacío.
#     2. Se valida stock de cada producto con `select_for_update()`, pero
#        NO se descuenta (el descuento ocurre al pagar).
#     3. Se crea la Orden con el total calculado.
#     4. Se crean los OrderItem con SNAPSHOT de nombre, SKU y precio.
#     5. Se ELIMINA el carro (no se marca inactivo).
#
# Respuesta:
#     201 Created con la orden recién creada y todos sus ítems.
#     400 Bad Request si el carro está vacío o hay stock insuficiente.
# =============================================================================

@extend_schema(
    tags=['Órdenes'],
    summary='Realizar checkout del carro',
    description=(
        'Convierte el carro activo en una Orden en estado PENDIENTE. '
        'NO descuenta stock todavía; el descuento ocurre al pagar. '
        'El carro se elimina y se creará uno nuevo vacío en el próximo '
        'request a /api/cart/.'
    ),
    responses={
        201: CheckoutResponseSerializer,
        400: OpenApiResponse(description='Carro vacío o stock insuficiente.'),
    },
)
class CheckoutView(APIView):
    """
    Endpoint de checkout.

    Método: POST /api/orders/checkout/
    Permisos: IsAuthenticated (cualquier usuario logueado con carro).
    Body: (vacío).

    Delega toda la lógica a `checkout(user)` del servicio, que aplica
    la validación de stock y crea la orden de forma atómica.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Maneja el POST del checkout.

        Args:
            request: Objeto Request con el usuario autenticado.

        Returns:
            Response: 201 con {message, order} o 400 si hay error.
        """
        # --- Delegar a la lógica de negocio ---
        # checkout() valida stock, crea la orden, crea los OrderItem con
        # snapshot, y elimina el carro. Todo dentro de @transaction.atomic.
        order = checkout(request.user)

        # --- Retornar la orden creada ---
        return Response(
            {
                'message': 'Orden generada. Procede al pago.',
                'order': OrderSerializer(order).data,
            },
            status=status.HTTP_201_CREATED,
        )


# =============================================================================
# ENDPOINT: GET /api/orders/my-orders/
# =============================================================================
# Lista las órdenes del usuario autenticado (cliente o admin).
#
# El filtro `user=request.user` garantiza que un cliente NUNCA vea órdenes
# ajenas, incluso si intenta manipular la URL.
#
# Paginación: 10 órdenes por página (configurable con ?page_size=N).
# Filtros: ?status=PENDIENTE, ?ordering=-created_at.
# =============================================================================

@extend_schema(
    tags=['Órdenes'],
    summary='Listar mis órdenes',
    description='Retorna solo las órdenes del usuario autenticado, ordenadas por fecha descendente.',
    responses={200: OrderListSerializer(many=True)},
)
class MyOrdersView(generics.ListAPIView):
    """
    Endpoint para listar las órdenes propias.

    Método: GET /api/orders/my-orders/
    Permisos: IsAuthenticated.

    El queryset se filtra por `user=request.user`, así que solo devuelve
    las órdenes del usuario logueado.
    """

    serializer_class = OrderListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Retorna las órdenes del usuario autenticado, ordenadas por fecha.

        Returns:
            QuerySet: Órdenes del usuario, más recientes primero.
        """
        return Order.objects.filter(
            user=self.request.user
        ).order_by('-created_at')


# =============================================================================
# ENDPOINT: GET /api/orders/{order_number}/
# =============================================================================
# Retorna el detalle completo de una orden (con ítems anidados).
#
# Reglas de acceso:
#     - Cliente: solo puede ver SUS propias órdenes.
#     - Admin: puede ver cualquier orden (auditoría, soporte).
#
# Se usa `order_number` (UUID público) en lugar de la PK interna para
# evitar enumeración de órdenes por parte de atacantes.
#
# Nota: usa el permiso `IsOwnerOrAdmin`, que se evalúa a nivel de objeto
# (has_object_permission). Si el objeto no pertenece al usuario y el
# usuario no es admin → 403 Forbidden.
# =============================================================================

@extend_schema(
    tags=['Órdenes'],
    summary='Ver detalle de una orden',
    description='Un cliente solo puede ver sus órdenes; un admin puede ver cualquiera.',
    responses={200: OrderSerializer},
)
class OrderDetailView(generics.RetrieveAPIView):
    """
    Endpoint para ver el detalle de una orden.

    Método: GET /api/orders/{order_number}/
    Permisos: IsAuthenticated + IsOwnerOrAdmin.

    Se usa `lookup_field = 'order_number'` para buscar por UUID en lugar
    de la PK entera. Esto evita que un atacante enumere órdenes ajenas
    probando IDs secuenciales.
    """

    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    lookup_field = 'order_number'

    def get_queryset(self):
        """
        Filtra el queryset según el rol del usuario.

        - Admin: ve todas las órdenes.
        - Cliente: solo ve las suyas.

        Esta doble validación (queryset + IsOwnerOrAdmin) es defensa
        en profundidad: incluso si el permiso falla, el queryset ya
        limita lo que el usuario puede consultar.

        Returns:
            QuerySet: Órdenes visibles para el usuario.
        """
        user = self.request.user
        if getattr(user, 'role', None) == 'ADMIN':
            return Order.objects.all()
        return Order.objects.filter(user=user)


# =============================================================================
# ENDPOINT: PATCH /api/orders/{order_number}/status/
# =============================================================================
# Cambia el estado de una orden aplicando la máquina de estados.
#
# Reglas (validadas en dos capas):
#     1. Permisos a nivel de vista:
#        - Admin: cualquier transición válida.
#        - Cliente: solo PENDIENTE → PAGADO sobre SUS órdenes.
#     2. Transiciones válidas (validadas en `services.py::change_order_status`):
#        - PENDIENTE → PAGADO / CANCELADO
#        - PAGADO → ENTREGADO / CANCELADO
#        - ENTREGADO / CANCELADO: estados finales.
#
# Efectos colaterales (gestionados en el servicio):
#     - PENDIENTE → PAGADO: DESCUENTA stock de cada producto.
#     - PAGADO → CANCELADO: REPONE stock de cada producto.
#     - Otras transiciones: solo actualizan el estado y timestamps.
# =============================================================================

@extend_schema(
    tags=['Órdenes'],
    summary='Cambiar estado de una orden',
    description=(
        'Permite transicionar el estado de la orden. '
        'Reglas: '
        'PENDIENTE→PAGADO (descuenta stock), '
        'PENDIENTE→CANCELADO, '
        'PAGADO→ENTREGADO, '
        'PAGADO→CANCELADO (repone stock).'
    ),
    request=ChangeStatusSerializer,
    responses={
        200: OrderSerializer,
        400: OpenApiResponse(description='Transición inválida o stock insuficiente.'),
        403: OpenApiResponse(description='Sin permisos.'),
        404: OpenApiResponse(description='Orden no encontrada.'),
    },
)
class ChangeOrderStatusView(APIView):
    """
    Endpoint para cambiar el estado de una orden.

    Método: PATCH /api/orders/{order_number}/status/
    Permisos: IsAuthenticated + validación manual de rol y propiedad.
    Body: {status: 'PENDIENTE'|'PAGADO'|'ENTREGADO'|'CANCELADO'}.

    Flujo:
        1. Se obtiene la orden por su order_number (UUID).
        2. Se valida que el usuario sea el dueño o un admin.
        3. Se valida el nuevo estado con ChangeStatusSerializer.
        4. Si el usuario NO es admin, solo puede pagar (PENDIENTE → PAGADO).
        5. Se delega a `change_order_status()` que aplica la transición y
           sus efectos colaterales (descuento o reposición de stock).
    """

    permission_classes = [IsAuthenticated]

    def patch(self, request, order_number):
        """
        Maneja el PATCH para cambiar el estado.

        Args:
            request: Objeto Request con {status}.
            order_number: UUID de la orden a modificar.

        Returns:
            Response: 200 con {message, order} o error según el caso.

        Raises:
            PermissionDenied: Si el usuario no puede modificar esta orden
                              o no puede aplicar la transición solicitada.
        """
        # --- 1. Obtener la orden ---
        # Se prefetch de items para evitar N+1 en el serializer después.
        try:
            order = Order.objects.prefetch_related('items').get(
                order_number=order_number
            )
        except Order.DoesNotExist:
            return Response(
                {'detail': 'Orden no encontrada.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # --- 2. Validar permisos sobre la orden ---
        # Un usuario puede modificar la orden si es el dueño o es admin.
        is_admin = getattr(request.user, 'role', None) == 'ADMIN'
        is_owner = order.user_id == request.user.id

        if not (is_admin or is_owner):
            raise PermissionDenied('No tienes permiso sobre esta orden.')

        # --- 3. Validar el nuevo estado con el serializer ---
        serializer = ChangeStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data['status']

        # --- 4. Regla adicional para clientes ---
        # Un cliente solo puede pagar SU propia orden. No puede cancelar,
        # entregar ni revertir estados.
        if not is_admin:
            if new_status != Order.Status.PAGADO:
                raise PermissionDenied(
                    'Solo un Administrador puede cambiar la orden a este estado.'
                )

        # --- 5. Delegar la transición al servicio ---
        # change_order_status() valida la transición contra la máquina de
        # estados y aplica los efectos colaterales (stock).
        order = change_order_status(order, new_status)

        # --- 6. Retornar la orden actualizada ---
        return Response(
            {
                'message': f'Orden actualizada a {order.get_status_display()}.',
                'order': OrderSerializer(order).data,
            },
            status=status.HTTP_200_OK,
        )


# =============================================================================
# ENDPOINT: GET /api/orders/
# =============================================================================
# Lista TODAS las órdenes del sistema. Solo accesible para ADMIN.
#
# Se usa para el panel admin (auditoría, gestión de estados, soporte).
#
# Filtros disponibles (django-filter - OrderFilter):
#     - ?status=PENDIENTE|PAGADO|ENTREGADO|CANCELADO
#     - ?user=<id>
#     - ?username=<texto>
#     - ?total_min=<num> & ?total_max=<num>
#     - ?created_after=YYYY-MM-DD & ?created_before=YYYY-MM-DD
#     - ?paid_after=YYYY-MM-DD & ?paid_before=YYYY-MM-DD
#     - ?search=<order_number|username|email>
#     - ?ordering=created_at|total|status
# =============================================================================

@extend_schema(
    tags=['Órdenes'],
    summary='Listar todas las órdenes (solo Admin)',
    description=(
        'Retorna todas las órdenes del sistema con filtros por estado, '
        'usuario, rango de fechas y rango de total. Solo Admin.'
    ),
    responses={200: OrderListSerializer(many=True)},
)
class AllOrdersView(generics.ListAPIView):
    """
    Endpoint para listar todas las órdenes (vista de admin).

    Método: GET /api/orders/
    Permisos: IsAuthenticated + IsAdminRole.

    Características:
        - Optimización: select_related('user') para evitar N+1.
        - Filtros avanzados con OrderFilter (status, fechas, total, etc.).
        - Búsqueda por texto en order_number, username y email.
        - Ordenamiento configurable.

    Se usa para el panel de administración del frontend.
    """

    serializer_class = OrderListSerializer
    permission_classes = [IsAuthenticated, IsAdminRole]

    # --- Optimización: traer el user en la misma query ---
    queryset = Order.objects.select_related('user').order_by('-created_at')

    # --- Filtros, búsqueda y ordenamiento ---
    filterset_class = OrderFilter
    search_fields = ['order_number', 'user__username', 'user__email']
    ordering_fields = ['created_at', 'total', 'status']
    ordering = ['-created_at']