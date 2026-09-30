"""
==============================================================================
URLS DE LA APP USERS
==============================================================================
Define las rutas de autenticación y gestión de usuarios. Se usa el prefijo
`/api/` (definido en config/urls.py) más las rutas específicas de esta app.

Estructura:
    ┌──────────────────────────────────────────────────────────────────┐
    │ AUTENTICACIÓN                                                    │
    │ POST   /api/auth/register/         → Registro de cliente         │
    │ POST   /api/auth/login/            → Login JWT                   │
    │ POST   /api/auth/refresh/          → Refrescar access            │
    │ POST   /api/auth/logout/           → Logout con blacklist        │
    │ GET    /api/auth/me/               → Perfil del usuario          │
    │ POST   /api/auth/change-password/  → Cambiar contraseña          │
    ├──────────────────────────────────────────────────────────────────┤
    │ GESTIÓN DE USUARIOS (solo Admin)                                 │
    │ GET    /api/users/                 → Listar usuarios             │
    │ POST   /api/users/                 → Crear usuario               │
    │ GET    /api/users/{id}/            → Detalle                     │
    │ PUT    /api/users/{id}/            → Actualizar completo         │
    │ PATCH  /api/users/{id}/            → Actualizar parcial          │
    │ DELETE /api/users/{id}/            → Eliminar (con soft delete)  │
    └──────────────────────────────────────────────────────────────────┘

Nota de diseño:
    El ViewSet de usuarios se registra con DefaultRouter, que genera
    automáticamente las rutas CRUD. Las rutas de autenticación se declaran
    explícitamente porque no siguen el patrón REST estándar.

Autor: José Fica
Sección: AP-N4-C2
Año: 2026
==============================================================================
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    ChangePasswordView,
    LoginView,
    LogoutView,
    MeView,
    RegisterView,
    UserViewSet,
)

app_name = 'users'

# =============================================================================
# ROUTER: VIEWSET DE USUARIOS
# =============================================================================
# Registra el ViewSet de usuarios en /api/users/. El router genera
# automáticamente las rutas list, create, retrieve, update, partial_update
# y destroy.
# =============================================================================

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    # =========================================================================
    # REGISTRO Y LOGIN
    # =========================================================================
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),

    # =========================================================================
    # CICLO DE VIDA DEL TOKEN JWT
    # =========================================================================
    # - /refresh/ → obtiene un nuevo access usando el refresh.
    # - /logout/  → agrega el refresh a la blacklist (invalidación).
    # =========================================================================
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),

    # =========================================================================
    # PERFIL Y SEGURIDAD DEL USUARIO
    # =========================================================================
    # - /me/              → datos del usuario autenticado.
    # - /change-password/ → cambio de contraseña autenticado.
    # =========================================================================
    path('auth/me/', MeView.as_view(), name='me'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='change_password'),

    # =========================================================================
    # GESTIÓN DE USUARIOS (solo Admin)
    # =========================================================================
    # Se monta el router al final para evitar colisiones con las rutas
    # explícitas de autenticación (/api/auth/* no choca con /api/users/*).
    # =========================================================================
    path('', include(router.urls)),
]