"""
==============================================================================
VIEWSETS DEL CATÁLOGO DE PRODUCTOS
==============================================================================
Este módulo implementa los ViewSets de DRF para las entidades del catálogo:
Categorías, Marcas y Productos.

Diseño:
    - Se utiliza ModelViewSet para exponer el CRUD completo (list, create,
      retrieve, update, partial_update, destroy) con rutas generadas por
      el DefaultRouter.
    - Los permisos se delegan a IsAdminOrReadOnly: lectura pública (GET),
      escritura restringida a usuarios con rol ADMIN.
    - Los filtros se delegan a clases FilterSet (django-filter) definidas
      en apps/catalog/filters.py.
    - La búsqueda por texto (?search=) y el ordenamiento (?ordering=) se
      gestionan mediante SearchFilter y OrderingFilter de DRF.
    - La documentación OpenAPI se enriquece con @extend_schema_view y
      @extend_schema para que Swagger muestre descripciones y parámetros.

Optimizaciones aplicadas:
    - select_related('brand', 'category') evita N+1 en consultas de productos.
    - annotate(products_count=Count(...)) agrega el conteo de productos
      activos por categoría/marca en una sola query.
    - LargePagination permite al frontend solicitar ?page_size=N para
      poblar selects del panel admin sin hacer múltiples requests.

Autor: José Fica
Sección: AP-N4-C2
Año: 2026
==============================================================================
"""

from django.db.models import Count, Q
from drf_spectacular.utils import (
    OpenApiParameter,
    extend_schema,
    extend_schema_view,
)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser   # ← NUEVO
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.users.permissions import IsAdminOrReadOnly
from .filters import BrandFilter, CategoryFilter, ProductFilter
from .models import Brand, Category, Product
from .serializers import (
    BrandSerializer,
    CategorySerializer,
    ProductDetailSerializer,
    ProductListSerializer,
)


# =============================================================================
# PAGINACIÓN PERSONALIZADA
# =============================================================================
# IMPORTANTE: Debe definirse ANTES de los ViewSets que la usan.
# Python evalúa el archivo de arriba hacia abajo y necesita el nombre
# resuelto en el momento de la definición de cada ViewSet.
#
# Uso desde el frontend:
#     /api/products/                 → 10 items (default)
#     /api/products/?page_size=50    → 50 items
#     /api/products/?page_size=200   → 200 items (máximo permitido)
#     /api/products/?page_size=1000  → 200 items (limitado al máximo)
# =============================================================================

class LargePagination(PageNumberPagination):
    """
    Paginación configurable por query param.

    Permite al frontend solicitar más items por página para:
        - Poblar selects de marcas/categorías en modales de edición.
        - Traer todos los productos al admin cuando sea necesario.
        - Evitar múltiples requests para paginación manual.

    Límites:
        - page_size = 10 (por defecto, si no se especifica)
        - max_page_size = 200 (tope de seguridad)
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 200


# =============================================================================
# VIEWSET DE CATEGORÍA
# =============================================================================

@extend_schema_view(
    list=extend_schema(
        tags=['Catálogo - Categorías'],
        summary='Listar categorías',
        description=(
            'Endpoint público. Retorna categorías paginadas con la cantidad '
            'de productos activos en cada una.'
        ),
        parameters=[
            OpenApiParameter(name='is_active', description='Filtrar por estado activo', type=bool),
            OpenApiParameter(name='name_contains', description='Nombre contiene (icontains)', type=str),
            OpenApiParameter(name='created_after', description='Creadas después de (YYYY-MM-DD)', type=str),
            OpenApiParameter(name='created_before', description='Creadas antes de (YYYY-MM-DD)', type=str),
            OpenApiParameter(name='search', description='Búsqueda en nombre y descripción', type=str),
            OpenApiParameter(name='ordering', description='Orden: name, created_at, -updated_at', type=str),
            OpenApiParameter(name='page_size', description='Items por página (máx 200)', type=int),
        ],
    ),
    create=extend_schema(
        tags=['Catálogo - Categorías'],
        summary='Crear categoría (solo Admin)',
        description='Requiere token JWT con rol ADMIN.',
    ),
    retrieve=extend_schema(
        tags=['Catálogo - Categorías'],
        summary='Detalle de categoría',
    ),
    update=extend_schema(
        tags=['Catálogo - Categorías'],
        summary='Actualizar categoría (solo Admin)',
    ),
    partial_update=extend_schema(
        tags=['Catálogo - Categorías'],
        summary='Actualizar parcialmente categoría (solo Admin)',
    ),
    destroy=extend_schema(
        tags=['Catálogo - Categorías'],
        summary='Eliminar categoría (solo Admin)',
    ),
)
class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar Categorías del catálogo.

    Permisos:
        - Lectura (GET/HEAD/OPTIONS): pública.
        - Escritura (POST/PUT/PATCH/DELETE): solo usuarios con rol ADMIN.

    Filtros disponibles:
        - ?is_active=true|false
        - ?name_contains=<texto>
        - ?created_after=YYYY-MM-DD & ?created_before=YYYY-MM-DD
        - ?search=<texto>            (búsqueda en name y description)
        - ?ordering=name|-created_at
        - ?page_size=N               (máx 200)
    """

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_class = CategoryFilter
    pagination_class = LargePagination

    # --- Backends de búsqueda y ordenamiento ---
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['name']

    def get_queryset(self):
        """
        Optimiza la consulta agregando el conteo de productos activos
        por categoría. Evita N+1 queries al exponer 'products_count'.
        """
        return Category.objects.annotate(
            products_count=Count(
                'products',
                filter=Q(products__is_active=True),
            )
        )


# =============================================================================
# VIEWSET DE MARCA
# =============================================================================

@extend_schema_view(
    list=extend_schema(
        tags=['Catálogo - Marcas'],
        summary='Listar marcas',
        description=(
            'Endpoint público. Retorna marcas paginadas con la cantidad '
            'de productos activos en cada una.'
        ),
        parameters=[
            OpenApiParameter(name='is_active', description='Filtrar por estado activo', type=bool),
            OpenApiParameter(name='name_contains', description='Nombre contiene (icontains)', type=str),
            OpenApiParameter(name='created_after', description='Creadas después de (YYYY-MM-DD)', type=str),
            OpenApiParameter(name='created_before', description='Creadas antes de (YYYY-MM-DD)', type=str),
            OpenApiParameter(name='search', description='Búsqueda en nombre y descripción', type=str),
            OpenApiParameter(name='ordering', description='Orden: name, created_at, -updated_at', type=str),
            OpenApiParameter(name='page_size', description='Items por página (máx 200)', type=int),
        ],
    ),
    create=extend_schema(
        tags=['Catálogo - Marcas'],
        summary='Crear marca (solo Admin)',
    ),
    retrieve=extend_schema(
        tags=['Catálogo - Marcas'],
        summary='Detalle de marca',
    ),
    update=extend_schema(
        tags=['Catálogo - Marcas'],
        summary='Actualizar marca (solo Admin)',
    ),
    partial_update=extend_schema(
        tags=['Catálogo - Marcas'],
        summary='Actualizar parcialmente marca (solo Admin)',
    ),
    destroy=extend_schema(
        tags=['Catálogo - Marcas'],
        summary='Eliminar marca (solo Admin)',
    ),
)
class BrandViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar Marcas del catálogo.

    Permisos y filtros: idénticos a CategoryViewSet.
    """

    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_class = BrandFilter
    pagination_class = LargePagination

    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['name']

    def get_queryset(self):
        """Anota la cantidad de productos activos por marca."""
        return Brand.objects.annotate(
            products_count=Count(
                'products',
                filter=Q(products__is_active=True),
            )
        )


# =============================================================================
# VIEWSET DE PRODUCTO (el más importante del catálogo)
# =============================================================================

@extend_schema_view(
    list=extend_schema(
        tags=['Catálogo - Productos'],
        summary='Listar productos',
        description=(
            'Endpoint público. Retorna productos paginados con múltiples '
            'filtros: categoría, marca, rango de precios, rango de stock, '
            'búsqueda por texto y ordenamiento.'
        ),
        parameters=[
            OpenApiParameter(name='category', description='ID de categoría', type=int),
            OpenApiParameter(name='category_slug', description='Slug de categoría', type=str),
            OpenApiParameter(name='category_name', description='Nombre de categoría (icontains)', type=str),
            OpenApiParameter(name='brand', description='ID de marca', type=int),
            OpenApiParameter(name='brand_slug', description='Slug de marca', type=str),
            OpenApiParameter(name='brand_name', description='Nombre de marca (icontains)', type=str),
            OpenApiParameter(name='price_min', description='Precio mínimo (CLP)', type=float),
            OpenApiParameter(name='price_max', description='Precio máximo (CLP)', type=float),
            OpenApiParameter(name='stock_min', description='Stock mínimo', type=int),
            OpenApiParameter(name='stock_max', description='Stock máximo', type=int),
            OpenApiParameter(name='in_stock', description='Solo productos con stock > 0', type=bool),
            OpenApiParameter(name='is_active', description='Solo productos activos', type=bool),
            OpenApiParameter(name='created_after', description='Creados después de (YYYY-MM-DD)', type=str),
            OpenApiParameter(name='created_before', description='Creados antes de (YYYY-MM-DD)', type=str),
            OpenApiParameter(name='search', description='Búsqueda en nombre, SKU, descripción, marca y categoría', type=str),
            OpenApiParameter(name='ordering', description='Orden: price, name, stock, -created_at', type=str),
            OpenApiParameter(name='page_size', description='Items por página (máx 200)', type=int),
        ],
    ),
    create=extend_schema(
        tags=['Catálogo - Productos'],
        summary='Crear producto (solo Admin)',
        description='Requiere token JWT con rol ADMIN.',
    ),
    retrieve=extend_schema(
        tags=['Catálogo - Productos'],
        summary='Detalle de producto',
        description='Retorna el producto con marca y categoría anidadas.',
    ),
    update=extend_schema(
        tags=['Catálogo - Productos'],
        summary='Actualizar producto (solo Admin)',
    ),
    partial_update=extend_schema(
        tags=['Catálogo - Productos'],
        summary='Actualizar parcialmente producto (solo Admin)',
    ),
    destroy=extend_schema(
        tags=['Catálogo - Productos'],
        summary='Eliminar producto (solo Admin)',
    ),
)
class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar Productos del catálogo.

    Permisos:
        - Lectura: pública.
        - Escritura: solo ADMIN.

    Serializers:
        - action='list'           → ProductListSerializer (ligero).
        - otras acciones          → ProductDetailSerializer (completo).

    Filtros disponibles (django-filter):
        - ?category=<id> & ?category_slug=<slug> & ?category_name=<texto>
        - ?brand=<id>    & ?brand_slug=<slug>    & ?brand_name=<texto>
        - ?price_min=<num> & ?price_max=<num>
        - ?stock_min=<num> & ?stock_max=<num>
        - ?in_stock=true
        - ?is_active=true|false
        - ?created_after=YYYY-MM-DD & ?created_before=YYYY-MM-DD
        - ?search=<texto>
        - ?ordering=price|name|stock|-created_at
        - ?page_size=N               (máx 200)
    """

    queryset = Product.objects.select_related('brand', 'category').all()
    permission_classes = [IsAdminOrReadOnly]
    filterset_class = ProductFilter
    pagination_class = LargePagination

    # --- NUEVO: parsers para aceptar archivos en POST/PATCH ---
    # JSONParser:      peticiones JSON normales (application/json).
    # MultiPartParser: peticiones con archivos (multipart/form-data).
    # FormParser:      formularios HTML tradicionales.
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    # --- Backends de búsqueda y ordenamiento ---
    search_fields = ['name', 'sku', 'description', 'brand__name', 'category__name']
    ordering_fields = ['name', 'price', 'stock', 'created_at', 'updated_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """
        Retorna un serializer ligero para 'list' y el completo para el resto.
        Optimiza el payload en listados grandes.
        """
        if self.action == 'list':
            return ProductListSerializer
        return ProductDetailSerializer

    def get_queryset(self):
        """
        Optimiza con select_related y aplica visibilidad según el usuario.

        Reglas de visibilidad:
            - Usuario anónimo o cliente: solo ve productos ACTIVOS y CON STOCK.
            - Admin: ve todos los productos (incluidos sin stock) para poder
              gestionar el inventario.

        Para forzar que un admin vea solo los que tienen stock, puede usar
        ?in_stock=true. Para que un admin vea todos, ?include_out_of_stock=true.
        """
        qs = Product.objects.select_related('brand', 'category')

        # Admins pueden ver todo si lo piden explícitamente
        include_oos = self.request.query_params.get('include_out_of_stock', 'false').lower() == 'true'
        is_admin = (
            self.request.user.is_authenticated
            and getattr(self.request.user, 'role', None) == 'ADMIN'
        )

        if not (is_admin and include_oos):
            # Público y clientes: solo productos activos
            qs = qs.filter(is_active=True)

            # Y solo con stock > 0 (a menos que el filtro in_stock esté en false)
            in_stock_param = self.request.query_params.get('in_stock', None)
            if in_stock_param is None or in_stock_param.lower() == 'true':
                qs = qs.filter(stock__gt=0)

        return qs

    # ---------------------------------------------------------------------
    # ACCIÓN PERSONALIZADA: consultar stock
    # ---------------------------------------------------------------------
    @extend_schema(
        tags=['Catálogo - Productos'],
        summary='Consultar stock de un producto',
        description=(
            'Endpoint público. Retorna solo el stock y su estado textual. '
            'Útil para validar disponibilidad sin traer todo el objeto.'
        ),
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer'},
                    'sku': {'type': 'string'},
                    'stock': {'type': 'integer'},
                    'stock_status': {'type': 'string'},
                    'is_available': {'type': 'boolean'},
                },
            }
        },
    )
    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def stock(self, request, pk=None):
        """
        GET /api/products/{id}/stock/

        Retorna un resumen del stock del producto:
            - stock: unidades disponibles.
            - stock_status: etiqueta legible ('Sin stock', 'Últimas unidades', etc.).
            - is_available: booleano (activo + stock > 0).
        """
        product = self.get_object()
        return Response(
            {
                'id': product.id,
                'sku': product.sku,
                'stock': product.stock,
                'stock_status': product.stock_status,
                'is_available': product.is_available,
            },
            status=status.HTTP_200_OK,
        )