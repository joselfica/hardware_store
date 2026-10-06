"""
==============================================================================
VISTAS DE AUTENTICACIÓN Y GESTIÓN DE USUARIOS
==============================================================================
Implementa los endpoints REST de autenticación JWT y la gestión de usuarios
por parte de administradores.

Endpoints de autenticación:
    - POST /api/auth/register/         → Registro de nuevo cliente.
    - POST /api/auth/login/            → Login JWT (access + refresh + user).
    - POST /api/auth/refresh/          → Refrescar token access (en urls.py).
    - POST /api/auth/logout/           → Invalidar refresh (blacklist).
    - GET  /api/auth/me/               → Perfil del usuario autenticado.
    - POST /api/auth/change-password/  → Cambio de contraseña.

Endpoints de gestión (solo Admin):
    - GET/POST/PUT/PATCH/DELETE /api/users/  → CRUD completo de usuarios.

Notas de seguridad:
    - El registro público fuerza role=CLIENTE (anti-escalada de privilegios).
    - El login inyecta claims personalizados (role, email, full_name) al JWT.
    - El logout blacklistea el refresh para invalidar la sesión.
    - El ViewSet de usuarios aplica soft delete si el usuario tiene órdenes.

Autor: José Fica
Sección: AP-N4-C2
Año: 2026
==============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================

from django.contrib.auth import get_user_model
from django.db.models import ProtectedError
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse
from rest_framework import generics, permissions, status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .permissions import IsAdminRole, IsAuthenticatedAndActive
from .serializers import (
    ChangePasswordSerializer,
    CustomTokenObtainPairSerializer,
    UpdateProfileSerializer,
    RegisterSerializer,
    UserAdminSerializer,
    UserSerializer,
)

User = get_user_model()


# =============================================================================
# ENDPOINT: POST /api/auth/register/
# =============================================================================
# Registro público de nuevos usuarios.
#
# Reglas de seguridad:
#     - El rol se fuerza a CLIENTE en el serializer. Un atacante NO puede
#       auto-promoverse a ADMIN enviando `role: "ADMIN"` en el payload.
#     - Se valida email y username únicos (case-insensitive).
#     - Se aplican los validadores de contraseña de Django.
#
# Respuesta:
#     201 Created con {user, access, refresh, message}.
#     El registro autentica automáticamente al usuario (devuelve tokens).
# =============================================================================

@extend_schema(
    tags=['Autenticación'],
    summary='Registrar un nuevo cliente',
    description=(
        'Crea un usuario con rol CLIENTE y retorna los tokens JWT junto con '
        'los datos del usuario. El rol NO puede ser forzado desde el cliente.'
    ),
    request=RegisterSerializer,
    responses={
        201: OpenApiResponse(description='Usuario registrado exitosamente.'),
        400: OpenApiResponse(description='Datos inválidos.'),
    },
)
class RegisterView(generics.CreateAPIView):
    """
    Endpoint de registro público.

    Crea un nuevo usuario con rol CLIENTE y retorna tokens JWT para
    autenticarlo automáticamente. El rol NO puede forzarse desde el cliente:
    el serializer lo asigna siempre como CLIENTE.

    Método: POST /api/auth/register/
    Permisos: AllowAny (público).
    Body: {username, email, first_name, last_name, rut?, phone?, password, password_confirm}.
    """

    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        """
        Sobrescribe create() para retornar también los tokens JWT.

        Mejora la UX porque el usuario queda autenticado inmediatamente
        tras registrarse, sin necesidad de hacer un segundo request a login.

        Args:
            request: Objeto Request con los datos del formulario.

        Returns:
            Response: 201 con {user, access, refresh, message}.
        """
        # --- 1. Validar y crear el usuario ---
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # --- 2. Generar tokens con claims personalizados ---
        # CustomTokenObtainPairSerializer.get_token() inyecta el rol y
        # otros datos del usuario en el payload del JWT.
        refresh = CustomTokenObtainPairSerializer.get_token(user)

        # --- 3. Retornar tokens + datos del usuario ---
        return Response(
            {
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'message': 'Usuario registrado exitosamente.',
            },
            status=status.HTTP_201_CREATED,
        )


# =============================================================================
# ENDPOINT: POST /api/auth/login/
# =============================================================================
# Login JWT con claims personalizados.
#
# Se extiende TokenObtainPairView para usar CustomTokenObtainPairSerializer,
# que inyecta claims adicionales (role, email, full_name) en el payload del
# token y retorna los datos del usuario en la respuesta.
# =============================================================================

class LoginView(TokenObtainPairView):
    """
    Endpoint de login JWT.

    Retorna:
        - access: token de corta duración (60 min por defecto).
        - refresh: token de larga duración (7 días por defecto).
        - user: datos del usuario autenticado.

    Los tokens incluyen el claim 'role' que se usa para RBAC en el frontend
    y en los permisos DRF.

    Método: POST /api/auth/login/
    Permisos: AllowAny (público).
    Body: {username, password}.
    """

    serializer_class = CustomTokenObtainPairSerializer


# =============================================================================
# ENDPOINT: POST /api/auth/logout/
# =============================================================================
# Logout con blacklist del refresh token.
#
# Agrega el refresh a la lista negra de SimpleJWT. Después de esto, el
# refresh NO puede usarse para obtener nuevos access tokens, incluso si
# alguien lo hubiera robado.
# =============================================================================

@extend_schema(
    tags=['Autenticación'],
    summary='Cerrar sesión (logout)',
    description=(
        'Invalida el token refresh agregándolo a la blacklist. '
        'Después de esto, el refresh no puede usarse para obtener nuevos access.'
    ),
    request={'application/json': {'type': 'object', 'properties': {
        'refresh': {'type': 'string', 'description': 'Token refresh a invalidar.'}
    }}},
    responses={
        205: OpenApiResponse(description='Logout exitoso.'),
        400: OpenApiResponse(description='Token inválido o ya expirado.'),
    },
)
class LogoutView(APIView):
    """
    Endpoint de logout.

    Requiere autenticación con un access válido para evitar que terceros
    invaliden tokens ajenos.

    Método: POST /api/auth/logout/
    Permisos: IsAuthenticated.
    Body: {refresh}.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """
        Agrega el refresh token a la blacklist.

        Args:
            request: Objeto Request con {refresh}.

        Returns:
            Response: 205 si se invalidó, 400 si el token es inválido.
        """
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response(
                    {'detail': 'Se requiere el token refresh.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(
                {'message': 'Sesión cerrada exitosamente.'},
                status=status.HTTP_205_RESET_CONTENT,
            )
        except TokenError as e:
            return Response(
                {'detail': f'Token inválido o expirado: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST,
            )


# =============================================================================
# ENDPOINT: GET /api/auth/me/
# =============================================================================
# Retorna los datos del usuario autenticado.
#
# Útil para que el frontend valide la sesión al recargar la página y
# cargue el perfil del usuario sin depender del payload del token.
# =============================================================================

@extend_schema(
    tags=['Autenticación'],
    summary='Obtener perfil del usuario autenticado',
    responses={200: UserSerializer},
)
class MeView(generics.RetrieveUpdateAPIView):
    """
    Endpoint para ver y actualizar el perfil del usuario autenticado.

    Métodos:
        - GET   /api/auth/me/  → Obtener el perfil actual.
        - PATCH /api/auth/me/  → Actualizar datos personales (parcial).
        - PUT   /api/auth/me/  → Actualizar datos personales (completo).

    Permisos: IsAuthenticatedAndActive.

    Reglas:
        - El usuario NO puede cambiar su username (ligado al historial).
        - El usuario NO puede cambiar su role (anti-escalada).
        - El email y RUT deben ser únicos.
    """

    permission_classes = [IsAuthenticatedAndActive]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        """Usa el serializer específico para actualización."""
        if self.request.method in ('PUT', 'PATCH'):
            return UpdateProfileSerializer
        return UserSerializer


# =============================================================================
# ENDPOINT: POST /api/auth/change-password/
# =============================================================================
# Permite al usuario autenticado cambiar su contraseña.
#
# Valida:
#     - La contraseña actual es correcta.
#     - La nueva contraseña cumple con los validadores de Django.
#     - Las dos nuevas contraseñas coinciden.
# =============================================================================

@extend_schema(
    tags=['Autenticación'],
    summary='Cambiar contraseña',
    request=ChangePasswordSerializer,
    responses={
        200: OpenApiResponse(description='Contraseña actualizada.'),
        400: OpenApiResponse(description='Contraseña actual incorrecta o inválida.'),
    },
)
class ChangePasswordView(generics.UpdateAPIView):
    """
    Endpoint para cambiar la contraseña del usuario autenticado.

    Método: POST /api/auth/change-password/
    Permisos: IsAuthenticated.
    Body: {old_password, new_password, new_password_confirm}.
    """

    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Retorna el usuario autenticado."""
        return self.request.user

    def update(self, request, *args, **kwargs):
        """
        Procesa el cambio de contraseña.

        Args:
            request: Objeto Request con las contraseñas.

        Returns:
            Response: 200 si se actualizó correctamente.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {'message': 'Contraseña actualizada correctamente.'},
            status=status.HTTP_200_OK,
        )


# =============================================================================
# VIEWSET: GESTIÓN DE USUARIOS (solo Admin)
# =============================================================================
# CRUD completo de usuarios accesible solo para administradores.
#
# Reglas de negocio:
#     1. Solo ADMIN puede listar, crear, editar o eliminar usuarios.
#     2. No se puede eliminar a sí mismo.
#     3. No se puede eliminar al último admin activo.
#     4. Si un usuario tiene órdenes asociadas (Order.user PROTECT),
#        se aplica SOFT DELETE en vez de eliminación física.
# =============================================================================

@extend_schema_view(
    list=extend_schema(
        tags=['Admin - Usuarios'],
        summary='Listar usuarios (solo Admin)',
        description='Retorna la lista paginada de usuarios con filtros por rol y estado.',
    ),
    create=extend_schema(
        tags=['Admin - Usuarios'],
        summary='Crear usuario (solo Admin)',
        description='Permite crear usuarios con cualquier rol (CLIENTE o ADMIN).',
    ),
    retrieve=extend_schema(
        tags=['Admin - Usuarios'],
        summary='Detalle de usuario',
    ),
    update=extend_schema(
        tags=['Admin - Usuarios'],
        summary='Actualizar usuario',
    ),
    partial_update=extend_schema(
        tags=['Admin - Usuarios'],
        summary='Actualizar parcialmente usuario',
    ),
    destroy=extend_schema(
        tags=['Admin - Usuarios'],
        summary='Eliminar usuario',
        description='Aplica soft delete si el usuario tiene órdenes asociadas.',
    ),
)
class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet de gestión de usuarios (exclusivo para ADMIN).

    Filtros disponibles:
        - ?role=ADMIN|CLIENTE
        - ?is_active=true|false
        - ?is_staff=true|false
        - ?search=<username|email|first_name|last_name|rut>
        - ?ordering=username|email|date_joined|last_login

    Reglas de eliminación (ver destroy()):
        - No puede eliminarse a sí mismo.
        - No puede eliminar al último admin activo.
        - Soft delete si el usuario tiene órdenes asociadas.
    """

    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserAdminSerializer
    permission_classes = [IsAdminRole]

    # --- Filtros, búsqueda y ordenamiento ---
    filterset_fields = ['role', 'is_active', 'is_staff']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'rut']
    ordering_fields = ['username', 'email', 'date_joined', 'last_login']
    ordering = ['-date_joined']

    def destroy(self, request, *args, **kwargs):
        """
        Elimina un usuario con validaciones de negocio y soft delete.

        Reglas:
            1. No se puede eliminar a sí mismo (403).
            2. No se puede eliminar al último admin activo (403).
            3. Si el usuario tiene órdenes asociadas → SOFT DELETE (200).
               - Se marca is_active=False.
               - Se renombra username y email con prefijo `deleted_<id>_`
                 para liberar los valores originales.
               - Las órdenes quedan intactas (integridad histórica).
            4. Si no tiene órdenes → eliminación física (204).

        Args:
            request: Objeto Request con el usuario autenticado.
            pk: ID del usuario a eliminar.

        Returns:
            Response:
                204 No Content si se eliminó físicamente.
                200 OK si se aplicó soft delete.
                403 Forbidden si viola reglas de negocio.
                409 Conflict si hay otros registros protegidos.
        """
        instance = self.get_object()

        # --- Validación 1: no puede eliminarse a sí mismo ---
        if instance.pk == request.user.pk:
            return Response(
                {'detail': 'No puedes eliminar tu propia cuenta.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        # --- Validación 2: no puede eliminar al último admin activo ---
        if instance.role == User.Role.ADMIN and instance.is_active:
            admins_activos = User.objects.filter(
                role=User.Role.ADMIN,
                is_active=True,
            ).exclude(pk=instance.pk).count()

            if admins_activos == 0:
                return Response(
                    {'detail': (
                        'No puedes eliminar al último administrador activo. '
                        'Debe existir al menos un admin para gestionar el sistema.'
                    )},
                    status=status.HTTP_403_FORBIDDEN,
                )

        # --- Validación 3: soft delete si tiene órdenes ---
        tiene_ordenes = instance.orders.exists()

        if tiene_ordenes:
            username_original = instance.username

            # Evitar renombrar dos veces si ya fue desactivado antes
            if not instance.username.startswith('deleted_'):
                instance.username = f'deleted_{instance.pk}_{instance.username}'
                instance.email = f'deleted_{instance.pk}_{instance.email or "user"}'

            instance.is_active = False
            instance.save()

            return Response(
                {
                    'detail': (
                        f'El usuario "{username_original}" tiene órdenes asociadas. '
                        'Se ha desactivado en lugar de eliminarse para preservar '
                        'el histórico de compras.'
                    ),
                    'soft_deleted': True,
                },
                status=status.HTTP_200_OK,
            )

        # --- Eliminación física: sin órdenes, sin problema ---
        try:
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProtectedError:
            return Response(
                {'detail': (
                    'No se puede eliminar este usuario porque tiene '
                    'registros asociados que dependen de él.'
                )},
                status=status.HTTP_409_CONFLICT,
            )